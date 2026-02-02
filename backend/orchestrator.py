import json
import time
import logging
from db import get_connection, put_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [orchestrator] %(message)s")
log = logging.getLogger(__name__)

SPEC_PATH = "workflows/manufacturing_analysis.json"

with open(SPEC_PATH) as f:
    SPEC = json.load(f)


def poll():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, input_data FROM workflows "
                "WHERE workflow_status = 'pending' "
                "FOR UPDATE SKIP LOCKED"
            )
            pending = cur.fetchall()

            for wf_id, input_data in pending:
                for task_def in SPEC["tasks"]:
                    cur.execute(
                        "INSERT INTO tasks (workflow_id, task_type, depends_on, input_data) "
                        "VALUES (%s, %s, %s, %s)",
                        (wf_id, task_def["task_type"], task_def["depends_on"], json.dumps(input_data)),
                    )
                cur.execute(
                    "UPDATE workflows SET workflow_status = 'running', updated_at = NOW() WHERE id = %s",
                    (wf_id,),
                )
                log.info("Started workflow %d with %d tasks", wf_id, len(SPEC["tasks"]))

            cur.execute("SELECT id FROM workflows WHERE workflow_status = 'running'")
            running = cur.fetchall()

            for (wf_id,) in running:
                cur.execute("SELECT task_status FROM tasks WHERE workflow_id = %s", (wf_id,))
                statuses = [r[0] for r in cur.fetchall()]

                if all(s == "completed" for s in statuses):
                    cur.execute(
                        "UPDATE workflows SET workflow_status = 'completed', updated_at = NOW(), "
                        "result = (SELECT output_data FROM tasks WHERE workflow_id = %s AND task_type = 'verdict') "
                        "WHERE id = %s",
                        (wf_id, wf_id),
                    )
                    log.info("Workflow %d completed", wf_id)
                elif any(s == "failed" for s in statuses):
                    cur.execute(
                        "UPDATE workflows SET workflow_status = 'failed', updated_at = NOW() WHERE id = %s",
                        (wf_id,),
                    )
                    log.info("Workflow %d failed", wf_id)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        put_connection(conn)


if __name__ == "__main__":
    log.info("Orchestrator started")
    while True:
        try:
            poll()
        except Exception:
            log.exception("Poll error")
        time.sleep(2)
