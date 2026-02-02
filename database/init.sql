CREATE TABLE workflows (
    id SERIAL PRIMARY KEY,
    workflow_type VARCHAR(255) NOT NULL DEFAULT 'manufacturing_analysis',
    workflow_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_data JSONB NOT NULL,
    result JSONB
);

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    workflow_id INT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    task_type VARCHAR(255) NOT NULL,
    task_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    depends_on TEXT[] NOT NULL DEFAULT '{}',
    input_data JSONB,
    output_data JSONB,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lease_expires_at TIMESTAMP,
    attempts INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 3
);

CREATE INDEX idx_tasks_acquirable ON tasks (task_status, lease_expires_at);
CREATE INDEX idx_tasks_workflow ON tasks (workflow_id);
CREATE INDEX idx_workflows_status ON workflows (workflow_status);
