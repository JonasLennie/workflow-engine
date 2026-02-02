import usePolling from "../hooks/usePolling";

const STATUS_COLORS = {
  completed: "#22c55e",
  running: "#eab308",
  pending: "#94a3b8",
  failed: "#ef4444",
};

export default function StatusTracker({ workflowId }) {
  const { data } = usePolling(
    workflowId ? `/status/${workflowId}` : null,
    2000
  );

  if (!workflowId) return null;

  return (
    <section className="panel">
      <h2>Status - Workflow #{workflowId}</h2>
      {!data ? (
        <p>Loading...</p>
      ) : (
        <>
          <p>
            Workflow: <span className="badge" style={{ background: STATUS_COLORS[data.status] }}>{data.status}</span>
          </p>
          <div className="task-list">
            {data.tasks?.map((t) => (
              <div key={t.task_type} className="task-card">
                <span className="task-name">{t.task_type}</span>
                <span className="badge" style={{ background: STATUS_COLORS[t.task_status] }}>
                  {t.task_status}
                </span>
                {t.error && <span className="error-text">({t.error})</span>}
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
