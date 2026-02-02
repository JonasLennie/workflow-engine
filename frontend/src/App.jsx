import { useState } from "react";
import SubmitForm from "./components/SubmitForm";
import StatusTracker from "./components/StatusTracker";
import ResultsView from "./components/ResultsView";

export default function App() {
  const [workflowId, setWorkflowId] = useState(null);

  return (
    <div className="app">
      <h1>Manufacturing Workflow Engine</h1>
      <div className="panels">
        <SubmitForm onCreated={setWorkflowId} />
        <StatusTracker workflowId={workflowId} />
        <ResultsView workflowId={workflowId} />
      </div>
    </div>
  );
}
