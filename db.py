import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=os.environ["DATABASE_URL"],
        )
    return _pool


def get_connection():
    conn = get_pool().getconn()
    conn.autocommit = False
    return conn


def put_connection(conn):
    get_pool().putconn(conn)


def query(sql, params=None, fetch=True):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            result = cur.fetchall() if fetch else None
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        put_connection(conn)


def execute(sql, params=None):
    return query(sql, params, fetch=False)
