# 数据库、Redis 与 Graph Agent 设计

## PostgreSQL

PostgreSQL 负责持久化保存:

- `runs`: 每次研究任务。
- `result_items`: Paper Pool、Fact Pool、Gap Pool、Hypothesis Pool、Review Pool。
- `tool_calls`: 每次工具调用的输入、输出、日志和状态。
- `literature_edges`: Graph Agent 生成的论文关系边。

当前使用 `pgvector/pgvector:pg16` 镜像, 后续可以把论文 chunk embedding 和假设 embedding
保存到 PostgreSQL 中。

共享开发环境连接信息:

| 字段 | 值 |
| --- | --- |
| Host | `159.75.37.44` |
| Port | `5432` |
| User | `root` |
| Database | `postgres` |
| Password | 见项目本地 `.env` 的 `POSTGRES_PASSWORD` |
| SQLAlchemy URL | 见项目本地 `.env` 的 `DATABASE_URL` |

说明: 当前未提供独立数据库名, 因此 `.env` 先按 PostgreSQL 默认库 `postgres` 配置。如果服务器后续创建 `ai_scientist` 数据库, 需要同步修改 `POSTGRES_DB` 和 `DATABASE_URL`。

## Redis

Redis 使用 `redis/redis-stack` 镜像, 主要职责:

- 上下文记忆: 保存 run 的短期状态、用户反馈、最近 Agent 输出。
- RAG 缓存: 保存检索结果、论文 chunk 缓存、embedding 检索临时结果。
- 任务状态缓存: 前端轮询当前节点时优先从 Redis 读取。
- 后续扩展: 使用 Redis Stack 的搜索/向量能力做轻量 RAG。

共享开发环境连接信息:

| 字段 | 值 |
| --- | --- |
| Host | `159.75.37.44` |
| Port | `6379` |
| Username | 无 |
| Password | 见项目本地 `.env` 的 `REDIS_PASSWORD` |
| Redis URL | 见项目本地 `.env` 的 `REDIS_URL` |

## Graph Agent

Graph Agent 用于生成和查询文献之间的关系, 帮助系统从“论文列表”升级为“论文知识网络”。

关系类型:

- shared_dataset: 使用相同数据集。
- shared_task: 研究相同视觉任务。
- method_lineage: 方法继承或改进关系。
- citation: 引用关系。
- shared_keyword: 关键词相似。
- semantic_similarity: embedding 语义相似。

输出:

```json
{
  "nodes": [],
  "edges": [],
  "summary": {
    "num_papers": 0,
    "num_relations": 0
  }
}
```

Graph Agent 的结果会写入 `literature_graph`, 并被 Evidence Integrator、Gap Discovery 和
Hypothesis Agents 使用。
