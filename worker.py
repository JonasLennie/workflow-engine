import json
import time
import logging
from db import get_connection, put_connection
from task_handlers import HANDLERS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [worker] %(message)s")
log = logging.getLogger(__name__)


class RetryableError(Exception):
    pass


def try_acquire_task(cur):
    cur.execute("""
        SELECT t.id, t.task_type, t.workflow_id, t.input_data, t.depends_on, t.attempts, t.max_attempts
        FROM tasks t
        WHERE t.task_status = 'pending'
          AND (t.lease_expires_at IS NULL OR t.lease_expires_at < NOW())
          AND NOT EXISTS (
              SELECT 1 FROM tasks dep
              WHERE dep.workflow_id = t.workflow_id
                AND dep.task_type = ANY(t.depends_on)
                AND dep.task_status != 'completed'
          )
        ORDER BY t.created_at
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    """)
    row = cur.fetchone()
    if not row:
        return None

    task_id = row[0]
    cur.execute(
        "UPDATE tasks SET task_status = 'running', "
        "lease_expires_at = NOW() + INTERVAL '5 minutes', "
        "attempts = attempts + 1, updated_at = NOW() "
        "WHERE id = %s",
        (task_id,),
    )
    return row


def gather_inputs(cur, workflow_id, depends_on, base_input):
    if not depends_on:
        return base_input
    cur.execute(
        "SELECT task_type, output_data FROM tasks "
        "WHERE workflow_id = %s AND task_type = ANY(%s) AND task_status = 'completed'",
        (workflow_id, list(depends_on)),
    )
    upstream = {r[0]: r[1] for r in cur.fetchall()}
    return {**base_input, "upstream": upstream}


def execute_task(conn, task_row):
    task_id, task_type, workflow_id, input_data, depends_on, attempts, max_attempts = task_row

    try:
        with conn.cursor() as cur:
            full_input = gather_inputs(cur, workflow_id, depends_on, input_data)
        conn.commit()

        handler = HANDLERS.get(task_type)
        if not handler:
            raise ValueError(f"Unknown task type: {task_type}")

        result = handler(full_input)

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET task_status = 'completed', output_data = %s, "
                "updated_at = NOW(), lease_expires_at = NULL WHERE id = %s",
                (json.dumps(result), task_id),
            )
        conn.commit()
        log.info("Task %d (%s) completed", task_id, task_type)

    except RetryableError as e:
        backoff = min(2 ** attempts, 60)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET task_status = 'pending', error = %s, "
                "lease_expires_at = NOW() + make_interval(secs => %s), updated_at = NOW() "
                "WHERE id = %s",
                (str(e), backoff, task_id),
            )
        conn.commit()
        log.warning("Task %d (%s) retryable error, backoff %ds: %s", task_id, task_type, backoff, e)

    except Exception as e:
        status = "failed" if attempts >= max_attempts else "pending"
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET task_status = %s, error = %s, "
                "updated_at = NOW(), lease_expires_at = NULL WHERE id = %s",
                (status, str(e), task_id),
            )
        conn.commit()
        log.error("Task %d (%s) error (attempt %d/%d): %s", task_id, task_type, attempts, max_attempts, e)


if __name__ == "__main__":
    log.info("Worker started")
    while True:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                task = try_acquire_task(cur)
            conn.commit()

            if task:
                execute_task(conn, task)
            else:
                time.sleep(1)
        except Exception:
            conn.rollback()
            log.exception("Worker loop error")
            time.sleep(1)
        finally:
            put_connection(conn)
