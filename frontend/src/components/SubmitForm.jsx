import { useState } from "react";

const SAMPLE_DATA = JSON.stringify(
  {
    sensor_readings: [
      { sensor_id: "temp_1", values: [72.1, 73.4, 71.8, 99.2, 72.5] },
      { sensor_id: "pressure_1", values: [14.7, 14.8, 14.6, 14.7, 14.9] },
    ],
    measurements: [
      { part_id: "A100", dimension: "width", values: [10.01, 10.02, 9.98, 10.0] },
    ],
    metadata: { batch_id: "B-2026-001", line: "assembly_3" },
  },
  null,
  2
);

export default function SubmitForm({ onCreated }) {
  const [input, setInput] = useState(SAMPLE_DATA);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: input,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      onCreated(data.workflow_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="panel">
      <h2>Submit Workflow</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={14}
          spellCheck={false}
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Submitting..." : "Submit"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
