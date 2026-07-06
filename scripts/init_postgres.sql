CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    domain TEXT,
    task_type TEXT,
    status TEXT NOT NULL DEFAULT 'created',
    current_node TEXT,
    iteration INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS result_items (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    pool_type TEXT NOT NULL,
    source_agent TEXT,
    content_json JSONB NOT NULL,
    confidence DOUBLE PRECISION,
    status TEXT NOT NULL DEFAULT 'candidate',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    input_json JSONB,
    output_json JSONB,
    stdout TEXT,
    stderr TEXT,
    exit_code INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS literature_edges (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    source_paper_id TEXT NOT NULL,
    target_paper_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    evidence TEXT,
    weight DOUBLE PRECISION DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_result_items_run_pool ON result_items(run_id, pool_type);
CREATE INDEX IF NOT EXISTS idx_literature_edges_run ON literature_edges(run_id);
