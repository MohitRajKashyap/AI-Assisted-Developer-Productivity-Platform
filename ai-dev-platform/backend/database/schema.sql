-- AI Developer Productivity Platform Database Schema

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'developer',
    api_key_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    repo_url TEXT,
    language TEXT,
    owner_id TEXT REFERENCES users(id),
    context_file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prompt_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    strategy TEXT NOT NULL, -- baseline, cot, few_shot, negative, self_reflection, context_window
    template TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    project_id TEXT REFERENCES projects(id),
    created_by TEXT REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prompt_experiments (
    id TEXT PRIMARY KEY,
    name TEXT,
    task TEXT NOT NULL,
    input_code TEXT,
    strategies TEXT NOT NULL, -- JSON array of strategies tested
    results JSON, -- JSON object with results per strategy
    winner TEXT,
    project_id TEXT REFERENCES projects(id),
    created_by TEXT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluations (
    id TEXT PRIMARY KEY,
    experiment_id TEXT REFERENCES prompt_experiments(id),
    strategy TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    latency_ms INTEGER,
    correctness_score REAL,
    relevance_score REAL,
    completeness_score REAL,
    consistency_score REAL,
    hallucination_score REAL,
    overall_score REAL,
    cost_usd REAL,
    raw_output TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bug_reports (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    stack_trace TEXT,
    severity TEXT, -- critical, high, medium, low
    category TEXT, -- regression, new_bug, performance, security
    status TEXT DEFAULT 'open', -- open, in_progress, resolved, closed
    project_id TEXT REFERENCES projects(id),
    reporter_id TEXT REFERENCES users(id),
    assignee_id TEXT REFERENCES users(id),
    analysis_result JSON,
    fix_suggestions JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pull_requests (
    id TEXT PRIMARY KEY,
    pr_number INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    diff TEXT NOT NULL,
    base_branch TEXT DEFAULT 'main',
    head_branch TEXT,
    author TEXT,
    project_id TEXT REFERENCES projects(id),
    review_result JSON,
    review_status TEXT DEFAULT 'pending', -- pending, reviewed, approved, changes_requested
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_executions (
    id TEXT PRIMARY KEY,
    workflow_type TEXT NOT NULL, -- bug_triage, pr_review, error_fix, doc_gen
    input_data JSON NOT NULL,
    agent_steps JSON, -- array of {agent, input, output, duration_ms}
    final_output JSON,
    status TEXT DEFAULT 'running', -- running, completed, failed
    total_duration_ms INTEGER,
    total_tokens INTEGER,
    total_cost_usd REAL,
    error_message TEXT,
    project_id TEXT REFERENCES projects(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL, -- bug_triage, pr_review, experiment_summary, weekly_digest
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    project_id TEXT REFERENCES projects(id),
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS context_files (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    file_type TEXT, -- overview, architecture, standards, api_docs, guidelines
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_evaluations_experiment ON evaluations(experiment_id);
CREATE INDEX IF NOT EXISTS idx_bug_reports_project ON bug_reports(project_id);
CREATE INDEX IF NOT EXISTS idx_bug_reports_status ON bug_reports(status);
CREATE INDEX IF NOT EXISTS idx_pr_project ON pull_requests(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_exec_type ON agent_executions(workflow_type);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_strategy ON prompt_templates(strategy);
