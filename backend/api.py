import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import get_connection, put_connection
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Workflow Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class WorkflowRequest(BaseModel):
    sensor_readings: list = []
    measurements: list = []
    metadata: dict = {}


@app.post("/workflow")
def create_workflow(payload: WorkflowRequest):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO workflows (input_data) VALUES (%s) RETURNING id",
                (json.dumps(payload.model_dump()),),
            )
            workflow_id = cur.fetchone()[0]
        conn.commit()
        return {"workflow_id": workflow_id}
    except Exception:
        conn.rollback()
        raise
    finally:
        put_connection(conn)


@app.get("/status/{workflow_id}")
def get_status(workflow_id: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, workflow_status, created_at, updated_at FROM workflows WHERE id = %s",
                (workflow_id,),
            )
            wf = cur.fetchone()
            if not wf:
                raise HTTPException(status_code=404, detail="Workflow not found")

            cur.execute(
                "SELECT task_type, task_status, attempts, error FROM tasks WHERE workflow_id = %s ORDER BY id",
                (workflow_id,),
            )
            tasks = cur.fetchall()
        conn.commit()
        return {
            "workflow_id": wf["id"],
            "status": wf["workflow_status"],
            "created_at": str(wf["created_at"]),
            "updated_at": str(wf["updated_at"]),
            "tasks": [dict(t) for t in tasks],
        }
    finally:
        put_connection(conn)


@app.get("/results/{workflow_id}")
def get_results(workflow_id: int):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, workflow_status, result FROM workflows WHERE id = %s",
                (workflow_id,),
            )
            wf = cur.fetchone()
            if not wf:
                raise HTTPException(status_code=404, detail="Workflow not found")
            if wf["workflow_status"] != "completed":
                raise HTTPException(status_code=409, detail="Workflow not yet completed")
        conn.commit()
        return {
            "workflow_id": wf["id"],
            "status": wf["workflow_status"],
            "result": wf["result"],
        }
    finally:
        put_connection(conn)
