# CV AI Scientist 团队分工与开发计划

版本: v0.1  
日期: 2026-07-06  
开发周期: 2026-07-07 到 2026-09-10  
比赛提交冻结时间: 2026-09-05 前  
团队成员: 杨旭、冯佳乐、杜灿

## 1. 项目管理原则

本项目按网页版优先开发, 目标是在网页端展示一个可交互的 CV AI Scientist 系统。网页只是交互入口, 核心能力在后端:

```text
前端网页
  -> FastAPI 后端
  -> LangGraph 多智能体工作流
  -> Tool 工具系统
  -> Result Pool 中间结果池
  -> 最终科学假设与研究计划
```

团队开发时要坚持三个原则:

1. 先跑通闭环, 再增强真实能力。
2. 每周必须有可演示页面, 不只汇报代码进度。
3. 任何 Agent 输出都要结构化保存, 方便前端展示和最终报告引用。
4. 每个人尽量负责一条端到端链路, 包括 Agent、Tool、API 和页面展示, 避免小团队被前后端边界拖慢。

## 2. 成员职责

三人团队不要按纯前端/纯后端切分。更合理的方式是按“端到端功能链”切分: 每个人都负责自己模块的 Agent、Tool、API 和网页展示。这样减少接口等待, 也能保证每个人都理解完整系统。

| 成员 | 角色 | 主要职责 | 关键交付 |
| --- | --- | --- | --- |
| 杨旭 | 总架构 + 科研推理链 | LangGraph 主流程、Supervisor、Result Pool、假设审稿聚合、实验设计、报告生成、项目管理 | 主工作流、评审聚合、最终报告、技术方案 |
| 冯佳乐 | 文献证据链 | 文献检索、PDF 解析、事实抽取、引用校验、Evidence Board、对应网页展示 | Paper Pool、Fact Pool、Evidence Board、引用校验 |
| 杜灿 | 视觉数据与实验链 | 网页框架、CV 数据集画像、图表工具、实验工具、结果展示、人工反馈页面 | Web Demo、Dataset Profile、实验图表、Human Review |

## 3. 杨旭任务

杨旭既负责项目统筹, 也负责核心 Agent 和关键链路开发。重点是把多智能体系统搭起来, 并负责最终假设选择、实验设计和报告生成。

具体任务:

- 确定最终 CV 细分方向和数据集。
- 维护项目文档、任务列表和开发节奏。
- 设计整体架构: FastAPI、LangGraph、Agent、Tool、Result Pool。
- 设计 PostgreSQL + Redis 数据层, PostgreSQL 保存长期数据, Redis 保存上下文记忆和 RAG 缓存。
- 实现 LangGraph 主流程、Supervisor Agent 和条件路由。
- 实现假设聚合、审稿路由、实验设计和报告生成相关 Agent。
- 实现 Graph Agent 初版, 用于生成论文之间的关系图。
- 实现最终报告导出相关 Tool 或接口。
- 管理 Gitee 仓库、分支、合并和代码 Review。
- 维护 `.env.example`、README、运行说明。
- 每周组织一次联调验收。
- 最终负责技术方案 PDF、演示视频脚本、答辩讲稿。

重点关注文件:

```text
README.md
docs/
app/core/config.py
app/graph/state.py
app/graph/build_graph.py
app/api/
```

阶段性交付:

| 时间 | 交付 |
| --- | --- |
| 2026-07-13 前 | 项目骨架、接口规范、Mock 闭环验收 |
| 2026-07-27 前 | 多智能体核心流程验收 |
| 2026-08-10 前 | 审稿聚合、实验设计、前后端联调验收 |
| 2026-08-24 前 | 完整真实案例验收 |
| 2026-09-05 前 | 比赛提交版冻结 |
| 2026-09-10 前 | 答辩展示版完善 |

## 4. 冯佳乐任务

冯佳乐负责文献证据链, 从真实论文进入系统开始, 到形成可被假设生成使用的 Evidence Board。该模块也需要提供对应 API 和基础网页展示支持。

核心任务:

- 实现文献检索工具。
- 实现 PDF/摘要读取。
- 实现事实抽取 Agent。
- 实现引用真实性校验工具。
- 实现 Evidence Integrator Agent。
- 将 Paper Pool、Fact Pool、Evidence Board 写入 Result Pool。
- 提供文献证据链 API。
- 协助前端展示论文、事实和证据板。

需要实现的 Agent:

- Literature Search Agent
- Paper Reader Agent
- Fact Extractor Agent
- Evidence Integrator Agent
- Evidence Reviewer Agent
- Citation Verification Agent

需要实现的工具:

- arXiv/Semantic Scholar 检索工具
- PDF 解析工具
- DOI/URL 引用校验工具
- 向量检索工具

验收标准:

- 输入一个研究问题, 能生成 Paper Pool、Fact Pool 和 Evidence Board。
- 每条关键事实必须能追溯到论文来源。
- References 只能来自真实检索结果。
- 前端能展示论文列表、事实列表和证据板摘要。

## 5. 杜灿任务

杜灿负责视觉数据与实验链, 从网页交互开始, 到数据集画像、工具执行、实验结果展示和人工反馈。该模块不只是前端, 也包含 CV Tool 和部分实验 Tool。

前端页面任务:

- 任务创建页
- 工作流状态页
- Result Pool 展示页
- 候选假设评分页
- 人工选择/驳回假设交互
- 数据集画像页
- 实验结果页
- 报告预览和导出页

CV 数据工具任务:

- 数据集目录扫描。
- 图片数量、尺寸、格式统计。
- 类别分布统计。
- 目标框/缺陷区域面积统计。
- 小目标比例或小缺陷比例统计。
- 模糊、亮度、噪声等图像质量统计。
- 样例图和统计图生成。

实验展示任务:

- baseline 指标展示。
- 小规模实验日志展示。
- 图表 artifact 管理。
- 最终报告中插入关键图表。

需要实现的 Agent/Tool:

- Dataset Profiling Agent。
- Dataset Scan Tool。
- Image Quality Tool。
- Plot Generator Tool。
- Tool Execution 页面和日志展示。
- Human Review 交互节点。

验收标准:

- 用户可以通过网页创建任务并查看运行状态。
- 页面能展示 Agent 节点、Result Pool、候选假设、评分和图表。
- Human Review 节点可以人工选择一个假设继续流程。
- 页面能预览和导出最终报告。

## 6. 细分任务清单

本节可以直接作为 Gitee issue 的来源。建议每条任务单独建 issue, 标题格式为:

```text
[负责人][任务编号] 任务名称
```

示例:

```text
[杨旭][YA-01] 实现 ScientistState 数据结构
[冯佳乐][FJL-01] 实现 Literature Search Tool
[杜灿][DC-02] 实现任务创建页面
```

### 6.1 杨旭任务细分

| 编号 | 任务 | 交付物 | 验收标准 |
| --- | --- | --- | --- |
| PM-01 | 确定最终 CV 场景 | 选题说明文档 | 在工业缺陷检测/遥感小目标检测中确定一个 MVP 场景 |
| PM-02 | 确定 MVP 数据集 | 数据集选择说明 | 写清楚数据集来源、任务类型、使用方式和风险 |
| PM-03 | 建立仓库目录规范 | README + 目录结构 | 冯佳乐、杜灿能按目录找到各自模块 |
| PM-04 | 维护 `.env.example` | `.env.example` | 包含 DASHSCOPE_API_KEY、模型名、数据库、输出目录 |
| PM-05 | 制定接口字段规范 | API 字段说明 | 前后端对 `run_id`、`status`、`result_pool` 字段理解一致 |
| PM-06 | 设计 Result Pool 数据结构 | Result Pool schema | Paper/Fact/Gap/Hypothesis/Review/Artifact 都有统一字段 |
| PM-07 | 设计 Agent 输出 JSON schema | schemas 文档 | 每个 Agent 输出字段明确, 支持前端展示 |
| PM-08 | 设计 PostgreSQL 表结构 | SQL/ER 说明 | 包含 runs、result_items、tool_calls、literature_edges |
| PM-09 | 设计 Redis Key 规范 | Redis key 文档 | 覆盖上下文记忆、RAG 缓存、任务状态 |
| YA-01 | 实现 `ScientistState` | `app/graph/state.py` | 包含 query、paper_pool、dataset_profile、hypothesis_pool、review_pool 等字段 |
| YA-02 | 搭建 LangGraph 主流程 | `app/graph/build_graph.py` | mock 数据能从 START 跑到 END |
| YA-03 | 实现 Supervisor Agent | supervisor node | 能根据状态判断下一步节点 |
| YA-04 | 实现条件路由 | routing module | 根据评分进入实验设计、重新生成或人工审核 |
| YA-05 | 实现 run 状态保存 | run repository | 保存 run_id、status、current_node、iteration |
| YA-06 | 封装 Qwen/百炼模型调用 | model client | 支持模型名配置、错误处理、结构化输出 |
| YA-07 | 实现 Problem Parser Agent | parser node | 输入研究问题, 输出 domain、task_type、constraints |
| YA-08 | 实现 PostgreSQL 连接 | db client | 能连接数据库并写入 mock run |
| YA-09 | 实现 Redis Memory Store | redis memory | 能按 run_id 读写上下文 JSON |
| YA-10 | 实现 Graph Agent 初版 | literature_graph | 能基于 Paper Pool 生成 nodes/edges |
| YA-11 | 实现 Gap Discovery Agent | gap_pool | 至少生成 3 个有证据支撑的 gap |
| YA-12 | 实现 4 个 Hypothesis Agents | hypothesis_pool | 至少生成 6 个候选假设 |
| YA-13 | 实现 Novelty/Feasibility Reviewer | review_pool | 每个假设有创新性和可行性评分 |
| YA-14 | 实现 Aggregation Agent | selected_hypothesis | 能选出 Top-1 或融合 Top-2 假设 |
| YA-15 | 实现 Experiment Designer Agent | experiment_plan | 输出 baseline、metrics、ablation、risk_control |
| YA-16 | 实现 Report Writer Agent | final_report | 输出赛题要求的完整报告字段 |
| YA-17 | 制定评分规则 | review rubric | novelty、feasibility、evidence、reproducibility 评分规则明确 |
| YA-18 | 每周代码 Review 和集成 | Review 记录 | 每周都有可演示页面和明确问题清单 |
| YA-19 | 技术方案 PDF 和演示脚本 | PDF 大纲 + demo script | 10 分钟内能讲清系统价值和完整流程 |
| YA-20 | 百炼调用证据整理 | 截图/调用说明 | 准备模型调用截图、API 配置说明 |
| YA-21 | 最终提交材料检查 | 提交清单 | 9 月 5 日前确认源码、文档、视频、截图齐全 |

### 6.2 冯佳乐任务细分

| 编号 | 任务 | 交付物 | 验收标准 |
| --- | --- | --- | --- |
| FJL-01 | 实现 Literature Search Tool | literature tool | 能按 query 返回至少 10 篇论文元数据 |
| FJL-02 | 实现 Semantic Scholar/arXiv 适配 | search adapters | 至少接入一个真实文献源 |
| FJL-03 | 实现 Paper Reader | paper reader | 能读取 PDF/摘要文本并返回章节内容 |
| FJL-04 | 实现 Fact Extractor Agent | fact extractor | 至少抽取 20 条带来源 fact |
| FJL-05 | 实现 Citation Verifier | citation tool | DOI/URL/arXiv ID 至少校验一种 |
| FJL-06 | 实现 Evidence Integrator Agent | evidence board | 能融合 fact_pool 和 dataset_profile |
| FJL-07 | 实现 Evidence Reviewer Agent | evidence review | 能指出假设缺少哪些证据 |
| FJL-08 | 为 Graph Agent 补充文献关系字段 | paper metadata | paper 中包含 datasets、tasks、keywords、citations |
| FJL-09 | 实现文献向量检索 | vector retriever | 能按 query 找到相关 chunk |
| FJL-10 | 实现 Paper Pool API | API endpoint | 前端能查询论文列表 |
| FJL-11 | 实现 Fact Pool API | API endpoint | 前端能查询事实列表 |
| FJL-12 | 实现 Evidence Board API | API endpoint | 前端能查询证据板摘要 |
| FJL-13 | 实现引用约束逻辑 | reference guard | Report Writer 只能使用 Paper Pool 引用 |
| FJL-14 | 文献链网页展示协助 | frontend component/API demo | 能展示 Paper/Fact/Evidence 三类结果 |
| FJL-15 | 文献链测试 | tests | 覆盖文献检索、fact schema、citation check |
| FJL-16 | 文献链演示素材 | screenshots/logs | 准备文献检索和引用校验截图 |

### 6.3 杜灿任务细分

| 编号 | 任务 | 交付物 | 验收标准 |
| --- | --- | --- | --- |
| DC-01 | 搭建 Streamlit 项目入口 | `frontend/streamlit_app.py` | 能启动网页首页 |
| DC-02 | 实现任务创建页 | create run page | 能输入研究问题、领域、任务类型、数据集路径 |
| DC-03 | 接入创建任务接口 | API client | 点击按钮后能拿到 `run_id` |
| DC-04 | 实现工作流状态页 | workflow page | 显示 Agent 节点、状态、当前节点 |
| DC-05 | 实现 Result Pool 页面 | result pool page | 展示 Paper/Fact/Gap/Hypothesis/Review 分类结果 |
| DC-06 | 实现候选假设表格和详情 | hypothesis UI | 展示假设、评分、风险、证据、验证方法 |
| DC-07 | 实现人工选择/驳回 | human review UI | 可以 approve/reject 并提交给后端 |
| DC-08 | 实现 Dataset Profiling Agent | dataset profile node | 能把数据集统计写入 state |
| DC-09 | 实现数据集扫描工具 | dataset_scan | 输出图片数量、目录结构、格式分布 |
| DC-10 | 实现图像尺寸统计 | image size stats | 输出尺寸分布图 |
| DC-11 | 实现类别/缺陷分布统计 | class/defect stats | 输出类别或缺陷分布图 |
| DC-12 | 实现目标/缺陷面积统计 | area stats | 输出小目标/小缺陷比例 |
| DC-13 | 实现图像质量统计 | quality stats | 输出模糊、亮度、对比度等统计 |
| DC-14 | 实现样例图可视化 | sample grid | 页面能展示样例图或标注图 |
| DC-15 | 实现 Tool Execution 日志页 | tool logs page | 能展示工具调用 input、output、status、error |
| DC-16 | 实现实验结果页面 | experiment page | 展示 metrics、artifact、日志 |
| DC-17 | 实现 Plot Generator Tool | plot tool | 能从 json/csv 生成统计图 |
| DC-18 | 实现报告预览页 | report page | Markdown 报告可读、字段完整 |
| DC-19 | 实现报告导出 | export button | 能导出 Markdown/HTML/PDF 中至少一种 |
| DC-20 | 前端异常处理和演示美化 | error states + demo polish | 关键页面适合录屏展示 |

### 6.4 第一周每日任务细分

第一周目标是先跑通 mock 网页闭环, 不追求真实科研能力。

| 日期 | 杨旭 | 冯佳乐 | 杜灿 | 当日验收 |
| --- | --- | --- | --- | --- |
| 07-07 | 建仓库规范、确认选题、定义 `ScientistState` 草稿、初始化 Postgres/Redis 配置 | 初始化文献链目录和 mock Paper Pool | 初始化 Streamlit、做首页草稿 | 三人能 clone 并运行空项目 |
| 07-08 | 搭建 mock graph: parse -> graph_agent -> report | 实现 mock 文献检索 Tool | 实现任务创建表单 | 页面能提交表单并打印输入 |
| 07-09 | 定义 Result Pool schema 和 run 状态 | 实现 mock Fact Pool 返回 | 接入创建任务接口 | 创建任务后页面显示 run_id |
| 07-10 | 实现 Supervisor/route mock 和 Graph Agent mock | 实现 mock Evidence Board | 实现工作流状态页 | 页面能显示 Agent 节点状态 |
| 07-11 | 实现 mock hypothesis/review/report | 实现 Paper/Fact API mock | 实现候选假设表格 | 页面能展示 mock 假设和评分 |
| 07-12 | 支持人工选择后进入 mock report | 协助联调文献结果展示 | 实现人工选择按钮和结果页 | 能从输入跑到 mock report |
| 07-13 | 周验收和下周计划 | 修复后端问题 | 修复前端问题 | 第一周 mock 闭环通过 |

### 6.5 第二到四周任务细分

| 周期 | 杨旭 | 冯佳乐 | 杜灿 | 验收重点 |
| --- | --- | --- | --- | --- |
| 第 2 周 | Problem Parser、模型调用封装、PostgreSQL/Redis 读写、主流程接入真实数据 | 文献检索、PDF 读取、Fact 抽取、引用校验 | Dataset Profiler、Paper Pool 展示、数据画像页 | 真实论文 + 真实数据画像 + 数据库可写 |
| 第 3 周 | Gap Discovery、4 个 Hypothesis Agents、假设 schema | Evidence Board、Evidence Reviewer、文献证据补强 | Gap/Hypothesis 页面和详情展示 | 至少 6 个有证据假设 |
| 第 4 周 | Novelty/Feasibility Reviewer、Aggregation、条件回退 | Evidence Reviewer、引用约束、文献链测试 | 评分展示、人工选择/驳回交互 | 审稿-回退-人工选择闭环 |

### 6.6 第五到八周任务细分

| 周期 | 杨旭 | 冯佳乐 | 杜灿 | 验收重点 |
| --- | --- | --- | --- | --- |
| 第 5 周 | Experiment Designer、最小实验范围、报告结构 | 文献链稳定性、工具执行协助 | 实验工具、日志页、artifact 展示 | 至少一个真实工具执行结果 |
| 第 6 周 | Report Writer、完整流程验收、报告字段 | 引用约束、References 真实校验 | 报告预览和导出 | 网页到最终报告闭环 |
| 第 7 周 | 技术方案 PDF 初稿、演示脚本、系统集成 | 后端稳定性、文献链测试、引用截图 | 页面美化、图表优化 | 完整真实案例可演示 |
| 第 8 周 | 提交材料、视频脚本、截图清单 | 修关键 bug、冻结文献链 API | 录屏页面打磨、导出稳定 | 提交材料初版齐全 |

### 6.7 模块依赖关系

开发时按以下依赖推进:

```text
接口字段规范
  -> LangGraph mock workflow
  -> 前端 mock 展示
  -> 文献工具 / 数据工具
  -> Evidence Board
  -> Hypothesis Pool
  -> Review Pool
  -> Human Review
  -> Experiment Plan
  -> Tool Execution
  -> Final Report
```

容易阻塞的接口:

| 接口/数据 | 上游 | 下游 | 必须尽早确定 |
| --- | --- | --- | --- |
| `ScientistState` | 杨旭 | 所有人 | 是 |
| `run status` | 杨旭 | 杜灿 | 是 |
| `Result Pool item` | 杨旭 + 冯佳乐 + 杜灿 | 所有人 | 是 |
| `paper_pool/fact_pool` | 冯佳乐 | 杨旭 + 杜灿 | 是 |
| `dataset_profile` | 杜灿 | 杨旭 + 冯佳乐 | 是 |
| `selected_hypothesis` | 杨旭 + 杜灿 | 杨旭 | 是 |
| `final_report` | 杨旭 | 杜灿 | 是 |

## 7. Gitee 协作规范

仓库地址:

```text
https://gitee.com/cxcy666_admin/ai--scientist
```

成员邀请链接:

```text
https://gitee.com/cxcy666_admin/ai--scientist/invite_link?invite=0f140dabfbedf159a3f80d7774e2d7903790a5cb447d1991e511b1509403e86ee7cbd7aba9cd3b6a8da87cab6e3c90fa
```

推荐分支:

```text
main              稳定提交版
dev               日常集成分支
feature/*         功能分支
fix/*             修复分支
docs/*            文档分支
```

个人分支示例:

```text
feature/feng-langgraph-core
feature/feng-literature-tools
feature/ducan-web-ui
feature/ducan-dataset-profiler
docs/project-plan
```

提交规范:

```text
feat: 新功能
fix: bug 修复
docs: 文档
refactor: 重构
test: 测试
chore: 配置或杂项
```

合并规则:

- 所有人从 `dev` 拉分支。
- 功能完成后合并到 `dev`。
- `main` 只保存每周验收通过版本和最终提交版本。
- 不允许把 API Key、真实 `.env`、大型数据集、临时输出文件提交到仓库。

## 8. 每日同步规则

每天晚上同步一次, 每个人只需要说三件事:

```text
今天完成了什么:
遇到了什么问题:
明天准备做什么:
```

遇到接口字段变化时, 必须同步到文档, 否则前后端会互相卡住。

## 9. 每周里程碑

### 第 0 天: 2026-07-07 启动会

目标:

- 三人加入 Gitee 仓库。
- 确认网页版优先路线。
- 确认最终 MVP 场景: 工业缺陷检测或遥感小目标检测。
- 确认每周集成时间。

验收:

- 三人都能 clone 仓库。
- 本地能运行基础项目。
- `.env.example`、README、目录结构建好。

### 第 1 周: 2026-07-07 到 2026-07-13

目标:

- 建立项目骨架。
- 完成 FastAPI + Streamlit 基础联通。
- 完成 LangGraph mock workflow, 包含 Graph Agent mock 节点。
- 完成 Qwen/百炼 API 调用 demo。
- 完成 PostgreSQL/Redis 基础配置。

分工:

- 杨旭: 建仓库结构、接口规范、README、任务板、ScientistState、mock graph、PostgreSQL/Redis 配置。
- 冯佳乐: 初始化文献链目录、mock Paper Pool、mock Fact Pool、mock Evidence Board。
- 杜灿: Streamlit 首页、创建任务页、任务状态页。

验收:

- 网页能创建一个 mock run。
- 后端能从 START 跑到 END。
- 页面能显示当前节点和 mock final report。

### 第 2 周: 2026-07-14 到 2026-07-20

目标:

- 完成文献检索、PDF 读取、基础引用校验。
- 完成 CV 数据集扫描和基础画像。
- 前端展示 Paper Pool 和 Dataset Profile。

分工:

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

分工:

- 冯佳乐: Evidence Board、Evidence Reviewer、文献证据补强。
- 杜灿: 候选假设表格和详情区域。
- 杨旭: Gap Discovery、4 个 Hypothesis Agents、假设 JSON schema 和 prompt 质量。

验收:

- 系统能基于真实文献和数据画像生成至少 6 个候选假设。
- 每个假设包含 mechanism、evidence、test_method、risk。

### 第 4 周: 2026-07-28 到 2026-08-03

目标:

- 完成 4 个 Reviewer Agents。
- 完成 Aggregation Agent。
- 完成审稿失败回退循环。
- 完成 Human Review 网页交互。

分工:

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

分工:

- 冯佳乐: 文献链稳定性、工具执行协助。
- 杜灿: Metric/Plot 展示、实验日志页面。
- 杨旭: Experiment Designer、最小实验范围、报告结构。

验收:

- 选中假设能生成 baseline、metrics、ablation。
- 至少有一个真实工具执行结果。

### 第 6 周: 2026-08-11 到 2026-08-17

目标:

- 完成 Report Writer Agent。
- 完成 Markdown 报告预览。
- 完成 PDF/HTML 导出初版。
- 跑通网页输入到最终报告的完整闭环。

分工:

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

分工:

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

### 提交冻结期: 2026-09-01 到 2026-09-05

目标:

- 完成最终检查。
- 固定代码版本和演示版本。
- 检查压缩包、报名表、网盘链接、截图。

验收:

- 比赛提交版冻结。
- 技术方案 PDF、源码、演示视频、截图、复现说明全部准备好。

### 展示完善期: 2026-09-06 到 2026-09-10

目标:

- 准备答辩展示版。
- 整理讲稿。
- 准备常见问题回答。
- 复盘代码结构和项目亮点。

验收:

- 杨旭可以讲清楚整体架构和项目价值。
- 冯佳乐可以讲清楚多智能体和工具增强。
- 杜灿可以讲清楚网页交互、数据画像和实验展示。

## 10. 启动会讲解顺序

杨旭可以按这个顺序开会:

1. 我们做的是 Web 版 CV AI Scientist, 不是聊天机器人。
2. 核心技术是 LangGraph 多智能体编排 + Tool 工具增强。
3. 每个 Agent 会产生结构化结果, 进入 Result Pool。
4. 网页端负责展示流程、候选假设、评分、数据图表和最终报告。
5. 杨旭负责主图、Supervisor、假设审稿和报告; 冯佳乐负责文献证据链; 杜灿负责视觉数据、实验链和网页展示。
6. 7 月 13 日前先跑通 mock 闭环。
7. 8 月中旬跑通完整真实流程。
8. 9 月 5 日前冻结比赛提交版。
