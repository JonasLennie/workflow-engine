import usePolling from "../hooks/usePolling";

const VERDICT_COLORS = {
  PASS: "#22c55e",
  WARNING: "#eab308",
  FAIL: "#ef4444",
};

export default function ResultsView({ workflowId }) {
  const { data } = usePolling(
    workflowId ? `/results/${workflowId}` : null,
    3000
  );

  if (!workflowId || !data?.result) return null;

  const { verdict, summary, outliers, trends } = data.result;

  return (
    <section className="panel">
      <h2>Results</h2>
      <div className="verdict" style={{ background: VERDICT_COLORS[verdict] || "#94a3b8" }}>
        {verdict}
      </div>
      <p>{summary}</p>

      {outliers?.length > 0 && (
        <details>
          <summary>Outliers ({outliers.length})</summary>
          <pre>{JSON.stringify(outliers, null, 2)}</pre>
        </details>
      )}

      {trends?.length > 0 && (
        <details>
          <summary>Trends ({trends.length})</summary>
          <pre>{JSON.stringify(trends, null, 2)}</pre>
        </details>
      )}
    </section>
  );
}
