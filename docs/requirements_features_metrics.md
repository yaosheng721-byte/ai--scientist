# CV AI Scientist 需求、功能与指标文档

版本: v0.1  
日期: 2026-07-06  
产品形态: 网页端 AI Scientist 系统  
核心技术: Qwen/百炼 + LangChain + LangGraph + Tool 工具增强

## 1. 项目定位

本项目要做一个面向计算机视觉研究场景的 AI Scientist 网页系统。用户输入一个 CV 研究问题和数据集信息后, 系统通过多智能体协作完成文献检索、事实抽取、数据集画像、知识缺口识别、候选假设生成、审稿评分、实验设计、工具验证和报告生成。

一句话定位:

> 一个能够把 CV 科研问题转化为可验证研究假设和实验计划的多智能体科研助手。

本项目不是:

- 普通聊天机器人。
- 普通论文总结工具。
- 只生成 idea 的文本系统。
- 只套一个大模型 API 的演示项目。

本项目必须体现:

- 多智能体协同。
- 工具增强。
- 真实文献和真实引用。
- 视觉数据集分析。
- 可验证实验计划。
- 网页端可交互展示。

## 2. 目标用户

主要用户:

- 参赛团队成员。
- 计算机视觉方向学生。
- 想寻找 CV 论文选题或实验方向的科研初学者。

评审视角用户:

- 科学专家: 关注假设是否有科学价值、是否自洽、是否可验证。
- 技术专家: 关注多智能体设计、工具调用、数据处理、代码复现。
- 应用专家: 关注系统是否能支撑真实场景、是否有成果转化潜力。

## 3. 核心使用场景

### 场景 1: 从研究问题生成候选假设

用户输入:

```text
工业缺陷检测中小缺陷区域定位不稳定, 是否可以通过显式建模缺陷尺度先验来提升定位性能?
```

系统输出:

- 相关论文列表。
- 论文事实。
- 数据集画像。
- 知识缺口。
- 多个候选假设。
- 每个假设的审稿评分。

### 场景 2: 从数据集画像发现研究缺口

用户上传或指定数据集路径后, 系统自动分析:

- 类别分布。
- 图片尺寸。
- 目标/缺陷面积比例。
- 小目标或小缺陷比例。
- 图像质量。
- 样例图。

系统根据数据观察生成潜在研究缺口。

### 场景 3: 对候选假设进行审稿式评估

系统生成多个候选假设后, Reviewer Agents 从以下维度打分:

- 创新性。
- 可行性。
- 证据充分性。
- 可复现性。

用户可以在网页上选择一个假设进入实验设计。

### 场景 4: 生成最终研究计划

系统最终输出标准化《科学假设与研究计划》:

- 待研究问题。
- 解决思路。
- 技术细节。
- 数据集。
- 实验设计。
- 预期或初步结果。
- 真实参考文献。

## 4. 功能总览

| 模块 | 功能 | 优先级 | 负责人 |
| --- | --- | --- | --- |
| 网页端任务创建 | 输入研究问题、选择领域、上传/指定数据集 | P0 | 杜灿 |
| 工作流状态展示 | 展示当前 Agent、运行状态、日志 | P0 | 杜灿 |
| LangGraph 编排 | 多智能体节点、条件边、循环 | P0 | 杨旭 |
| Qwen/百炼接入 | 模型调用、结构化输出 | P0 | 杨旭 |
| 文献检索 | 检索真实论文 | P0 | 冯佳乐 |
| PDF/事实抽取 | 从论文抽取结构化事实 | P0 | 冯佳乐 |
| 引用校验 | 校验 DOI、URL、arXiv ID | P0 | 冯佳乐 |
| 数据集画像 | CV 数据统计和图表 | P0 | 杜灿 |
| PostgreSQL 持久化 | 保存 runs、result pools、tool calls、文献关系边 | P0 | 杨旭 |
| Redis 记忆与 RAG | 保存上下文记忆、检索缓存、短期状态和 RAG 缓存 | P0 | 杨旭 |
| Graph Agent | 生成和查询文献之间的关系图 | P0 | 杨旭 + 冯佳乐 |
| 证据融合 | 融合文献事实和数据画像 | P0 | 冯佳乐 + 杨旭 |
| 假设生成 | 多 Agent 生成候选假设 | P0 | 杨旭 |
| 审稿评分 | 多 Reviewer Agent 打分 | P0 | 杨旭 + 冯佳乐 |
| 人工反馈 | 人类选择/驳回候选假设 | P0 | 杜灿 |
| 实验设计 | 生成 baseline、metrics、ablation | P0 | 杨旭 |
| 工具执行 | 跑数据统计、轻量实验、生成图表 | P1 | 杜灿 + 杨旭 |
| 报告生成 | Markdown/PDF/HTML 报告 | P0 | 杨旭 + 杜灿 |
| 演示视频素材 | 运行截图、流程讲解 | P1 | 杨旭 + 杜灿 |
| React 正式前端 | 更精致的前端 UI | P2 | 视时间决定 |

优先级说明:

- P0: 比赛提交必须完成。
- P1: 强加分项, 尽量完成。
- P2: 有时间再做。

## 5. 功能需求详情

### 5.1 任务创建功能

用户可以在网页端创建研究任务。

输入字段:

- 研究问题。
- CV 领域: 工业缺陷、遥感、医学影像、通用 CV。
- 任务类型: classification、detection、segmentation、anomaly_detection、change_detection。
- 数据集路径或上传文件。
- 可选论文 PDF。
- 最大迭代次数。
- 模型选择。

输出:

- `run_id`
- 当前任务状态。
- 进入任务详情页。

验收:

- 输入合法时能创建任务。
- 输入缺失时有明确提示。
- 创建任务后网页能看到 `run_id` 和初始状态。

### 5.2 工作流状态展示

网页需要展示多智能体运行过程。

展示内容:

- 当前运行节点。
- 每个节点状态: pending、running、success、failed。
- 迭代次数。
- Result Pool 数量。
- 工具调用日志。
- 错误信息。

验收:

- 至少展示 8 个 Agent/Node。
- 节点状态能随运行变化。
- 出错时能展示错误信息, 不直接页面崩溃。

### 5.3 文献检索功能

系统根据研究问题检索真实论文。

输入:

- query。
- keywords。
- domain。
- max_results。

输出:

- Paper Pool。

每篇论文至少包含:

- title。
- authors。
- year。
- venue 或 source。
- url、doi 或 arxiv_id。
- relevance_score。

验收:

- 单次任务至少返回 10 篇相关论文。
- 至少 80% 论文有 URL、DOI 或 arXiv ID。
- 前端能展示论文列表。

### 5.4 论文事实抽取功能

系统从论文中抽取事实。

事实字段:

- fact_id。
- claim。
- evidence_text。
- source_paper_id。
- section。
- page 或 source_location。
- confidence。

验收:

- 单次任务至少抽取 20 条事实。
- 每条事实必须绑定论文来源。
- 不允许输出没有来源的关键结论。

### 5.5 引用真实性校验

系统必须避免虚构参考文献。

规则:

- References 只能来自 Paper Pool。
- Report Writer 不能新造论文标题、作者、DOI。
- DOI、URL、arXiv ID 至少存在一个。

验收:

- 最终报告中的每篇参考文献都能追溯到 Paper Pool。
- 虚构引用数量必须为 0。

### 5.6 数据集画像功能

系统对 CV 数据集做自动统计。

基础统计:

- 图片总数。
- train/test/val 数量。
- 图片尺寸分布。
- 文件格式分布。
- 类别分布。

检测/分割任务统计:

- bbox 数量。
- bbox 面积分布。
- 小目标比例。
- mask 面积分布。
- 类别不均衡情况。

异常检测任务统计:

- normal/abnormal 数量。
- 缺陷区域面积比例。
- 缺陷类别分布。
- texture/object 类别差异。

图像质量统计:

- 模糊分数。
- 亮度分布。
- 对比度。
- 噪声估计。

输出:

- `dataset_profile.json`
- 统计图表。
- 样例图。
- 数据观察结论。

验收:

- 至少生成 3 张统计图。
- 至少生成 5 条数据观察。
- 结果能在网页端展示。

### 5.7 PostgreSQL 持久化功能

系统使用 PostgreSQL 保存长期数据。

需要保存:

- `runs`: 每次研究任务的基本信息、状态、当前节点和迭代次数。
- `result_items`: Paper Pool、Fact Pool、Gap Pool、Hypothesis Pool、Review Pool。
- `tool_calls`: 工具调用输入、输出、日志、错误和退出码。
- `literature_edges`: Graph Agent 生成的论文关系边。

验收:

- 创建任务后能写入 `runs`。
- Agent/Tool 的关键输出能写入 `result_items`。
- 工具调用日志能写入 `tool_calls`。
- Graph Agent 生成的关系能写入 `literature_edges`。

### 5.8 Redis 上下文记忆与 RAG 功能

系统使用 Redis 作为短期记忆和 RAG 缓存层。

用途:

- 保存 run 的当前上下文和最近 Agent 输出。
- 缓存文献检索结果。
- 缓存论文 chunk 和 RAG 检索结果。
- 保存前端轮询需要的任务状态。
- 后续使用 Redis Stack 扩展轻量向量检索。

验收:

- 能按 `run_id` 写入和读取上下文 JSON。
- 能缓存一次文献检索结果。
- 前端查询任务状态时可以优先读取 Redis 状态。

### 5.9 Graph Agent 文献关系图功能

Graph Agent 用于分析论文之间的关系, 帮助系统从“论文列表”升级为“论文知识网络”。

关系类型:

- shared_dataset: 使用相同数据集。
- shared_task: 研究相同视觉任务。
- method_lineage: 方法继承或改进关系。
- citation: 引用关系。
- shared_keyword: 关键词相似。
- semantic_similarity: 语义相似。

输出字段:

- nodes: 论文节点。
- edges: 论文之间的关系边。
- summary: 论文数量、关系数量、核心论文。

验收:

- 输入 Paper Pool 后能生成文献关系图。
- 每条关系边包含 source、target、relation_type、evidence、weight。
- 关系图结果能被 Evidence Board 和 Gap Discovery 使用。

### 5.10 Evidence Board 功能

Evidence Board 用来融合文献事实和数据观察。

字段:

- known_facts。
- dataset_observations。
- contradictions。
- under_explored_factors。
- transferable_methods。

验收:

- 至少包含 10 条文献事实。
- 至少包含 5 条数据观察。
- 至少输出 3 个潜在研究缺口线索。

### 5.11 知识缺口发现功能

系统根据 Evidence Board 发现研究 gap。

每个 gap 包含:

- gap_id。
- description。
- supporting_facts。
- supporting_dataset_observations。
- research_value。
- testability。

验收:

- 至少生成 3 个 gap。
- 每个 gap 至少绑定 1 条文献事实或 1 条数据观察。
- gap 不能只是泛泛而谈, 必须和 CV 场景相关。

### 5.12 候选假设生成功能

系统由多个 Hypothesis Agents 并行生成候选假设。

Agent 类型:

- 文献驱动假设 Agent。
- 数据驱动假设 Agent。
- 跨领域迁移假设 Agent。
- 模型结构创新 Agent。

每个假设字段:

- hypothesis_id。
- source_agent。
- hypothesis。
- mechanism。
- expected_effect。
- required_data。
- test_method。
- supporting_evidence。
- risks。

验收:

- 至少生成 6 个候选假设。
- 每个假设必须有机制解释。
- 每个假设必须有验证方法。
- 每个假设必须有风险说明。

### 5.13 审稿评分功能

系统通过多个 Reviewer Agents 对假设评分。

评分维度:

- novelty_score: 创新性。
- feasibility_score: 可行性。
- evidence_score: 证据充分性。
- reproducibility_score: 可复现性。

总分公式:

```text
final_score =
  0.30 * novelty_score +
  0.25 * feasibility_score +
  0.25 * evidence_score +
  0.20 * reproducibility_score
```

通过条件:

- final_score >= 80。
- evidence_score >= 75。
- feasibility_score >= 70。

验收:

- 每个候选假设都有四项评分和总分。
- 每个低分项必须给出原因。
- 分数不足时触发回退或人工 review。

### 5.14 人工反馈功能

用户可以在网页端参与选择和修正。

功能:

- 查看候选假设详情。
- 查看评分和审稿意见。
- 选择一个假设进入实验设计。
- 驳回全部假设并要求重新生成。
- 输入人工修改意见。

验收:

- 人工选择后后端能继续执行下一节点。
- 人工驳回后系统能回到假设生成或 gap 发现。

### 5.15 实验设计功能

系统将选中假设转为实验计划。

字段:

- baseline。
- proposed_method。
- dataset。
- metrics。
- ablation。
- training_or_validation_plan。
- expected_result。
- risk_control。

验收:

- 至少给出 1 个 baseline。
- 至少给出 3 个 metrics。
- 至少给出 2 个 ablation。
- 实验计划必须能在当前时间和算力条件下小规模验证。

### 5.16 工具执行功能

系统调用真实工具执行外部功能。

工具类型:

- 文献检索工具。
- PDF 解析工具。
- 数据集画像工具。
- 图表生成工具。
- 指标计算工具。
- 轻量 baseline 或 demo 实验工具。

验收:

- 至少接入 5 类工具。
- 每次工具调用记录 input、output、status、log。
- 至少有一个真实 artifact, 如图表、json、日志或指标文件。

### 5.17 报告生成功能

最终报告必须符合比赛要求。

报告字段:

- Problem Statement。
- Rationale。
- Technical Details。
- Datasets。
- Source。
- Target。
- Paper Title。
- Paper Abstract。
- Methods。
- Experiments。
- Results。
- References。

验收:

- 报告字段完整。
- References 真实可查。
- Results 区分 executed_result、pilot_result、expected_result。
- 网页端可以预览并导出。

## 6. 非功能需求

### 6.1 可复现性

要求:

- 代码有 README。
- 环境变量有 `.env.example`。
- 关键实验有运行命令。
- 工具输出保存到 `outputs/`。

指标:

- 新成员按 README 能在 30 分钟内启动网页 demo。
- 同一个 mock run 可以稳定复现。

### 6.2 稳定性

要求:

- Agent 输出 JSON 解析失败时能重试。
- 工具调用失败时能返回错误状态。
- 前端不因单个节点失败而崩溃。

指标:

- Mock 流程成功率 >= 95%。
- 真实 demo 流程成功率 >= 80%。

### 6.3 安全性

要求:

- API Key 不进仓库。
- `.env` 不提交。
- 用户上传文件限制类型和大小。
- 工具执行路径受控。

指标:

- 仓库中真实 API Key 数量为 0。
- `.gitignore` 覆盖 `.env`、outputs、data/raw。

### 6.4 展示性

要求:

- 评委能在网页上看懂多智能体流程。
- 关键中间结果可视化。
- 最终报告可导出。

指标:

- 页面至少包含 5 个核心视图。
- 每个核心模块有可展示结果。

## 7. 关键验收指标

### 7.1 比赛评分对齐指标

| 评分方向 | 比赛分值 | 项目对应指标 |
| --- | --- | --- |
| 科学价值 | 40 | 假设创新性、自洽性、可落地验证性 |
| 技术深度 | 30 | 多智能体编排、工具增强、CV 数据处理、模型调用 |
| 应用潜力 | 30 | 真实场景支撑、复现性、报告质量、demo 展示 |

### 7.2 产品完成度指标

| 指标 | 最低要求 | 目标要求 |
| --- | --- | --- |
| 网页核心页面数 | 5 个 | 7 个以上 |
| Agent/Node 数量 | 8 个 | 12 个以上 |
| 工具类别数量 | 5 类 | 8 类以上 |
| 候选假设数量 | 6 个 | 8 个以上 |
| Reviewer 类型 | 4 类 | 4 类以上 |
| 数据画像图表 | 3 张 | 5 张以上 |
| PostgreSQL 核心表 | 4 张 | 4 张以上 |
| Redis 记忆读写 | 1 类上下文 | 上下文 + RAG 缓存 |
| Graph Agent 关系类型 | 3 类 | 6 类以上 |
| 真实论文数量 | 10 篇 | 20 篇以上 |
| 结构化事实数量 | 20 条 | 50 条以上 |
| 审稿迭代次数 | 1 轮 | 2-3 轮 |
| 最终报告字段完整率 | 100% | 100% |

### 7.3 文献和引用指标

| 指标 | 要求 |
| --- | --- |
| 虚构引用数 | 0 |
| 参考文献可追溯率 | 100% |
| 论文元数据完整率 | >= 80% |
| 每个关键结论来源绑定 | >= 90% |

### 7.4 假设质量指标

| 指标 | 要求 |
| --- | --- |
| final_score | >= 80 |
| evidence_score | >= 75 |
| feasibility_score | >= 70 |
| 每个假设有机制解释 | 100% |
| 每个假设有验证方法 | 100% |
| 每个假设有风险说明 | 100% |

### 7.5 CV 数据分析指标

| 指标 | 最低要求 |
| --- | --- |
| 数据集基础统计 | 必须完成 |
| 类别/样本分布图 | 必须完成 |
| 图像尺寸分布图 | 必须完成 |
| 小目标/缺陷面积统计 | 必须完成 |
| 图像质量统计 | 尽量完成 |
| 样例图展示 | 必须完成 |

### 7.6 工具执行指标

| 指标 | 要求 |
| --- | --- |
| 工具调用日志保存率 | 100% |
| 工具失败可见性 | 100% |
| artifact 路径记录 | 100% |
| 至少一个真实执行结果 | 必须完成 |

### 7.7 前端展示指标

| 页面 | 必须展示 |
| --- | --- |
| 任务创建页 | 研究问题、领域、任务类型、数据集 |
| 工作流页 | Agent 节点状态、运行日志 |
| Result Pool 页 | Paper/Fact/Gap/Hypothesis/Review |
| 假设评审页 | 候选假设、评分、人工选择 |
| 数据画像页 | 统计图、样例图、数据观察 |
| 实验结果页 | 指标、日志、artifact |
| 报告页 | Markdown 预览、导出 |

## 8. MVP 范围

MVP 必须完成:

- 网页创建任务。
- LangGraph 多智能体 mock 到真实流程。
- Qwen/百炼模型调用。
- 文献检索和事实抽取。
- 数据集画像。
- 候选假设生成。
- 审稿评分。
- 人工选择假设。
- 实验设计。
- 至少一个工具真实执行结果。
- 最终报告预览和导出。

MVP 可以暂时不做:

- 完整大规模模型训练。
- 多用户权限系统。
- 复杂后台任务队列。
- 精致 React 前端。
- 云端部署。

## 9. 第一版 Demo 验收流程

2026-07-13 前的第一版 Demo 只要求 mock 闭环:

```text
打开网页
  -> 输入研究问题
  -> 创建 run
  -> 后端运行 mock LangGraph
  -> 页面显示 Agent 状态
  -> 页面显示 mock 候选假设
  -> 人工选择一个假设
  -> 生成 mock 报告
```

第一版 Demo 通过后, 再逐步替换真实工具:

```text
mock paper -> 真实文献检索
mock fact -> 真实 PDF/摘要事实抽取
mock dataset profile -> 真实 OpenCV 数据画像
mock hypothesis -> 真实 Qwen 多 Agent 生成
mock result -> 真实工具执行结果
```

## 10. 最终提交验收清单

2026-09-05 前必须检查:

- 技术方案 PDF 不超过比赛要求页数。
- 源代码可运行。
- README 写清楚环境配置和启动方式。
- `.env.example` 存在, 真实 `.env` 未提交。
- 百炼/Qwen 调用截图准备好。
- 网页 demo 可录屏。
- 至少一个完整案例可复现。
- 参考文献真实可查。
- 最终报告字段完整。
- 演示视频不超过 10 分钟。
- 压缩包、报名表、网盘链接和截图准备好。
