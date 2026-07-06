# AI Scientist

Web-first CV AI Scientist prototype using Qwen/DashScope-compatible APIs, LangGraph,
PostgreSQL, and Redis.

## Quick Start

1. Start database services:

```bash
docker compose up -d
```

2. Install dependencies:

```bash
pip install -e ".[dev]"
```

3. Start the API:

```bash
uvicorn app.main:app --reload
```

4. Start the web UI:

```bash
streamlit run frontend/streamlit_app.py
```

## Architecture

- PostgreSQL: persistent runs, result pools, tool calls, and literature graph edges.
- Redis: context memory, run cache, RAG/cache layer, and future vector search with Redis Stack.
- Graph Agent: builds paper relationship graphs from shared citations, method lineage,
  datasets, tasks, and semantic similarity.

## Team Repository

Gitee repository:

```text
https://gitee.com/cxcy666_admin/ai--scientist
```

Invite link:

```text
https://gitee.com/cxcy666_admin/ai--scientist/invite_link?invite=0f140dabfbedf159a3f80d7774e2d7903790a5cb447d1991e511b1509403e86ee7cbd7aba9cd3b6a8da87cab6e3c90fa
```
