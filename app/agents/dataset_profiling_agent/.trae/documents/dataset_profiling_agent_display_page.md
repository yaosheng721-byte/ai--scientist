# Dataset Profiling Agent 展示页面（mock 闭环）

## Context（背景）

项目已有一个规则型 `DatasetProfilingAgent`，按固定顺序调度 4 个 Tool（dataset_scan → annotation_parser → image_quality → plot_generator）对数据集做画像。当前只能通过 `examples/demo.py` 在终端运行，看不到调度过程和结果的结构化展示。

用户希望在**根目录**做一个展示用页面，能触发规则型智能体对 `demo_dataset` 跑一轮 mock 闭环，并展示**调度执行日志 + 汇总结果**。

硬约束：**只新增页面文件，不改任何现有代码文件**。
样式：简洁高效、深色主题、加一点渐变。

## 现状（探索结论）

- Agent 入口：[agent/dataset_profiling_agent.py](file:///d:/Python项目/dataset_profiling_agent/agent/dataset_profiling_agent.py) 的 `DatasetProfilingAgent().run({"dataset_path": ...})` → 返回汇总 dict
- 调度顺序：`dataset_scan` → `annotation_parser(scan_result["annotation_files"][0])` → `image_quality` → `plot_generator`，最后 `**` 合并 + `observations`
- [logs/tool_logger.py](file:///d:/Python项目/dataset_profiling_agent/logs/tool_logger.py) 的 `tool_log(name, status)` 是 `print(f"[{time}] [{name}] {status}")` 到 stdout
- demo_dataset：3 张 jpg + 1 个空 `4.txt`（被识别为 YOLO 标注）
- image_quality / plot_generator / parse_yolo / parse_voc 返回死数据；parse_coco 真实解析
- 返回 dict 含：`dataset_name` / `image_count` / `splits` / `image_dirs` / `annotation_files` / `mask_dirs` / `image_extensions` / `annotation_format` / `quality_statistics` / `artifacts` / `observations`
- 已知小坑（不动它）：`annotation_files` 为空时 `agent.run` 会 IndexError；`annotation_format` 字段被 parse_yolo 的 str 覆盖 scan 的 list

## 方案

### 新增文件：根目录 `app.py`（唯一改动）

只新增 `app.py` 一个文件。不创建 `.streamlit/config.toml`，不改任何现有文件。深色 + 渐变全部靠 `app.py` 内 CSS 注入实现。

### 核心 mock 闭环逻辑

1. 输入 `dataset_path`（默认 `demo_dataset` 绝对路径）+ 「运行 Agent」按钮
2. 点击后：
   - 用 `contextlib.redirect_stdout(io.StringIO())` 包裹 `agent.run()`
   - 捕获 `tool_log` 的 print 作为「执行日志」（纯页面内操作，不改 tool_logger）
   - `try/except` 捕获异常（如目录无标注文件导致 `annotation_files[0]` 越界），用 `st.error` 展示
3. 展示三块：
   - **执行日志区**：捕获的日志按行展示，按 Tool 分段高亮，体现规则型调度顺序（这是「规则型智能体」最直观的体现）
   - **结果概览**：深色卡片展示关键指标（image_count / annotation_format / splits / image_extensions）
   - **分模块结果**：标注解析（annotation_format / class_distribution）、图像质量（quality_statistics）、产物（artifacts）、observations
   - **原始 JSON**：`st.json` 展示完整 dict（折叠区）

### 复用现有代码（不改动，仅 import）

- `from agent.dataset_profiling_agent import DatasetProfilingAgent`
- Agent 内部已调度 4 个 Tool，页面只调 `agent.run()`，不重写调度逻辑

### 样式（深色 + 渐变，纯 CSS 注入）

- `st.set_page_config(page_title="Dataset Profiling Agent", layout="wide")`
- 注入 CSS：
  - `.stApp` 背景：深色渐变（如 `linear-gradient(160deg, #0f172a 0%, #1b1432 100%)`）
  - 内容卡片：`st.container(border=True)` + CSS 覆盖为深色卡片 + 微渐变边框
  - 按钮 / metric / text_input 用 CSS 覆盖为深色系
  - 强调色用偏冷亮色（青紫）做渐变点缀，文字高对比
- 不依赖任何外部图片/资源

### 异常与边界

- 路径不存在 → `st.error` 提示
- 目录无标注文件 → `agent.run` 抛 IndexError → `try/except` 捕获，友好提示「该目录没有标注文件，建议用 demo_dataset」
- 默认路径写死 `demo_dataset` 绝对路径，保证开箱即跑
- 运行前主区给一个引导说明 + 调度流程示意（dataset_scan → annotation_parser → image_quality → plot_generator）

## 关键文件

- 新增：`app.py`（根目录，**唯一改动**）
- 只读引用：`agent/dataset_profiling_agent.py`、`logs/tool_logger.py`、`tools/*`（均不改）

## 验证

1. `streamlit run app.py`
2. 默认路径（demo_dataset）点「运行 Agent」
3. 应看到：执行日志（4 个 Tool 的 start/finished）+ 结果概览卡片 + 分模块结果 + 原始 JSON
4. 改成不存在的路径 → 看到 `st.error`，页面不崩溃
5. `git status` 确认只有 `app.py` 一个新文件，无现有文件被改动
