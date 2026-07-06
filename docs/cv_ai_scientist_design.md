# CV AI Scientist 多智能体系统开发设计文档

版本: v0.1  
日期: 2026-07-06  
项目方向: 基于国产开源大模型的计算机视觉 AI Scientist  
推荐技术栈: Qwen/百炼 + LangChain + LangGraph + FastAPI + PyTorch/OpenCV

## 1. 项目目标

本项目要开发一个面向计算机视觉研究场景的 AI Scientist 原型系统。系统围绕一个具体 CV 科研问题, 自动完成文献检索、事实抽取、视觉数据集分析、知识缺口识别、候选假设生成、审稿式反思、实验设计、小规模工具验证和最终研究计划生成。

系统最终输出一份结构化的《科学假设与研究计划》, 字段包括:

- Problem Statement: 待研究问题
- Rationale: 解决思路和推理链
- Technical Details: 技术手段
- Datasets: 数据集
- Source: 假设依据的历史数据和文献事实
- Target: 验证实验需要采集或使用的数据特征
- Paper Title: 论文标题
- Paper Abstract: 摘要
- Methods: 方法论和模型/实验流程
- Experiments: baseline、ablation、metrics
- Results: 小规模验证结果或可行性分析
- References: 真实可查的参考文献

本项目不是普通论文问答系统, 也不是单 Agent 的论文 idea 生成器。核心设计是:

> 以 LangGraph 为多智能体编排核心, 以 Result Pool 管理多智能体候选结果, 以工具调用增强文献检索、视觉数据分析和实验验证能力, 构建一个可迭代、可审稿、可验证的 CV AI Scientist 系统。

## 2. 推荐选题范围

第一阶段不要做泛 CV, 必须选一个可验证的垂直场景。推荐优先级如下:

| 方向 | 推荐度 | 原因 |
| --- | --- | --- |
| 工业缺陷检测 | 高 | 数据公开、实验轻量、demo 稳定, 可用 MVTec AD 或 VisA |
| 遥感小目标检测/变化检测 | 高 | 应用价值强, 比赛叙事更好, 可用 DOTA、DIOR、LEVIR-CD 等 |
| 医学影像检测/分割 | 中 | 科学价值高, 但合规和专业解释门槛更高 |
| 泛 CV 方法创新 | 低 | 容易变成论文助手, 科学问题不够聚焦 |

建议 MVP 先做工业缺陷检测, 因为更容易跑通文献、数据、实验、可视化闭环。若团队有遥感或医学老师资源, 可替换为对应方向。

## 3. 总体系统架构

```mermaid
flowchart TD
    A["用户输入: 研究问题 + 数据集 + 可选论文"] --> B["Supervisor Agent"]

    B --> C["Problem Parser Agent"]
    C --> D1["Literature Team"]
    C --> D2["Dataset Team"]
    C --> D3["Domain Knowledge Agent"]

    D1 --> E1["Paper Pool"]
    D1 --> E2["Fact Pool"]
    D1 --> E5["Graph Agent"]
    E5 --> E6["Literature Graph"]
    D2 --> E3["Dataset Profile"]
    D3 --> E4["Domain Context"]

    E1 --> F["Evidence Integrator Agent"]
    E2 --> F
    E6 --> F
    E3 --> F
    E4 --> F

    F --> G["Gap Discovery Agent"]

    G --> H1["Literature-driven Hypothesis Agent"]
    G --> H2["Data-driven Hypothesis Agent"]
    G --> H3["Cross-domain Transfer Agent"]
    G --> H4["Model Innovation Agent"]

    H1 --> I["Hypothesis Pool"]
    H2 --> I
    H3 --> I
    H4 --> I

    I --> J1["Novelty Reviewer Agent"]
    I --> J2["Feasibility Reviewer Agent"]
    I --> J3["Evidence Reviewer Agent"]
    I --> J4["Reproducibility Reviewer Agent"]

    J1 --> K["Aggregation Agent"]
    J2 --> K
    J3 --> K
    J4 --> K

    K --> L{"Review Passed?"}
    L -- "No" --> G
    L -- "Need Human" --> M["Human Review Node"]
    L -- "Yes" --> N["Experiment Designer Agent"]

    M --> N
    N --> O["Tool Execution Node"]
    O --> P["Result Interpreter Agent"]
    P --> Q["Report Writer Agent"]
    Q --> R["Final Report + Demo"]
```

架构采用三类编排:

1. 串行主流程: 问题解析 -> 信息收集 -> 证据融合 -> 假设生成 -> 审稿 -> 实验 -> 报告。
2. 并行候选生成: 多个假设 Agent 同时产出不同风格的候选假设。
3. 条件循环: 审稿失败回到知识缺口或假设生成节点, 最多迭代 3 轮。

架构口径说明:

- `Supervisor Agent` 是唯一的总控智能体, 负责调度和质量门控。
- `Graph Agent` 是业务 Agent, 负责生成论文关系图。
- `Tool Execution Node` 是工具执行节点, 不作为独立科研 Agent 展示。
- `Human Review Node` 是人在回路节点, 不作为 AI Agent 展示。
- 流程分支由 LangGraph 条件边实现, 不单独设置独立路由智能体。

## 4. Agent 分层设计

### 4.1 总控层

#### Supervisor Agent

职责:

- 读取全局状态。
- 判断当前阶段缺少哪些产物。
- 调度下一个节点或子图。
- 控制最多迭代次数。
- 在低置信度或高风险时触发人工确认。

输入:

- 全局 `ScientistState`

输出:

```json
{
  "next_node": "retrieve_literature",
  "reason": "paper_pool is empty and user query has been parsed",
  "confidence": 0.91
}
```

注意:

- Supervisor 不负责写论文、不直接生成最终假设。
- Supervisor 只做路由和质量门控。

#### LangGraph 条件路由

系统不单独设置独立路由智能体。路由由 `Supervisor Agent` 给出控制建议, 再由 LangGraph 条件边执行。

条件路由职责:

- 根据审稿分数决定流程分支。
- 根据迭代次数决定继续自动修正还是进入人工审核。
- 支持 `design_experiment`、`generate_hypotheses`、`find_gaps`、`human_review`、`end` 等路径。

路由规则示例:

```text
if final_score >= 80 and evidence_score >= 75:
    go to experiment_design
elif iteration < 3 and evidence_score < 75:
    go to evidence_integration
elif iteration < 3:
    go to hypothesis_generation
else:
    go to human_review
```

实现建议:

```python
def route_after_review(state: ScientistState) -> str:
    ...
```

### 4.2 信息获取层

#### Problem Parser Agent

职责:

- 将用户输入的自然语言研究问题转成结构化任务。
- 判断任务类型: classification、detection、segmentation、anomaly_detection、change_detection。
- 识别领域: industrial、remote_sensing、medical、general_cv。

输出示例:

```json
{
  "domain": "industrial",
  "task_type": "anomaly_detection",
  "target_problem": "few-shot visual anomaly detection under limited defect samples",
  "constraints": ["open dataset", "lightweight validation", "reproducible baseline"],
  "success_metrics": ["AUROC", "F1", "PRO"]
}
```

#### Literature Search Agent

职责:

- 根据问题和关键词检索真实论文。
- 优先检索近 5 年论文, 同时保留经典 baseline。
- 输出论文候选池, 不做深度总结。

工具:

- arXiv Search Tool
- Semantic Scholar Tool
- Crossref DOI Tool
- Local PDF Loader
- Vector Retriever

输出字段:

```json
{
  "paper_id": "paper_001",
  "title": "...",
  "authors": ["..."],
  "year": 2024,
  "venue": "...",
  "url": "...",
  "doi": "...",
  "arxiv_id": "...",
  "relevance_score": 0.87
}
```

#### Paper Reader Agent

职责:

- 读取论文 PDF、abstract、introduction、method、experiment、limitation。
- 不直接生成假设。
- 产出可追溯的论文摘要卡片。

工具:

- PDF Parser
- HTML Parser
- OCR Tool 可选

#### Fact Extractor Agent

职责:

- 从论文中抽取结构化事实。
- 每条事实必须绑定证据来源。
- 不允许生成没有来源的结论。

输出示例:

```json
{
  "fact_id": "fact_032",
  "claim": "Patch-based reconstruction methods can miss subtle texture anomalies in low-data regimes.",
  "evidence_text": "...",
  "source_paper_id": "paper_008",
  "section": "Experiments",
  "page": 7,
  "confidence": 0.82
}
```

#### Graph Agent

职责:

- 基于 Paper Pool 构建文献关系图。
- 识别论文之间的 shared_dataset、shared_task、method_lineage、citation、shared_keyword、semantic_similarity 等关系。
- 将关系图写入 `literature_graph`, 供 Evidence Integrator、Gap Discovery 和 Hypothesis Agents 使用。

输入:

- Paper Pool
- Fact Pool
- 可选的 citation metadata 和 embedding 相似度

输出示例:

```json
{
  "nodes": [
    {
      "id": "paper_001",
      "title": "...",
      "year": 2024
    }
  ],
  "edges": [
    {
      "source": "paper_001",
      "target": "paper_002",
      "relation_type": "shared_dataset",
      "evidence": "MVTec AD",
      "weight": 0.87
    }
  ],
  "summary": {
    "num_papers": 10,
    "num_relations": 18
  }
}
```

#### Dataset Profiling Agent

职责:

- 分析视觉数据集本身。
- 这是 CV 方向区别于普通文献助手的关键模块。

工具:

- Dataset Loader
- COCO/VOC/Yolo Annotation Parser
- OpenCV Image Analyzer
- Image Quality Analyzer
- Plot Generator

统计项:

- 图片数量、训练/测试划分。
- 类别分布。
- 图像尺寸分布。
- 目标框面积分布。
- 小目标比例。
- 缺陷区域比例。
- 模糊、低光、噪声估计。
- 样本可视化。
- train/test 分布差异。

输出示例:

```json
{
  "dataset_name": "MVTec AD",
  "num_images": 5354,
  "task_type": "anomaly_detection",
  "class_distribution": {},
  "image_size_distribution": {},
  "defect_area_ratio": {},
  "quality_statistics": {
    "blur_score_mean": 0.41,
    "brightness_mean": 0.56
  },
  "observations": [
    "Most defects occupy less than 5% of image area.",
    "Texture categories show higher intra-class variation than object categories."
  ],
  "artifacts": {
    "profile_json": "outputs/dataset_profile.json",
    "plots": ["outputs/class_distribution.png"]
  }
}
```

### 4.3 科研推理层

#### Evidence Integrator Agent

职责:

- 融合论文事实、文献关系图、数据画像和领域背景。
- 形成 Evidence Board。
- 标记矛盾、空白和可迁移技术。

输出:

```json
{
  "known_facts": [],
  "dataset_observations": [],
  "contradictions": [],
  "under_explored_factors": [],
  "transferable_methods": []
}
```

#### Gap Discovery Agent

职责:

- 找出 3-5 个具体知识缺口。
- 每个 gap 都必须有事实依据和数据观察依据。

输出:

```json
{
  "gap_id": "gap_001",
  "description": "Existing anomaly detection methods rarely model defect area ratio as an explicit prior.",
  "supporting_facts": ["fact_003", "fact_019"],
  "supporting_dataset_observations": ["obs_002"],
  "research_value": 0.84,
  "testability": 0.79
}
```

#### Hypothesis Agents

设置 4 个并行假设生成 Agent, 每个 Agent 生成 2-3 个候选假设。

1. Literature-driven Hypothesis Agent  
   从论文局限和未解决问题出发。

2. Data-driven Hypothesis Agent  
   从数据集统计异常、分布偏差和视觉质量问题出发。

3. Cross-domain Transfer Agent  
   从其他 CV 任务迁移方法, 如频域增强、扩散模型、对比学习、测试时自适应。

4. Model Innovation Agent  
   从模型结构、损失函数、训练策略或推理策略出发。

候选假设必须使用统一结构:

```json
{
  "hypothesis_id": "hyp_001",
  "source_agent": "data_driven_hypothesis_agent",
  "hypothesis": "In few-shot industrial anomaly detection, explicitly modeling defect area ratio as a scale prior can improve localization stability for tiny defects.",
  "mechanism": "Tiny defects are diluted by global reconstruction losses; scale-aware priors can increase sensitivity to local residuals.",
  "expected_effect": "Improve pixel-level AUROC and PRO on small-defect classes.",
  "required_data": ["normal images", "limited defect masks"],
  "test_method": "Compare PatchCore baseline with a scale-aware residual weighting module.",
  "supporting_evidence": ["fact_003", "obs_002"],
  "risks": ["May overfit to specific defect categories"],
  "novelty_score": null,
  "feasibility_score": null,
  "evidence_score": null
}
```

### 4.4 批判验证层

#### Novelty Reviewer Agent

职责:

- 判断假设是否像已有论文的简单复述。
- 检查是否有明确创新点。

评分:

- 0-40: 基本重复已有工作。
- 40-70: 有组合创新, 但不够清晰。
- 70-90: 有明确新机制或新验证角度。
- 90-100: 高创新且有潜在论文价值。

#### Feasibility Reviewer Agent

职责:

- 判断假设能否在比赛时间和算力内验证。
- 检查数据集、baseline、指标、训练成本。

#### Evidence Reviewer Agent

职责:

- 检查每个推理链是否有真实论文或数据支撑。
- 如果引用缺失, 必须要求回退。

#### Reproducibility Reviewer Agent

职责:

- 检查实验是否可以复现。
- 检查代码、随机种子、数据路径、依赖和指标计算是否明确。

#### Aggregation Agent

职责:

- 汇总所有 Reviewer 的评分。
- 选择 Top-1 或融合 Top-2 假设。
- 输出最终选中假设和改写建议。

评分公式:

```text
final_score =
  0.30 * novelty_score +
  0.25 * feasibility_score +
  0.25 * evidence_score +
  0.20 * reproducibility_score
```

通过条件:

- final_score >= 80
- evidence_score >= 75
- feasibility_score >= 70

### 4.5 实验执行层

#### Experiment Designer Agent

职责:

- 将选中假设转成实验计划。
- 明确 baseline、proposed variant、metrics、ablation、expected result。

输出:

```json
{
  "baseline": ["PatchCore", "PaDiM"],
  "proposed_variant": "Scale-aware residual weighting",
  "dataset": "MVTec AD",
  "metrics": ["image-AUROC", "pixel-AUROC", "PRO", "F1"],
  "ablation": [
    "without scale prior",
    "with fixed scale prior",
    "with adaptive scale prior"
  ],
  "minimum_validation": "Run on 2 categories with 1 random seed for MVP."
}
```

#### Code Generation Agent

职责:

- 生成或修改实验配置。
- 不直接在生产目录写不可控代码。
- 只输出 patch 建议或在 sandbox 中生成脚本。

#### Tool Execution Node

职责:

- 调用真实工具执行数据统计、baseline 推理、小规模训练或图表生成。
- 记录 stdout、stderr、exit code、artifact 路径。

工具:

- Python Executor
- OpenCV Analyzer
- PyTorch Runner
- YOLO Runner 可选
- Anomalib Runner 可选
- Metric Calculator
- Plot Generator

#### Result Interpreter Agent

职责:

- 解释实验结果。
- 区分真实结果、初步结果和预期结果。
- 不允许把未运行的实验写成已验证结果。

## 5. Result Pool 设计

多智能体系统的核心不是让 Agent 各说各话, 而是把多个候选结果沉淀到统一结果池中。

建议维护以下池:

| Pool | 内容 | 生产者 | 消费者 |
| --- | --- | --- | --- |
| Paper Pool | 论文元数据 | Literature Search Agent | Paper Reader Agent |
| Fact Pool | 论文事实 | Fact Extractor Agent | Evidence Integrator Agent |
| Literature Graph Pool | 文献关系图 | Graph Agent | Evidence Integrator Agent / Gap Discovery Agent |
| Dataset Observation Pool | 数据集观察 | Dataset Profiling Agent | Evidence Integrator Agent |
| Gap Pool | 知识缺口 | Gap Discovery Agent | Hypothesis Agents |
| Hypothesis Pool | 候选假设 | 4 个 Hypothesis Agents | Reviewer Agents |
| Review Pool | 审稿评分和意见 | Reviewer Agents | Aggregation Agent |
| Artifact Pool | 图表、实验日志、报告 | Tool Execution Node | Report Writer Agent |

每条结果必须有统一元数据:

```json
{
  "id": "...",
  "type": "hypothesis",
  "source_agent": "...",
  "created_at": "...",
  "input_refs": ["fact_001", "obs_003"],
  "content": {},
  "confidence": 0.82,
  "status": "candidate"
}
```

## 6. LangGraph 状态设计

全局状态建议使用 TypedDict 或 Pydantic BaseModel。

```python
from typing import TypedDict, Literal, Any

class ScientistState(TypedDict, total=False):
    run_id: str
    user_query: str
    domain: str
    task_type: str
    constraints: list[str]

    paper_pool: list[dict]
    fact_pool: list[dict]
    literature_graph: dict
    dataset_profile: dict
    dataset_observation_pool: list[dict]
    evidence_board: dict

    gap_pool: list[dict]
    hypothesis_pool: list[dict]
    review_pool: list[dict]
    selected_hypothesis: dict

    experiment_plan: dict
    tool_outputs: dict[str, Any]
    artifacts: list[dict]

    final_report: dict
    messages: list[dict]

    iteration: int
    max_iteration: int
    route: Literal[
        "parse_problem",
        "retrieve_literature",
        "build_literature_graph",
        "profile_dataset",
        "integrate_evidence",
        "find_gaps",
        "generate_hypotheses",
        "review_hypotheses",
        "aggregate_reviews",
        "design_experiment",
        "run_tools",
        "interpret_results",
        "write_report",
        "human_review",
        "end"
    ]
```

注意事项:

- 不要把所有中间产物塞进 `messages`。
- `messages` 只保留对话和少量解释。
- 论文事实、假设、评分、工具结果必须结构化存储。

## 7. LangGraph 编排建议

主图:

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(ScientistState)

graph.add_node("parse_problem", parse_problem_node)
graph.add_node("retrieve_literature", retrieve_literature_node)
graph.add_node("read_and_extract_facts", read_and_extract_facts_node)
graph.add_node("build_literature_graph", build_literature_graph_node)
graph.add_node("profile_dataset", profile_dataset_node)
graph.add_node("integrate_evidence", integrate_evidence_node)
graph.add_node("find_gaps", find_gaps_node)
graph.add_node("generate_hypotheses", generate_hypotheses_node)
graph.add_node("review_hypotheses", review_hypotheses_node)
graph.add_node("aggregate_reviews", aggregate_reviews_node)
graph.add_node("design_experiment", design_experiment_node)
graph.add_node("run_tools", run_tools_node)
graph.add_node("interpret_results", interpret_results_node)
graph.add_node("write_report", write_report_node)
graph.add_node("human_review", human_review_node)

graph.add_edge(START, "parse_problem")
graph.add_edge("parse_problem", "retrieve_literature")
graph.add_edge("retrieve_literature", "read_and_extract_facts")
graph.add_edge("read_and_extract_facts", "build_literature_graph")
graph.add_edge("build_literature_graph", "profile_dataset")
graph.add_edge("profile_dataset", "integrate_evidence")
graph.add_edge("integrate_evidence", "find_gaps")
graph.add_edge("find_gaps", "generate_hypotheses")
graph.add_edge("generate_hypotheses", "review_hypotheses")
graph.add_edge("review_hypotheses", "aggregate_reviews")

graph.add_conditional_edges(
    "aggregate_reviews",
    route_after_review,
    {
        "design_experiment": "design_experiment",
        "generate_hypotheses": "generate_hypotheses",
        "find_gaps": "find_gaps",
        "human_review": "human_review",
    },
)

graph.add_edge("human_review", "design_experiment")
graph.add_edge("design_experiment", "run_tools")
graph.add_edge("run_tools", "interpret_results")
graph.add_edge("interpret_results", "write_report")
graph.add_edge("write_report", END)
```

并行假设生成可以在 `generate_hypotheses_node` 内部实现:

```python
async def generate_hypotheses_node(state: ScientistState) -> dict:
    results = await asyncio.gather(
        literature_hypothesis_agent.ainvoke(state),
        data_hypothesis_agent.ainvoke(state),
        transfer_hypothesis_agent.ainvoke(state),
        model_innovation_agent.ainvoke(state),
    )
    hypothesis_pool = []
    for result in results:
        hypothesis_pool.extend(result["hypotheses"])
    return {"hypothesis_pool": hypothesis_pool}
```

LangGraph 官方文档中, Graph API 使用 State、Node、Edge 建模流程, 并支持条件边。参考:

- LangGraph Graph API: https://docs.langchain.com/oss/python/langgraph/graph-api
- LangGraph conditional edges API: https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_conditional_edges
- LangGraph persistence: https://langchain-ai.github.io/langgraph/concepts/time-travel/

## 8. 工具系统设计

工具要按 Agent 权限绑定, 不能所有 Agent 都能调用所有工具。

### 8.1 文献工具

| Tool | 输入 | 输出 | 调用者 |
| --- | --- | --- | --- |
| `arxiv_search` | query, max_results | paper list | Literature Search Agent |
| `semantic_scholar_search` | query | paper list | Literature Search Agent |
| `crossref_verify` | title/doi | verified metadata | Citation Verification Agent |
| `pdf_parse` | pdf_path/url | section text | Paper Reader Agent |
| `vector_retrieve` | query | chunks | Paper Reader Agent |

### 8.2 CV 数据工具

| Tool | 输入 | 输出 | 调用者 |
| --- | --- | --- | --- |
| `dataset_scan` | dataset_path | file tree + counts | Dataset Profiling Agent |
| `coco_profile` | annotation_path | bbox/class stats | Dataset Profiling Agent |
| `image_quality_profile` | image_dir | blur/brightness/noise stats | Dataset Profiling Agent |
| `sample_visualizer` | dataset_path | image grid | Dataset Profiling Agent |
| `defect_mask_profile` | mask_dir | area ratio stats | Dataset Profiling Agent |

### 8.3 实验工具

| Tool | 输入 | 输出 | 调用者 |
| --- | --- | --- | --- |
| `python_executor` | script/config | logs + artifacts | Tool Execution Node |
| `metric_calculator` | predictions, labels | metrics | Tool Execution Node |
| `plot_generator` | csv/json | plots | Tool Execution Node |
| `baseline_runner` | config | metrics + logs | Tool Execution Node |

### 8.4 RAG 与记忆工具

| Tool | 输入 | 输出 | 调用者 |
| --- | --- | --- | --- |
| `redis_memory_set` | run_id, key, json | status | Supervisor / Tool Execution Node |
| `redis_memory_get` | run_id, key | json | Supervisor / RAG Retriever |
| `rag_cache_get` | query/cache_key | cached chunks | Literature Search Agent / Paper Reader Agent |
| `rag_cache_set` | query/cache_key, chunks | status | Literature Search Agent / Paper Reader Agent |

### 8.5 Graph Agent 工具

| Tool | 输入 | 输出 | 调用者 |
| --- | --- | --- | --- |
| `literature_graph_builder` | paper_pool, fact_pool | nodes/edges | Graph Agent |
| `literature_relation_query` | paper_id / relation_type | related papers | Evidence Integrator / Gap Discovery |

### 8.6 报告工具

| Tool | 输入 | 输出 | 调用者 |
| --- | --- | --- | --- |
| `markdown_exporter` | final_report | md file | Report Writer Agent |
| `pdf_exporter` | md/html | pdf file | Report Writer Agent |
| `citation_formatter` | references | BibTeX/GB/T | Report Writer Agent |

LangChain 工具调用参考:

- LangChain Tools: https://docs.langchain.com/oss/python/langchain/tools
- LangChain Models and tool calling: https://docs.langchain.com/oss/python/langchain/models

## 9. 模型接入方案

比赛要求基座模型必须基于千问开源模型或千问系列, 并通过阿里云百炼平台调用模型 API, 提供调用凭证或截图。

当前开发环境通过 DashScope OpenAI 兼容接口接入模型, `.env` 中 `DASHSCOPE_MODEL` 暂时配置为 `deepseek-v4-pro`。这只作为开发调试配置。比赛提交版必须按赛题要求切换到 Qwen/千问系列模型, 例如 `qwen-plus`、`qwen-max` 或当时百炼平台可用的合规 Qwen 模型, 并保留调用截图。

建议模型分配:

| 场景 | 推荐模型类型 | 说明 |
| --- | --- | --- |
| Problem Parser、格式化输出 | qwen-plus / qwen-flash | 成本低, 输出稳定 |
| 假设生成、审稿反思 | qwen-max / qwen-plus | 推理要求更高 |
| 代码生成 | qwen-coder | 生成实验脚本和配置 |
| 图像理解 | Qwen-VL / Qwen-Omni | 解读样例图和实验可视化 |
| embedding | 百炼 embedding 模型 | 文献向量检索 |

百炼支持 OpenAI 兼容接口, 迁移成本低; 也支持 DashScope 原生接口。建议第一版使用 OpenAI 兼容接口, 方便 LangChain 集成。参考:

- 百炼平台介绍: https://help.aliyun.com/zh/model-studio/what-is-model-studio
- 百炼文本生成 API: https://help.aliyun.com/zh/model-studio/qwen-api-reference
- 百炼 API Key: https://help.aliyun.com/zh/model-studio/get-api-key
- 百炼模型列表: https://help.aliyun.com/zh/model-studio/models

示例配置:

```bash
export DASHSCOPE_API_KEY="sk-..."
export DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export DASHSCOPE_MODEL="qwen-plus"
```

注意:

- 不允许把 API Key 写进代码仓库。
- `.env` 只保存在本地, `.env.example` 只放占位字段。
- 所有模型调用需要记录 model name、time、token usage, 方便提交截图和复现说明。

## 10. 后端工程结构

建议目录:

```text
AI- Scientist/
  main.py
  pyproject.toml
  docker-compose.yml
  scripts/
    init_postgres.sql
  app/
    __init__.py
    main.py
    api/
      routes_runs.py
      routes_health.py
    core/
      config.py
    db/
      postgres.py
      redis.py
    graph/
      state.py
      build_graph.py
    agents/
      graph_agent.py
    tools/
      literature/
      cv/
      rag/
        redis_memory.py
  frontend/
    streamlit_app.py
  data/
    raw/
    processed/
  outputs/
    runs/
  tests/
    test_graph_routing.py
    test_dataset_profile.py
    test_fact_schema.py
  docs/
    cv_ai_scientist_design.md
    team_plan.md
    requirements_features_metrics.md
    database_and_memory.md
```

第一阶段可以只做 FastAPI + Streamlit。前端不必过早复杂化。

## 11. API 设计

### 11.1 创建研究任务

`POST /runs`

请求:

```json
{
  "query": "研究工业缺陷检测中小缺陷定位不稳定的问题",
  "domain": "industrial",
  "task_type": "anomaly_detection",
  "dataset_path": "data/raw/mvtec",
  "paper_urls": [],
  "max_iterations": 3
}
```

响应:

```json
{
  "run_id": "run_20260706_001",
  "status": "created"
}
```

### 11.2 执行或继续任务

`POST /runs/{run_id}/invoke`

响应:

```json
{
  "run_id": "run_20260706_001",
  "status": "running",
  "current_node": "retrieve_literature"
}
```

### 11.3 获取状态

`GET /runs/{run_id}`

响应:

```json
{
  "run_id": "run_20260706_001",
  "status": "waiting_human_review",
  "current_node": "human_review",
  "selected_hypothesis": {},
  "review_summary": {}
}
```

### 11.4 人工反馈

`POST /runs/{run_id}/feedback`

请求:

```json
{
  "decision": "approve",
  "selected_hypothesis_id": "hyp_003",
  "comments": "优先选择可在 MVTec 上快速验证的假设"
}
```

### 11.5 获取产物

`GET /runs/{run_id}/artifacts`

响应:

```json
{
  "artifacts": [
    {
      "type": "dataset_plot",
      "path": "outputs/runs/run_001/class_distribution.png"
    },
    {
      "type": "final_report",
      "path": "outputs/runs/run_001/final_report.md"
    }
  ]
}
```

## 12. 前端演示设计

本项目当前确定按网页版进行交互和展示。后端核心仍然用 Python + FastAPI + LangGraph 实现, 前端只负责展示流程、收集用户输入、触发任务、查看中间结果和导出报告, 不把 Agent 逻辑写在前端里。

推荐第一版使用 `Streamlit` 做网页版 MVP。原因是三人团队时间有限, Streamlit 能快速展示表格、图表、状态流、Markdown 报告和人工反馈按钮。若 8 月中旬前核心功能已经稳定, 再考虑升级为 `React/Vite + FastAPI` 的正式网页端。

### 12.1 网页端页面规划

页面:

1. Run 创建页
   - 研究问题输入框
   - 领域选择
   - 任务类型选择
   - 数据集路径输入
   - 上传论文 PDF
   - 选择模型和最大迭代次数
   - 创建任务按钮

2. 工作流可视化页
   - 显示当前 Agent 节点
   - 显示 Result Pool 数量
   - 显示迭代次数
   - 显示工具执行日志
   - 显示每个节点状态: pending、running、success、failed
   - 支持刷新任务状态

3. 候选假设页
   - 表格展示多个假设
   - 展示 novelty、feasibility、evidence、reproducibility 分数
   - 支持人工选择或驳回
   - 支持查看每个假设的证据来源

4. 实验结果页
   - 数据画像图
   - baseline 指标
   - 消融实验表
   - 可视化样例
   - 区分已执行结果、初步结果和预期结果

5. 报告页
   - Markdown 预览
   - 导出 PDF
   - 展示 References, 且引用只能来自 Paper Pool

### 12.2 网页端交互流程

```text
用户打开网页
  -> 创建研究任务
  -> 后端创建 run_id
  -> 页面进入任务详情
  -> 后端执行 LangGraph
  -> 前端轮询 run 状态
  -> 展示 Agent 运行进度和 Result Pool
  -> 到达 Human Review 节点
  -> 用户选择/驳回候选假设
  -> 后端继续实验设计和工具执行
  -> 前端展示图表、日志和最终报告
```

### 12.3 MVP 前端技术选择

第一阶段:

```text
Streamlit + FastAPI + PostgreSQL + Redis
```

第二阶段可选升级:

```text
React/Vite + FastAPI + PostgreSQL + Redis
```

本项目优先保证演示完整性, 不优先追求复杂前端工程。前端的核心价值是让评委看见:

- 多智能体如何协同。
- 每个 Agent 输出了什么。
- 工具如何增强大模型。
- 人类如何参与选择和修正假设。
- 最终报告如何从中间证据生成。

## 13. 存储设计

本项目统一使用 PostgreSQL + Redis。

PostgreSQL 负责持久化保存长期数据:

- runs
- result_items
- tool_calls
- literature_edges

Redis 负责短期记忆和 RAG 缓存:

- run 当前上下文
- 最近 Agent 输出
- 文献检索缓存
- RAG chunk 缓存
- 前端轮询状态缓存

PostgreSQL 核心表:

```text
runs
  id
  query
  domain
  task_type
  status
  current_node
  iteration
  created_at
  updated_at

result_items
  id
  run_id
  pool_type
  source_agent
  content_json
  confidence
  status
  created_at

tool_calls
  id
  run_id
  tool_name
  input_json
  output_json
  stdout
  stderr
  exit_code
  created_at

literature_edges
  id
  run_id
  source_paper_id
  target_paper_id
  relation_type
  evidence
  weight
  created_at
```

Redis Key 规范:

```text
ai_scientist:run:{run_id}:context
ai_scientist:run:{run_id}:status
ai_scientist:run:{run_id}:recent_agent_outputs
ai_scientist:rag:search:{hash}
ai_scientist:rag:chunks:{paper_id}
```

## 14. 提示词设计原则

所有 Agent prompt 必须包含:

- 角色边界: 该 Agent 负责什么, 不负责什么。
- 输入字段说明。
- 工具使用规则。
- 输出 JSON schema。
- 失败处理规则。
- 禁止幻觉规则。

示例:

```text
你是 Evidence Reviewer Agent。
你的任务是检查候选假设是否有足够的论文事实和数据观察支撑。
你不能生成新的假设。
你不能虚构论文、DOI、实验结果。
如果证据不足, 必须明确指出缺失的证据类型。
请严格输出 JSON。
```

## 15. 质量门控

### 15.1 引用真实性

要求:

- 每篇论文必须有 URL、DOI 或 arXiv ID 中至少一个。
- final report 中每个关键论断要能追溯到 Fact Pool 或 Dataset Observation Pool。
- References 不允许由 Report Writer 自己临时编造。

### 15.2 假设质量

合格假设必须满足:

- 有明确问题边界。
- 有机制解释。
- 有可验证实验。
- 有数据集。
- 有 baseline。
- 有 metrics。
- 有风险说明。

### 15.3 实验真实性

报告中结果分三类标注:

- `executed_result`: 已运行工具得到。
- `pilot_result`: 小规模试验结果。
- `expected_result`: 预期结果, 不得伪装成真实实验。

## 16. 三人团队开发分工

本节只保留总设计文档中的分工摘要。具体 issue 级任务拆分、每日计划和每周验收以 `docs/team_plan.md` 为准。

当前团队:

| 成员 | 角色定位 | 核心职责 |
| --- | --- | --- |
| 杨旭 | 总架构 + 科研推理链 | LangGraph 主流程、Supervisor、PostgreSQL/Redis、Graph Agent、假设审稿聚合、实验设计、报告生成 |
| 冯佳乐 | 文献证据链 | 文献检索、PDF 解析、事实抽取、引用校验、Evidence Board、文献关系字段补充 |
| 杜灿 | 视觉数据与实验链 | 网页框架、CV 数据画像、图表工具、实验工具、结果展示、Human Review 页面 |

### 16.1 杨旭职责

杨旭既负责项目统筹, 也负责核心 Agent 和关键链路开发。

具体任务:

- 确定最终 CV 场景和数据集。
- 维护项目总设计文档和每周任务清单。
- 设计系统主架构: FastAPI、LangGraph、Agent、Tool、Result Pool。
- 设计 PostgreSQL + Redis 数据层。
- 实现 LangGraph 主流程、Supervisor Agent 和条件路由。
- 实现 Graph Agent 初版。
- 实现 Gap Discovery、Hypothesis Agents、Reviewer、Aggregation、Experiment Designer、Report Writer。
- 负责 Gitee 仓库管理、分支合并和代码 Review。
- 负责百炼/Qwen API Key 配置方案, 不把密钥提交到仓库。
- 负责最终技术方案 PDF、演示逻辑和答辩讲稿。
- 每周组织一次集成验收, 确定下周任务。

你需要亲自把控的核心文件:

```text
docs/cv_ai_scientist_design.md
app/graph/build_graph.py
app/graph/state.py
app/core/config.py
README.md
```

阶段性交付:

- 第 1 周: 项目骨架、接口规范、任务分工确认。
- 第 3 周: 后端主流程能跑通 mock 数据。
- 第 5 周: 前后端联调完成。
- 第 7 周: 完整案例跑通。
- 9 月 5 日前: 比赛提交版冻结。
- 9 月 10 日前: 答辩展示版和复盘版完善。

### 16.2 冯佳乐职责

冯佳乐负责文献证据链, 重点是让系统能够获得真实论文、真实事实和真实引用。

具体任务:

- 实现以下 Agent:
  - Literature Search Agent
  - Paper Reader Agent
  - Fact Extractor Agent
  - Evidence Integrator Agent
  - Evidence Reviewer Agent
  - Citation Verification Agent
- 实现文献类工具:
  - arXiv/Semantic Scholar 检索
  - PDF 解析
  - DOI/URL 引用校验
  - 向量检索
- 为 Graph Agent 补充 paper metadata 中的 datasets、tasks、keywords、citations 字段。
- 写文献链测试, 至少覆盖文献检索、fact schema、citation check。

交付标准:

- 输入一个研究问题, 系统可以生成 Paper Pool、Fact Pool 和 Evidence Board。
- References 只能来自真实检索结果, 不允许 Report Writer 新增虚构引用。

### 16.3 杜灿职责

杜灿负责视觉数据与实验链, 重点是让系统“看得见、点得动、有图表、有结果”。杜灿的工作不只是前端, 也包括 Dataset Profiling Agent 和 CV Tool。

具体任务:

- 实现网页版 MVP:
  - 创建研究任务页
  - 工作流状态页
  - Result Pool 展示页
  - 候选假设评分页
  - 人工选择/驳回假设交互
  - 实验结果与图表页
  - 报告预览和导出页
- 实现 CV 数据工具:
  - 数据集扫描
  - 图片数量和尺寸统计
  - 类别/缺陷分布统计
  - 目标框或缺陷区域面积统计
  - 模糊、亮度、噪声等质量统计
  - 样例图和统计图生成
- 实现实验展示工具:
  - baseline 指标展示
  - 小规模实验日志展示
  - 图表 artifact 管理
- 实现 Dataset Profiling Agent、Dataset Scan Tool、Image Quality Tool、Plot Generator Tool。
- 协助最终演示视频素材录制。

交付标准:

- 用户可以通过网页创建任务并查看运行状态。
- 页面能展示各 Agent 的中间结果。
- 页面能展示数据集画像图表和最终报告。
- 在 Human Review 节点, 用户可以选择一个假设继续后续流程。

### 16.4 三人协作边界

为了避免互相阻塞, 按接口协作:

| 模块 | 负责人 | 对外接口 |
| --- | --- | --- |
| LangGraph 主流程 | 杨旭 | `POST /runs/{run_id}/invoke` |
| PostgreSQL/Redis | 杨旭 | `DATABASE_URL`, `REDIS_URL` |
| Result Pool | 杨旭 + 冯佳乐 + 杜灿 | `GET /runs/{run_id}/results` |
| 文献证据链 | 冯佳乐 | `GET /runs/{run_id}/papers`, `GET /runs/{run_id}/facts` |
| 数据集画像 | 杜灿 | `POST /tools/dataset-profile` |
| 前端页面 | 杜灿 | 调用 FastAPI |
| 配置和部署 | 杨旭 | `.env.example`, README |
| 最终文档和答辩 | 杨旭 | PDF、PPT、演示视频 |

每日同步规则:

- 每天晚上前在群里发一次进度: 今天完成了什么、遇到什么问题、明天做什么。
- 每周至少集成一次, 集成优先级高于继续堆新功能。
- 任何接口字段改动, 必须同步到文档和示例 JSON。

## 17. 里程碑计划

当前日期是 2026-07-06, 团队计划从 2026-07-07 开发到 2026-09-10。需要注意: 赛题 PDF 中作品提交时间写的是 2026-09-05 前, 因此项目实际应分成两个版本:

- 2026-09-05 前: 比赛提交冻结版。
- 2026-09-10 前: 答辩展示完善版、复盘版和备用修复版。

### 第 0 天: 2026-07-07 启动会

目标:

- 三人确认项目方向: Web 版 CV AI Scientist。
- 确认最终优先场景, 建议先定工业缺陷检测或遥感小目标检测。
- 所有人加入 Gitee 仓库。
- 确认分工、分支规范、每周验收时间。

启动会要讲清楚:

- 我们不是做普通聊天机器人, 而是做多智能体科研流程系统。
- 网页端只是交互入口, 核心能力在后端 LangGraph。
- 每个 Agent 输出结构化结果, 进入 Result Pool。
- 工具增强必须有真实产物: 文献、引用、数据图表、实验日志。

验收:

- 三人都能拉取仓库。
- 本地能运行空项目或基础 demo。
- `.env.example`、README、目录结构建好。

### 第 1 周: 2026-07-07 到 2026-07-13

目标:

- 建立项目骨架。
- 完成 FastAPI + Streamlit 基础联通。
- 完成 LangGraph mock workflow, 包含 Graph Agent mock 节点。
- 完成 Qwen/百炼 API 调用 demo。
- 完成 PostgreSQL/Redis 基础配置。

负责人:

- 杨旭: 建仓库结构、README、任务板、接口规范、ScientistState、mock graph、PostgreSQL/Redis 配置。
- 冯佳乐: 初始化文献链目录、mock Paper Pool、mock Fact Pool、mock Evidence Board。
- 杜灿: Streamlit 首页、创建任务页、任务状态页。

验收:

- 网页能创建一个 mock run。
- 后端能从 START 跑到 END。
- 页面能显示当前节点和最终 mock report。

### 第 2 周: 2026-07-14 到 2026-07-20

目标:

- 完成文献检索、PDF 读取、基础引用校验。
- 完成 CV 数据集扫描和基础画像。
- 前端展示 Paper Pool 和 Dataset Profile。

负责人:

- 冯佳乐: Literature Search、Paper Reader、Fact Extractor 初版。
- 杜灿: Dataset Profiler、图表展示。
- 杨旭: Problem Parser、模型调用封装、PostgreSQL/Redis 读写、主流程接入真实数据。

验收:

- 一个真实 query 能检索 10 篇以上论文。
- 能抽取 20 条以上带来源的 fact。
- 一个真实数据集能生成统计 JSON 和至少 3 张图。

### 第 3 周: 2026-07-21 到 2026-07-27

目标:

- 完成 Evidence Board。
- 完成 Gap Discovery。
- 完成 4 个 Hypothesis Agents 初版。
- 前端展示 Gap Pool 和 Hypothesis Pool。

负责人:

- 冯佳乐: Evidence Board、Evidence Reviewer、文献证据补强。
- 杜灿: 候选假设表格、详情抽屉/详情区域。
- 杨旭: Gap Discovery、4 个 Hypothesis Agents、假设 JSON schema 和 prompt 质量。

验收:

- 系统能基于真实文献和数据画像生成至少 6 个候选假设。
- 每个假设必须包含 mechanism、evidence、test_method、risk。

### 第 4 周: 2026-07-28 到 2026-08-03

目标:

- 完成 4 个 Reviewer Agents。
- 完成 Aggregation Agent。
- 完成审稿失败回退循环。
- 完成 Human Review 网页交互。

负责人:

- 冯佳乐: Evidence Reviewer、引用约束、文献链测试。
- 杜灿: 评分展示、人工选择/驳回按钮。
- 杨旭: Novelty/Feasibility Reviewer、Aggregation、条件回退、评分规则和验收标准。

验收:

- 每个候选假设有 4 类评分。
- 分数不足时能自动回到假设生成或 Gap Discovery。
- 页面可以人工选择一个假设进入实验设计。

### 第 5 周: 2026-08-04 到 2026-08-10

目标:

- 完成 Experiment Designer Agent。
- 完成工具执行框架。
- 跑通一个轻量 baseline 或数据分析验证。
- 前端展示工具日志和 artifact。

负责人:

- 冯佳乐: 文献链稳定性、工具执行协助。
- 杜灿: Metric/Plot 展示、实验日志页面。
- 杨旭: Experiment Designer、最小实验范围、报告结构。

验收:

- 选中假设能生成 baseline、metrics、ablation。
- 至少有一个真实工具执行结果, 如数据统计图、baseline 指标或小规模推理日志。

### 第 6 周: 2026-08-11 到 2026-08-17

目标:

- 完成报告生成 Agent。
- 完成 Markdown 报告预览。
- 完成 PDF/HTML 导出初版。
- 跑通从网页输入到最终报告的完整闭环。

负责人:

- 冯佳乐: 引用约束、References 真实校验。
- 杜灿: 报告页面、导出按钮、artifact 列表。
- 杨旭: Report Writer、完整流程验收、报告字段。

验收:

- 网页完整跑通: 创建任务 -> Agent 流程 -> 人工选择 -> 工具执行 -> 报告生成。
- 报告包含赛题要求的所有字段。

### 第 7 周: 2026-08-18 到 2026-08-24

目标:

- 打磨真实案例。
- 补充测试和异常处理。
- 准备技术方案 PDF 初稿。
- 准备演示视频脚本。

负责人:

- 杨旭: 技术方案 PDF 初稿、讲稿、演示路线。
- 冯佳乐: 后端稳定性、引用真实性、Agent 输出质量。
- 杜灿: 前端可视化、页面体验、图表美化。

验收:

- 有一个完整真实案例可演示。
- 技术方案 PDF 初稿完成 70%。
- 演示视频脚本完成。

### 第 8 周: 2026-08-25 到 2026-08-31

目标:

- 进入比赛提交版打磨。
- 修复关键 bug。
- 完成技术方案 PDF。
- 录制 10 分钟内演示视频初版。
- 准备百炼调用截图、运行截图、代码说明。

验收:

- 提交材料初版齐全。
- 系统冻结核心功能, 不再新增大模块。
- 只允许修 bug、优化展示和补文档。

### 提交冻结期: 2026-09-01 到 2026-09-05

目标:

- 完成最终检查。
- 检查压缩包、报名表、网盘链接、截图。
- 固定代码版本和演示版本。
- 避免最后几天大改。

验收:

- 比赛提交版冻结。
- 技术方案 PDF、源码、演示视频、截图、复现说明全部准备好。

### 展示完善期: 2026-09-06 到 2026-09-10

目标:

- 在不影响提交版的前提下, 准备答辩展示版。
- 整理讲稿。
- 准备常见问题回答。
- 复盘代码结构和项目亮点。

验收:

- 杨旭可以按本文档讲清楚项目。
- 冯佳乐可以讲清楚多智能体和工具增强。
- 杜灿可以讲清楚网页交互、数据画像和实验展示。

## 18. MVP 验收标准

必须完成:

- 基于 Qwen/百炼 API 调用。
- LangGraph 多节点工作流。
- 至少 8 类 Agent 或 Node。
- 至少 5 类工具调用。
- PostgreSQL 能保存 runs、result_items、tool_calls、literature_edges。
- Redis 能按 run_id 保存和读取上下文记忆/RAG 缓存。
- Graph Agent 能基于 Paper Pool 生成文献关系图。
- 至少一个真实 CV 数据集画像。
- 至少一个真实文献检索和引用校验流程。
- 至少 6 个候选假设。
- 至少 1 轮审稿-修改循环。
- 最终生成标准化《科学假设与研究计划》。

加分项:

- 小规模 baseline 实验。
- 人在回路假设选择。
- 前端工作流可视化。
- 演示视频。
- 可复现脚本。

## 19. 风险与应对

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| Agent 太多导致系统失控 | 结果不稳定 | 主流程固定, 并行只放在候选生成和审稿阶段 |
| 引用幻觉 | 直接扣分 | References 只能来自 Paper Pool, 报告生成器不能新增引用 |
| 实验跑不动 | 无法展示验证 | 先做数据画像和小规模 baseline, 不追求大训练 |
| 前端耗时过多 | 拖慢核心功能 | 先用 Streamlit, 最后再美化 |
| 模型调用成本高 | 预算压力 | 轻节点用低成本模型, 关键节点用强模型 |
| 选题太泛 | 科学价值不足 | 固定一个场景和数据集, 做深做实 |

## 20. 向评委展示的技术亮点

建议在答辩和技术方案中重点强调:

1. 多智能体不是堆 prompt, 而是基于 LangGraph 的可追踪科研状态机。
2. 每个 Agent 产出结构化中间结果, 进入 Result Pool。
3. 多个假设 Agent 并行生成候选, 多个 Reviewer Agent 独立评分。
4. 工具增强覆盖文献检索、引用校验、CV 数据画像、实验执行和报告导出。
5. 假设生成基于论文事实和数据观察双证据。
6. 系统支持审稿式反思和多轮迭代。
7. 结果区分已执行实验、初步验证和预期结果, 避免大模型幻觉。

## 21. 下一步行动清单

### 21.1 2026-07-07 启动会行动项

1. 三人加入 Gitee 仓库: `https://gitee.com/cxcy666_admin/ai--scientist`。
2. 杨旭确认仓库权限, 冯佳乐和杜灿确认可以 clone、push 分支。
3. 确定最终 MVP 方向: 工业缺陷检测或遥感小目标检测二选一。
4. 确定前端路线: 第一版用 Streamlit 网页端, 后端用 FastAPI。
5. 确定每周集成时间, 建议每周日晚进行一次完整联调。
6. 建立第一批 issues:
   - 项目骨架初始化
   - FastAPI 基础接口
   - Streamlit 首页和任务页
   - LangGraph mock workflow
   - Qwen/百炼 API 接入
   - Dataset Profiler 初版
   - Literature Search 初版
7. 第一天不要追求功能多, 先保证三个人开发环境一致。

### 21.2 第一个可运行版本目标

第一个可运行版本不需要真实论文和真实实验全部完成, 但必须能展示系统形态:

```text
网页输入研究问题
  -> 后端创建 run
  -> LangGraph mock 流程运行
  -> 生成 mock Paper Pool / Literature Graph / Hypothesis Pool / Review Pool
  -> 网页展示节点状态和候选假设
  -> 人工选择一个假设
  -> 生成 mock final report
```

这个版本建议在 2026-07-13 前完成。只要这个闭环先跑起来, 后面替换真实工具会顺很多。

## 22. Gitee 仓库协作规范

仓库邀请链接由杨旭发送给成员, 成员接受邀请后进行开发。本文档不保存任何账号密码或 API Key。

成员邀请链接:

```text
https://gitee.com/cxcy666_admin/ai--scientist/invite_link?invite=0f140dabfbedf159a3f80d7774e2d7903790a5cb447d1991e511b1509403e86ee7cbd7aba9cd3b6a8da87cab6e3c90fa
```

### 22.1 分支规范

建议分支:

```text
main        稳定提交版, 只合并可运行代码
dev         日常集成分支
feature/*   个人功能分支
fix/*       bug 修复分支
docs/*      文档分支
```

个人分支示例:

```text
feature/feng-langgraph-core
feature/feng-literature-tools
feature/ducan-web-ui
feature/ducan-dataset-profiler
docs/project-design
```

### 22.2 提交规范

commit message 使用以下前缀:

```text
feat: 新功能
fix: bug 修复
docs: 文档
refactor: 重构
test: 测试
chore: 配置或杂项
```

示例:

```text
feat: add mock langgraph workflow
feat: add streamlit run creation page
fix: handle empty paper search result
docs: update team execution plan
```

### 22.3 合并规范

- 所有人从 `dev` 拉新分支开发。
- 功能完成后提 Pull Request / Merge Request 到 `dev`。
- 杨旭完成代码 Review 后合并。
- `main` 只在每周验收通过或提交冻结时从 `dev` 合并。
- 不允许直接把未测试代码推到 `main`。

### 22.4 环境变量规范

必须提供 `.env.example`, 但不能提交真实 `.env`。

示例:

```bash
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_API_KEY=
DASHSCOPE_MODEL=qwen-plus
DATABASE_URL=postgresql+asyncpg://root:CHANGE_ME@159.75.37.44:5432/postgres
REDIS_URL=redis://:CHANGE_ME@159.75.37.44:6379/0
OUTPUT_DIR=./outputs
```

`.gitignore` 必须包含:

```text
.env
data/raw/
outputs/
*.log
__pycache__/
.DS_Store
```

### 22.5 每周验收规则

每周验收只看可运行产物, 不只看口头进度。

每周需要回答:

- 这个星期能从网页点到哪里?
- 后端 LangGraph 跑到了哪个节点?
- 有哪些真实工具已经接入?
- 有哪些中间结果可以展示?
- 下周最可能阻塞的点是什么?

## 23. 杨旭讲解提纲

你开会时可以按以下顺序讲:

1. 比赛目标  
   我们要做的是基于 Qwen/百炼的 CV AI Scientist, 不是普通问答助手。

2. 产品形态  
   我们做网页版交互, 用户在网页输入研究问题, 系统展示多智能体协同过程和最终研究计划。

3. 技术核心  
   后端使用 LangGraph 编排多智能体, 每个 Agent 产出结构化结果, 进入 Result Pool。

4. 工具增强  
   文献检索、PDF 解析、引用校验、数据集画像、图表生成、实验执行都通过 Tool 完成。

5. 三人分工  
   杨旭管架构、集成和材料; 冯佳乐管后端 Agent 和工具; 杜灿管网页端、CV 数据画像和实验展示。

6. 时间节点  
   7 月 13 日前跑通 mock 网页闭环; 8 月中旬跑通完整真实流程; 9 月 5 日前冻结提交版; 9 月 10 日前完善答辩版。

7. 本周任务  
   仓库协作、项目骨架、FastAPI + Streamlit 联通、LangGraph mock workflow、Qwen API demo。

8. 验收方式  
   每周必须有可运行页面和可展示中间结果, 不以“代码差不多写了”作为完成标准。
