"""CV AI Scientist 前端主入口（mock 闭环版）。

页面：
    1. 任务创建页      - 调 POST /runs
    2. 工作流状态页    - 调 GET /runs/{run_id}
    3. Result Pool 展示页 - 调 GET /runs/{run_id}/results?pool_type=xxx
    4. 候选假设评分页  - 调 GET /runs/{run_id}/results?pool_type=hypothesis
    5. 人工选择/驳回   - 调 POST /runs/{run_id}/feedback
    6. 数据集画像页    - 调 POST /runs（task_type=dataset_profiling）+ GET /runs/{run_id}
    7. 实验结果页      - 调 GET /runs/{run_id}/artifacts
    8. 报告预览导出页  - 调 GET /runs/{run_id}/report
"""

import os

import requests
import streamlit as st
import plotly.graph_objects as go


# ============================================================================
# 配置
# ============================================================================

API_BASE = "http://127.0.0.1:8000"

# 默认 run_id（mock 模式下用这个就行）
DEFAULT_MOCK_RUN_ID = "run_mock_001"


# ============================================================================
# 页面配置 + 深色主题样式
# ============================================================================

st.set_page_config(
    page_title="CV AI Scientist",
    page_icon="🔬",
    layout="wide",
)

CSS = """
<style>
/* ========== 全局背景与文字 ========== */
.stApp {
    background: #0f172a;
    color: #e2e8f0;
}

/* 标题层级 */
.stApp h1 { color: #f8fafc; font-size: 26px; font-weight: 700; }
.stApp h2 { color: #f1f5f9; font-size: 20px; font-weight: 600; }
.stApp h3 { color: #e2e8f0; font-size: 16px; font-weight: 600; }
.stApp h4 { color: #cbd5e1; font-size: 14px; font-weight: 600; }
.stApp p, .stApp li, .stApp span { color: #cbd5e1; }

/* ========== 侧边栏 ========== */
.stApp [data-testid="stSidebar"] {
    background: #1e293b;
    border-right: 1px solid rgba(148, 163, 184, 0.12);
}
.stApp [data-testid="stSidebarNav"] { display: none; }

/* 侧边栏导航按钮 */
.stApp [data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    color: #94a3b8;
    padding: 10px 14px;
    margin: 2px 0;
    border-radius: 6px;
    transition: all 0.15s ease;
    font-size: 13px;
}
.stApp [data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(56, 189, 248, 0.08);
    border-left-color: rgba(56, 189, 248, 0.4);
    color: #e2e8f0;
}

/* ========== 页面标题 ========== */
.page-title {
    font-size: 24px;
    font-weight: 700;
    color: #f8fafc;
    margin-bottom: 4px;
}
.page-subtitle {
    color: #64748b;
    font-size: 13px;
    margin-bottom: 20px;
}

/* ========== 区块标题（带左侧色条） ========== */
.section-title {
    font-size: 15px;
    font-weight: 600;
    color: #f1f5f9;
    letter-spacing: 0.3px;
    margin: 0 0 12px 0;
    padding: 8px 12px;
    background: rgba(56, 189, 248, 0.06);
    border-left: 3px solid #38bdf8;
    border-radius: 0 6px 6px 0;
}

/* ========== 指标卡片 ========== */
.metric-card {
    background: #1e293b;
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 10px;
    padding: 14px 16px;
    height: 100%;
    transition: all 0.2s ease;
}
.metric-card:hover {
    border-color: rgba(56, 189, 248, 0.3);
    background: #233044;
}
.metric-card .metric-label {
    color: #64748b;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
.metric-card .metric-value {
    color: #f8fafc;
    font-size: 22px;
    font-weight: 700;
    word-break: break-all;
}
.metric-card .metric-sub {
    color: #475569;
    font-size: 11px;
    margin-top: 4px;
}

/* ========== 按钮 ========== */
.stApp div.stButton > button {
    background: #334155;
    color: #e2e8f0;
    border: 1px solid #475569;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    padding: 8px 20px;
    transition: all 0.15s ease;
}
.stApp div.stButton > button:hover {
    background: #3b4d63;
    border-color: #38bdf8;
    color: #f8fafc;
}

/* 主操作按钮（渐变蓝） */
.stApp div.stButton > button[kind="primary"],
.stApp div.stButton > button[data-testid*="primary"] {
    background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
    border: none;
    color: #ffffff;
}
.stApp div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
    box-shadow: 0 4px 14px rgba(14, 165, 233, 0.3);
}

/* ========== 输入框 ========== */
.stApp .stTextInput > div > div > input,
.stApp .stTextArea > div > div > textarea,
.stApp .stSelectbox > div > div > div {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 8px;
    font-size: 13px;
}
.stApp .stTextInput > div > div > input:focus,
.stApp .stTextArea > div > div > textarea:focus {
    border-color: #38bdf8;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.15);
}
.stApp .stTextInput label,
.stApp .stTextArea label,
.stApp .stSelectbox label {
    color: #94a3b8;
    font-size: 13px;
    font-weight: 500;
}

/* ========== 数据表格 ========== */
.stApp .stDataFrame {
    color: #e2e8f0;
}
.stApp .stDataFrame table {
    background: #1e293b;
}
.stApp .stDataFrame th {
    background: #233044;
    color: #94a3b8;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.stApp .stDataFrame td {
    color: #cbd5e1;
    font-size: 13px;
}

/* ========== Tab 样式 ========== */
.stApp .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}
.stApp .stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 6px 6px 0 0;
    color: #64748b;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
}
.stApp .stTabs [data-baseweb="tab"]:hover {
    color: #94a3b8;
    background-color: rgba(56, 189, 248, 0.04);
}
.stApp .stTabs [aria-selected="true"] {
    color: #38bdf8;
    border-bottom: 2px solid #38bdf8;
    background-color: rgba(56, 189, 248, 0.06);
}

/* ========== JSON 展示 ========== */
.stApp .stJson {
    background: #1e293b;
    border: 1px solid rgba(148, 163, 184, 0.1);
    border-radius: 8px;
    padding: 12px;
    font-size: 12px;
}

/* ========== Expander ========== */
.stApp .stExpander {
    border: 1px solid rgba(148, 163, 184, 0.1);
    border-radius: 8px;
    background: #1e293b;
}
.stApp .stExpander > details > summary {
    color: #94a3b8;
    font-size: 13px;
    font-weight: 500;
}

/* ========== 状态标签 ========== */
.stApp .stAlert {
    border-radius: 8px;
    font-size: 13px;
}

/* ========== 分割线 ========== */
.stApp hr {
    border-color: rgba(148, 163, 184, 0.1);
    margin: 20px 0;
}

/* ========== 滚动条 ========== */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #1e293b; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================================
# 侧边栏导航
# ============================================================================

PAGES = [
    "任务创建页",
    "工作流状态页",
    "Result Pool 展示页",
    "候选假设评分页",
    "人工选择/驳回假设",
    "数据集画像页",
    "工具执行日志页",
    "实验结果页",
    "报告预览和导出页",
]

if "page" not in st.session_state:
    st.session_state.page = "任务创建页"
if "last_run_id" not in st.session_state:
    st.session_state.last_run_id = DEFAULT_MOCK_RUN_ID

with st.sidebar:
    st.markdown('<div style="font-size:20px;font-weight:700;color:#f8fafc;margin-bottom:2px;">CV AI Scientist</div>', unsafe_allow_html=True)
    st.caption("科研助手系统 · mock 闭环版")
    st.divider()
    for name in PAGES:
        is_active = st.session_state.page == name
        label = f"{'▶ ' if is_active else '  '}{name}"
        if st.button(label, key=f"nav_{name}", use_container_width=True):
            st.session_state.page = name
            st.rerun()
    st.divider()
    st.caption(f"API: {API_BASE}")
    st.caption(f"当前 Run ID: `{st.session_state.last_run_id}`")

page = st.session_state.page


# ============================================================================
# 工具函数
# ============================================================================

def gradient_title(text, sub=""):
    """页面标题。"""
    html = f'<div class="page-title">{text}</div>'
    if sub:
        html += f'<div class="page-subtitle">{sub}</div>'
    st.markdown(html, unsafe_allow_html=True)


def section_title(text):
    """区块小标题。"""
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def metric_card(label, value, sub=""):
    """指标卡片。"""
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_chart_spec(chart_spec):
    """把 plot_generator 产出的 chart spec 渲染成 Plotly 图表。

    chart_spec 格式：
        - pie:  {"type": "pie", "title": "...", "data": {"labels": [], "values": [], "colors": []}}
        - bar:  {"type": "bar", "title": "...", "orientation": "h",
                 "xaxis_title": "...", "data": {"labels": [], "series": [{"name": "", "values": [], "color": ""}]}}
        - bar_grouped: 同 bar
    """
    if not chart_spec or not isinstance(chart_spec, dict):
        return

    title = chart_spec.get("title", "")
    chart_type = chart_spec.get("type", "")
    data = chart_spec.get("data", {})

    try:
        if chart_type == "pie":
            labels = data.get("labels", [])
            values = data.get("values", [])
            colors = data.get("colors", None)
            fig = go.Figure(
                data=[go.Pie(
                    labels=labels,
                    values=values,
                    marker=dict(colors=colors) if colors else None,
                    hole=0.4,
                    textinfo="label+percent",
                )]
            )
            fig.update_layout(
                title=dict(text=title, font=dict(color="#f1f5f9", size=14)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1"),
                showlegend=True,
                legend=dict(font=dict(color="#cbd5e1")),
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type in ("bar", "bar_grouped"):
            labels = data.get("labels", [])
            series_list = data.get("series", [])
            orientation = chart_spec.get("orientation", "v")
            xaxis_title = chart_spec.get("xaxis_title", "")

            fig = go.Figure()
            for s in series_list:
                if orientation == "h":
                    fig.add_trace(go.Bar(
                        name=s.get("name", ""),
                        y=labels,
                        x=s.get("values", []),
                        orientation="h",
                        marker_color=s.get("color", "#f472b6"),
                    ))
                else:
                    fig.add_trace(go.Bar(
                        name=s.get("name", ""),
                        x=labels,
                        y=s.get("values", []),
                        marker_color=s.get("color", "#f472b6"),
                    ))

            fig.update_layout(
                title=dict(text=title, font=dict(color="#f1f5f9", size=14)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,23,42,0.5)",
                font=dict(color="#cbd5e1"),
                barmode="group" if chart_type == "bar_grouped" else "group",
                showlegend=True,
                legend=dict(font=dict(color="#cbd5e1")),
                margin=dict(l=20, r=20, t=50, b=20),
                xaxis=dict(
                    title=xaxis_title if orientation == "h" else "",
                    gridcolor="rgba(148,163,184,0.1)",
                    color="#cbd5e1",
                ),
                yaxis=dict(
                    title=xaxis_title if orientation == "v" else "",
                    gridcolor="rgba(148,163,184,0.1)",
                    color="#cbd5e1",
                ),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"未知图表类型：{chart_type}")
    except Exception as e:  # noqa: BLE001
        st.error(f"图表渲染失败：{e}")
        st.json(chart_spec, expanded=1)


def render_sample_image(sample):
    """渲染单张样本图片（含 mask 对比）。"""
    title = sample.get("title", "")
    image_path = sample.get("image_path", "")
    mask_path = sample.get("mask_path")

    st.markdown(f"**{title}**")
    st.caption(f"路径：`{image_path}`")

    if not image_path or not os.path.exists(image_path):
        st.warning(f"图片不存在：{image_path}")
        return

    if mask_path and os.path.exists(mask_path):
        cols = st.columns(2)
        cols[0].image(image_path, caption="原图", use_container_width=True)
        cols[1].image(mask_path, caption="Mask", use_container_width=True)
    else:
        st.image(image_path, caption=title, use_container_width=True)


def api_get(path: str, params: dict | None = None, timeout: int = 10):
    """封装 GET 请求，统一错误处理。"""
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "无法连接后端服务，请确认 FastAPI 是否已启动（默认 http://127.0.0.1:8000）"
    except requests.exceptions.Timeout:
        return None, "请求超时"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP 错误：{e.response.status_code} {e.response.text}"
    except Exception as e:  # noqa: BLE001
        return None, f"请求失败：{type(e).__name__}: {e}"


def api_post(path: str, json_body: dict | None = None, timeout: int = 30):
    """封装 POST 请求，统一错误处理。"""
    try:
        resp = requests.post(f"{API_BASE}{path}", json=json_body, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "无法连接后端服务，请确认 FastAPI 是否已启动"
    except requests.exceptions.Timeout:
        return None, "请求超时"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP 错误：{e.response.status_code} {e.response.text}"
    except Exception as e:  # noqa: BLE001
        return None, f"请求失败：{type(e).__name__}: {e}"


# ============================================================================
# 页面 1：任务创建页
# ============================================================================

if page == "任务创建页":
    gradient_title("CV AI Scientist", "创建研究任务，启动多智能体科研流程")

    with st.form("create_run"):
        query = st.text_area(
            "研究问题",
            value="研究工业缺陷检测中小缺陷定位不稳定的问题",
            help="输入你想研究的科学问题",
        )
        domain = st.selectbox("领域", ["industrial", "remote_sensing", "medical", "general_cv"])
        task_type = st.selectbox(
            "任务类型",
            ["dataset_profiling", "anomaly_detection", "detection", "segmentation", "classification", "change_detection"],
            help="选 dataset_profiling 会触发数据集画像分析",
        )
        dataset_path = st.text_input(
            "数据集路径",
            value="app/agents/dataset_profiling_agent/demo_dataset/MVTec/bottle",
            help="数据集的本地路径",
        )
        submitted = st.form_submit_button("创建研究任务")

    if submitted:
        body = {
            "query": query,
            "domain": domain,
            "task_type": task_type,
            "dataset_path": dataset_path,
        }
        data, err = api_post("/runs", body)
        if err:
            st.error(err)
        else:
            run_id = data.get("run_id", "")
            st.session_state.last_run_id = run_id
            st.success("任务已创建")
            st.json(data, expanded=1)
            st.info(f"Run ID 已记录：{run_id}，可去「工作流状态页」查看进度")


# ============================================================================
# 页面 2：工作流状态页
# ============================================================================

elif page == "工作流状态页":
    gradient_title("工作流状态", "查看任务执行进度")

    run_id = st.text_input("Run ID", value=st.session_state.get("last_run_id", ""))
    auto_refresh = st.checkbox("自动刷新（每 2 秒）", value=True)

    if not run_id:
        st.info("请先在「任务创建页」创建任务，或在此输入 Run ID")
    else:
        data, err = api_get(f"/runs/{run_id}")
        if err:
            st.error(err)
        else:
            status = data.get("status", "unknown")
            current_node = data.get("current_node", "-")
            result = data.get("result")
            error = data.get("error")

            status_emoji = {
                "created": "⚪",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
                "not_found": "❓",
            }.get(status, "❓")

            col1, col2, col3 = st.columns(3)
            col1.metric("状态", f"{status_emoji} {status}")
            col2.metric("当前节点", current_node)
            col3.metric("进度", f"{data.get('progress', 0)}%")

            if error:
                st.error(f"错误信息：{error}")

            if status == "completed" and result:
                st.json(result, expanded=1)

            if auto_refresh and status == "running":
                import time
                time.sleep(2)
                st.rerun()


# ============================================================================
# 页面 3：Result Pool 展示页
# ============================================================================

elif page == "Result Pool 展示页":
    gradient_title("Result Pool", "展示文献链和假设链的所有中间产物")

    run_id = st.text_input("Run ID", value=st.session_state.get("last_run_id", ""))

    tab_paper, tab_fact, tab_gap, tab_hyp, tab_review = st.tabs([
        "📄 Paper Pool",
        "💡 Fact Pool",
        "🔍 Gap Pool",
        "🧠 Hypothesis Pool",
        "⭐ Review Pool",
    ])

    with tab_paper:
        section_title("论文池（Paper Pool）")
        data, err = api_get(f"/runs/{run_id}/results", {"pool_type": "paper"})
        if err:
            st.error(err)
        else:
            st.caption(f"共 {data.get('count', 0)} 篇论文")
            items = data.get("items", [])
            if items:
                # 简表
                import pandas as pd
                df = pd.DataFrame([{
                    "paper_id": it.get("paper_id", ""),
                    "title": it.get("title", "")[:60] + ("..." if len(it.get("title", "")) > 60 else ""),
                    "year": it.get("year", ""),
                    "venue": it.get("venue", ""),
                    "relevance": it.get("relevance_score", 0),
                } for it in items])
                st.dataframe(df, use_container_width=True, hide_index=True)
                # 详情
                for it in items:
                    with st.expander(f"{it.get('paper_id', '')} · {it.get('title', '')}"):
                        st.write(f"**作者**：{', '.join(it.get('authors', []))}")
                        st.write(f"**年份**：{it.get('year', '')} · **会议**：{it.get('venue', '')}")
                        st.write(f"**相关度**：{it.get('relevance_score', 0)}")
                        st.write(f"**URL**：{it.get('url', '')}")
                        st.write(f"**DOI**：{it.get('doi', '') or '—'} · **arXiv**：{it.get('arxiv_id', '') or '—'}")
            else:
                st.info("暂无论文数据")

    with tab_fact:
        section_title("事实池（Fact Pool）")
        data, err = api_get(f"/runs/{run_id}/results", {"pool_type": "fact"})
        if err:
            st.error(err)
        else:
            st.caption(f"共 {data.get('count', 0)} 条事实")
            items = data.get("items", [])
            if items:
                import pandas as pd
                df = pd.DataFrame([{
                    "fact_id": it.get("fact_id", ""),
                    "claim": it.get("claim", "")[:80] + ("..." if len(it.get("claim", "")) > 80 else ""),
                    "source": it.get("source_paper_id", ""),
                    "section": it.get("section", ""),
                    "confidence": it.get("confidence", 0),
                } for it in items])
                st.dataframe(df, use_container_width=True, hide_index=True)
                for it in items:
                    with st.expander(f"{it.get('fact_id', '')} · {it.get('claim', '')[:60]}..."):
                        st.write(f"**Claim**：{it.get('claim', '')}")
                        st.write(f"**证据原文**：{it.get('evidence_text', '')}")
                        st.write(f"**来源论文**：{it.get('source_paper_id', '')} · **章节**：{it.get('section', '')} · **页码**：{it.get('page', '')}")
                        st.write(f"**置信度**：{it.get('confidence', 0)}")
            else:
                st.info("暂无事实数据")

    with tab_gap:
        section_title("研究空白池（Gap Pool）")
        data, err = api_get(f"/runs/{run_id}/results", {"pool_type": "gap"})
        if err:
            st.error(err)
        else:
            st.caption(f"共 {data.get('count', 0)} 个研究空白")
            items = data.get("items", [])
            for it in items:
                with st.expander(f"{it.get('gap_id', '')} · {it.get('description', '')[:60]}..."):
                    st.write(f"**描述**：{it.get('description', '')}")
                    st.write(f"**类型**：{it.get('gap_type', '')}")
                    st.write(f"**支持事实**：{', '.join(it.get('supporting_facts', []))}")
                    st.write(f"**来源论文**：{', '.join(it.get('source_papers', []))}")

    with tab_hyp:
        section_title("候选假设池（Hypothesis Pool）")
        data, err = api_get(f"/runs/{run_id}/results", {"pool_type": "hypothesis"})
        if err:
            st.error(err)
        else:
            st.caption(f"共 {data.get('count', 0)} 个候选假设")
            items = data.get("items", [])
            if items:
                import pandas as pd
                df = pd.DataFrame([{
                    "hypothesis_id": it.get("hypothesis_id", ""),
                    "source_agent": it.get("source_agent", ""),
                    "hypothesis": it.get("hypothesis", "")[:60] + ("..." if len(it.get("hypothesis", "")) > 60 else ""),
                    "novelty": it.get("scores", {}).get("novelty", 0),
                    "feasibility": it.get("scores", {}).get("feasibility", 0),
                    "evidence": it.get("scores", {}).get("evidence", 0),
                    "reproducibility": it.get("scores", {}).get("reproducibility", 0),
                } for it in items])
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.info("详细评分见「候选假设评分页」")
            else:
                st.info("暂无假设数据")

    with tab_review:
        section_title("评分池（Review Pool）")
        data, err = api_get(f"/runs/{run_id}/results", {"pool_type": "review"})
        if err:
            st.error(err)
        else:
            st.caption(f"共 {data.get('count', 0)} 条评分")
            items = data.get("items", [])
            if items:
                import pandas as pd
                df = pd.DataFrame([{
                    "review_id": it.get("review_id", ""),
                    "hypothesis_id": it.get("hypothesis_id", ""),
                    "reviewer_type": it.get("reviewer_type", ""),
                    "score": it.get("score", 0),
                } for it in items])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("暂无评分数据")


# ============================================================================
# 页面 4：候选假设评分页
# ============================================================================

elif page == "候选假设评分页":
    gradient_title("候选假设评分", "展示所有候选假设及 4 维评分")

    run_id = st.text_input("Run ID", value=st.session_state.get("last_run_id", ""))

    data, err = api_get(f"/runs/{run_id}/results", {"pool_type": "hypothesis"})
    if err:
        st.error(err)
    else:
        items = data.get("items", [])
        st.caption(f"共 {len(items)} 个候选假设")

        if not items:
            st.info("暂无假设数据")
        else:
            # 概览表格
            import pandas as pd
            section_title("假设概览")
            df = pd.DataFrame([{
                "ID": it.get("hypothesis_id", ""),
                "来源": it.get("source_agent", ""),
                "假设": it.get("hypothesis", "")[:80] + ("..." if len(it.get("hypothesis", "")) > 80 else ""),
                "novelty": it.get("scores", {}).get("novelty", 0),
                "feasibility": it.get("scores", {}).get("feasibility", 0),
                "evidence": it.get("scores", {}).get("evidence", 0),
                "reproducibility": it.get("scores", {}).get("reproducibility", 0),
                "加权总分": round(
                    it.get("scores", {}).get("novelty", 0) * 0.3
                    + it.get("scores", {}).get("feasibility", 0) * 0.3
                    + it.get("scores", {}).get("evidence", 0) * 0.2
                    + it.get("scores", {}).get("reproducibility", 0) * 0.2,
                    2,
                ),
            } for it in items])
            df = df.sort_values("加权总分", ascending=False).reset_index(drop=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 详情
            section_title("假设详情")
            for it in items:
                scores = it.get("scores", {})
                title = f"{it.get('hypothesis_id', '')} · {it.get('hypothesis', '')[:50]}..."
                with st.expander(title, expanded=False):
                    st.write(f"**假设**：{it.get('hypothesis', '')}")
                    st.write(f"**来源 Agent**：{it.get('source_agent', '')}")
                    st.write(f"**机制**：{it.get('mechanism', '')}")
                    st.write(f"**预期效果**：{it.get('expected_effect', '')}")
                    st.write(f"**测试方法**：{it.get('test_method', '')}")
                    st.write(f"**所需数据**：{', '.join(it.get('required_data', []))}")
                    st.write(f"**支持证据**：{', '.join(it.get('supporting_evidence', []))}")
                    st.write(f"**风险**：{', '.join(it.get('risks', []))}")

                    # 4 维评分进度条
                    st.write("**评分**：")
                    score_cols = st.columns(4)
                    score_cols[0].metric("Novelty", scores.get("novelty", 0))
                    score_cols[1].metric("Feasibility", scores.get("feasibility", 0))
                    score_cols[2].metric("Evidence", scores.get("evidence", 0))
                    score_cols[3].metric("Reproducibility", scores.get("reproducibility", 0))

                    # 低分项标红
                    for k, v in scores.items():
                        if v < 70:
                            st.warning(f"低分项：**{k}** = {v}，建议关注")


# ============================================================================
# 页面 5：人工选择/驳回假设
# ============================================================================

elif page == "人工选择/驳回假设":
    gradient_title("人工选择/驳回假设", "审核候选假设，决定是否进入实验阶段")

    run_id = st.text_input("Run ID", value=st.session_state.get("last_run_id", ""))

    data, err = api_get(f"/runs/{run_id}/results", {"pool_type": "hypothesis"})
    if err:
        st.error(err)
    else:
        items = data.get("items", [])
        if not items:
            st.info("暂无假设数据，请先去「候选假设评分页」查看")
        else:
            st.caption(f"共 {len(items)} 个候选假设，请选择一个 approve 或全部 reject")

            # 人工修改意见
            comments = st.text_area("人工修改意见（可选）", placeholder="例如：优先选择可在 MVTec 上快速验证的假设")

            selected_id = None

            for it in items:
                scores = it.get("scores", {})
                col_info, col_action = st.columns([4, 1])
                with col_info:
                    st.write(f"**{it.get('hypothesis_id', '')}** · {it.get('hypothesis', '')}")
                    st.caption(
                        f"novelty={scores.get('novelty', 0)} · "
                        f"feasibility={scores.get('feasibility', 0)} · "
                        f"evidence={scores.get('evidence', 0)} · "
                        f"reproducibility={scores.get('reproducibility', 0)}"
                    )
                with col_action:
                    if st.button("Approve", key=f"approve_{it.get('hypothesis_id', '')}"):
                        selected_id = it.get("hypothesis_id", "")
                        st.session_state["_pending_decision"] = "approve"
                        st.session_state["_pending_hypothesis_id"] = selected_id
                        st.rerun()
                    if st.button("Reject", key=f"reject_{it.get('hypothesis_id', '')}"):
                        st.session_state["_pending_decision"] = "reject"
                        st.session_state["_pending_hypothesis_id"] = it.get("hypothesis_id", "")
                        st.rerun()

            # 全部驳回按钮
            if st.button("全部驳回并要求重新生成", type="primary"):
                st.session_state["_pending_decision"] = "reject_all"
                st.session_state["_pending_hypothesis_id"] = None
                st.rerun()

            # 处理待执行的决策
            pending_decision = st.session_state.pop("_pending_decision", None)
            pending_hyp_id = st.session_state.pop("_pending_hypothesis_id", None)
            if pending_decision:
                body = {
                    "decision": "approve" if pending_decision == "approve" else "reject",
                    "selected_hypothesis_id": pending_hyp_id,
                    "comments": comments,
                }
                resp, err = api_post(f"/runs/{run_id}/feedback", body)
                if err:
                    st.error(err)
                else:
                    if resp.get("status") == "approved":
                        st.success(f"已批准假设：{pending_hyp_id}")
                        st.json(resp, expanded=1)
                        st.info("可去「实验结果页」查看实验执行情况")
                    else:
                        st.warning(f"已驳回（{pending_decision}），假设将重新生成")
                        st.json(resp, expanded=1)


# ============================================================================
# 页面 6：数据集画像页
# ============================================================================

elif page == "数据集画像页":
    gradient_title("数据集画像", "调用 Dataset Profiling Agent 生成数据集统计与可视化")

    st.markdown(
        '<div style="color:#94a3b8;font-size:13px;margin-bottom:14px;">'
        '通过后端 API 触发 Dataset Profiling Agent，展示数据集统计结果'
        '</div>',
        unsafe_allow_html=True,
    )

    # 工具流程示意
    tool_flow_html = """
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px;align-items:center;">
        <span style="background:rgba(244,114,182,0.15);color:#f472b6;padding:6px 14px;border-radius:20px;font-size:12px;border:1px solid rgba(244,114,182,0.3);">dataset_scan</span>
        <span style="color:#64748b;">→</span>
        <span style="background:rgba(244,114,182,0.15);color:#f472b6;padding:6px 14px;border-radius:20px;font-size:12px;border:1px solid rgba(244,114,182,0.3);">annotation_parser</span>
        <span style="color:#64748b;">→</span>
        <span style="background:rgba(244,114,182,0.15);color:#f472b6;padding:6px 14px;border-radius:20px;font-size:12px;border:1px solid rgba(244,114,182,0.3);">image_quality</span>
        <span style="color:#64748b;">→</span>
        <span style="background:rgba(244,114,182,0.15);color:#f472b6;padding:6px 14px;border-radius:20px;font-size:12px;border:1px solid rgba(244,114,182,0.3);">opencv_image_analyzer</span>
        <span style="color:#64748b;">→</span>
        <span style="background:rgba(34,211,238,0.15);color:#22d3ee;padding:6px 14px;border-radius:20px;font-size:12px;border:1px solid rgba(34,211,238,0.3);">plot_generator</span>
    </div>
    """
    st.markdown(tool_flow_html, unsafe_allow_html=True)

    # 输入区
    cols = st.columns([4, 1])
    with cols[0]:
        dataset_path = st.text_input(
            "数据集路径（dataset_path）",
            value="app/agents/dataset_profiling_agent/demo_dataset/MVTec/bottle",
            help="默认指向项目内的 demo_dataset，开箱即跑",
        )
    with cols[1]:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        run_clicked = st.button("运行 Agent", use_container_width=True)

    # 触发任务
    if run_clicked:
        body = {
            "query": "dataset profiling",
            "task_type": "dataset_profiling",
            "dataset_path": dataset_path,
        }
        with st.spinner("正在创建任务..."):
            data, err = api_post("/runs", body)
        if err:
            st.error(err)
        else:
            new_run_id = data.get("run_id", "")
            st.session_state.last_run_id = new_run_id
            st.session_state.dp_run_id = new_run_id
            st.success(f"任务已创建，Run ID: {new_run_id}")

    # 查询结果
    dp_run_id = st.session_state.get("dp_run_id", st.session_state.get("last_run_id", ""))
    if dp_run_id:
        section_title(f"任务结果（Run ID: {dp_run_id}）")

        # 自动刷新选项
        auto_refresh = st.checkbox("自动刷新（每 2 秒）", value=False, key="dp_auto_refresh")

        data, err = api_get(f"/runs/{dp_run_id}")
        if err:
            st.error(err)
        else:
            status = data.get("status", "unknown")
            result = data.get("result")
            error = data.get("error")

            status_emoji = {
                "created": "⚪",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
                "not_found": "❓",
            }.get(status, "❓")

            col1, col2 = st.columns(2)
            col1.metric("状态", f"{status_emoji} {status}")
            col2.metric("当前节点", data.get("current_node", "-"))

            if error:
                st.error(f"错误信息：{error}")

            # 展示结果
            if status == "completed" and result:
                st.markdown("---")

                # 取出各模块数据
                scan = result.get("dataset_scan", {}) if isinstance(result, dict) else {}
                quality = result.get("image_quality", {}) if isinstance(result, dict) else {}
                annotation = result.get("annotation_parser", {}) if isinstance(result, dict) else {}
                artifacts = result.get("artifacts", {}) if isinstance(result, dict) else {}

                # result 是扁平结构，scan 的字段直接在 result 里
                # 兼容两种结构
                if not scan:
                    scan = {
                        k: v for k, v in result.items()
                        if k in ("dataset_name", "dataset_path", "image_count",
                                 "splits", "annotation_format", "image_extensions")
                    } if isinstance(result, dict) else {}
                if not quality and isinstance(result, dict):
                    quality = result.get("quality_statistics", {})
                if not annotation and isinstance(result, dict):
                    annotation = {
                        k: v for k, v in result.items()
                        if k in ("annotation_format", "annotation_stats")
                    }

                interactive_charts = artifacts.get("interactive_charts", [])
                sample_images = artifacts.get("sample_images", [])
                file_tree = artifacts.get("file_tree", {})
                profile_json_path = artifacts.get("profile_json", "")

                # 关键指标卡片
                section_title("关键指标")
                # 安全提取字段（result 可能是 dict 或其他类型）
                if isinstance(result, dict):
                    image_count = result.get("image_count", "-")
                    splits = result.get("splits", {})
                    if not isinstance(splits, dict):
                        splits = {}
                    ann_format = result.get("annotation_format", [])
                    if isinstance(ann_format, (list, tuple)):
                        ann_format_str = ", ".join(str(x) for x in ann_format) or "-"
                    elif ann_format:
                        ann_format_str = str(ann_format)
                    else:
                        ann_format_str = "-"
                else:
                    image_count = "-"
                    splits = {}
                    ann_format_str = "-"

                m_cols = st.columns(4)
                m_cols[0].metric("图像总数", image_count)
                m_cols[1].metric("类别数", len(splits))
                m_cols[2].metric("划分", ", ".join(splits.keys()) if splits else "-")
                m_cols[3].metric("标注格式", ann_format_str)

                # 数据观察
                observations = result.get("observations", []) if isinstance(result, dict) else []
                if observations:
                    section_title("数据观察（Observations）")
                    for obs in observations:
                        st.markdown(
                            f'<div style="background:rgba(30,41,59,0.4);border-left:3px solid #f472b6;'
                            f'padding:10px 14px;margin:6px 0;border-radius:0 8px 8px 0;color:#cbd5e1;">'
                            f'{obs}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                # Tab 分类展示
                tab_charts, tab_samples, tab_overview, tab_quality, tab_annotation, tab_raw = st.tabs([
                    "📊 交互图表",
                    "🖼️ 样本图片",
                    "📋 概览",
                    "🎚️ 图像质量",
                    "🏷️ 标注",
                    "📄 原始 JSON",
                ])

                with tab_charts:
                    if interactive_charts:
                        st.caption(f"共 {len(interactive_charts)} 张图表")
                        for chart in interactive_charts:
                            render_chart_spec(chart)
                    else:
                        st.info("暂无图表数据")

                with tab_samples:
                    if sample_images:
                        st.caption(f"共 {len(sample_images)} 张样本")
                        for sample in sample_images:
                            render_sample_image(sample)
                            st.markdown("---")
                    else:
                        st.info("暂无样本图片")

                with tab_overview:
                    st.write("**数据集扫描结果**：")
                    overview_data = {
                        k: v for k, v in result.items()
                        if k in ("dataset_name", "dataset_path", "image_count",
                                 "splits", "annotation_format", "image_extensions",
                                 "num_classes", "classes")
                    } if isinstance(result, dict) else {}
                    if overview_data:
                        st.json(overview_data, expanded=1)
                    else:
                        st.info("无概览数据")

                with tab_quality:
                    st.write("**图像质量分析**：")
                    quality_data = result.get("quality_statistics", {}) if isinstance(result, dict) else {}
                    if quality_data:
                        st.json(quality_data, expanded=1)
                    else:
                        st.info("无质量数据")

                with tab_annotation:
                    st.write("**标注解析结果**：")
                    annotation_data = {
                        k: v for k, v in result.items()
                        if k in ("annotation_format", "annotation_stats", "num_annotations")
                    } if isinstance(result, dict) else {}
                    if annotation_data:
                        st.json(annotation_data, expanded=1)
                    else:
                        st.info("无标注数据")

                with tab_raw:
                    st.write(f"**Profile JSON 路径**：`{profile_json_path}`")
                    st.json(result, expanded=1)

            elif status == "running":
                st.info("Agent 正在运行中，请稍候...")
                if auto_refresh:
                    import time
                    time.sleep(2)
                    st.rerun()
            elif status in ("created", "not_found"):
                st.info("任务尚未开始或不存在，点击「运行 Agent」启动")
    else:
        st.markdown(
            '<div style="margin-top:20px;color:#94a3b8;text-align:center;padding:40px 0;">'
            '<div style="font-size:18px;margin-bottom:8px;">👈 点击「运行 Agent」开始</div>'
            '<div style="font-size:13px;">'
            'Agent 会依次调度 dataset_scan → annotation_parser → image_quality → opencv_image_analyzer → plot_generator'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# ============================================================================
# 页面 7：工具执行日志页（DC-15）
# ============================================================================

elif page == "工具执行日志页":
    gradient_title("工具执行日志", "展示所有工具调用的 input、output、status、error")

    run_id = st.text_input("Run ID", value=st.session_state.get("last_run_id", ""))

    data, err = api_get(f"/runs/{run_id}/tool_calls")
    if err:
        st.error(err)
    else:
        tool_calls = data.get("tool_calls", [])
        if not tool_calls:
            st.info("暂无工具调用记录")
        else:
            # 概览
            section_title("调用概览")
            import pandas as pd
            total = len(tool_calls)
            success = sum(1 for tc in tool_calls if tc.get("status") == "success")
            failed = sum(1 for tc in tool_calls if tc.get("status") == "failed")
            total_time = sum(tc.get("duration_sec", 0) for tc in tool_calls)

            m_cols = st.columns(4)
            m_cols[0].metric("总调用数", total)
            m_cols[1].metric("成功", f"✅ {success}")
            m_cols[2].metric("失败", f"❌ {failed}")
            m_cols[3].metric("总耗时", f"{total_time:.2f}s")

            st.markdown("---")

            # 表格视图
            section_title("调用列表")
            df = pd.DataFrame([{
                "call_id": tc.get("call_id", ""),
                "工具名": tc.get("tool_name", ""),
                "状态": "✅ success" if tc.get("status") == "success" else "❌ failed",
                "耗时(s)": tc.get("duration_sec", 0),
                "时间": tc.get("timestamp", ""),
                "输出摘要": tc.get("output_summary", "")[:50] + ("..." if len(tc.get("output_summary", "")) > 50 else ""),
            } for tc in tool_calls])
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("---")

            # 详情
            section_title("调用详情")
            for tc in tool_calls:
                status = tc.get("status", "unknown")
                status_icon = "✅" if status == "success" else "❌"
                title = f"{status_icon} {tc.get('call_id', '')} · {tc.get('tool_name', '')} · {tc.get('duration_sec', 0)}s"
                with st.expander(title, expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**输入参数（Input）**")
                        st.json(tc.get("input", {}), expanded=1)
                    with col2:
                        st.write("**输出摘要（Output）**")
                        st.info(tc.get("output_summary", "无"))

                    if tc.get("error"):
                        st.write("**错误信息（Error）**")
                        st.error(tc.get("error"))

                    st.write(f"**状态**：{status_icon} {status}")
                    st.write(f"**耗时**：{tc.get('duration_sec', 0)} 秒")
                    st.write(f"**时间戳**：{tc.get('timestamp', '-')}")


# ============================================================================
# 页面 8：实验结果页
# ============================================================================

elif page == "实验结果页":
    gradient_title("实验结果", "展示 baseline 指标、消融实验和产物列表")

    run_id = st.text_input("Run ID", value=st.session_state.get("last_run_id", ""))

    # 产物列表
    section_title("产物列表（Artifacts）")
    data, err = api_get(f"/runs/{run_id}/artifacts")
    if err:
        st.error(err)
    else:
        artifacts = data.get("artifacts", [])
        if artifacts:
            import pandas as pd
            df = pd.DataFrame(artifacts)
            st.dataframe(df, use_container_width=True, hide_index=True)
            for art in artifacts:
                st.write(f"- `{art.get('path', '')}` · {art.get('description', '')}")
        else:
            st.info("暂无产物")

    st.markdown("---")

    # 实验指标（从报告里取）
    section_title("实验指标")
    report_data, rep_err = api_get(f"/runs/{run_id}/report")
    if rep_err:
        st.error(rep_err)
    else:
        report = report_data.get("report", {})
        results = report.get("results", {})
        if results:
            import pandas as pd
            metric_rows = []
            for metric, vals in results.items():
                if isinstance(vals, dict):
                    metric_rows.append({
                        "指标": metric,
                        "baseline": vals.get("baseline", "-"),
                        "ours": vals.get("ours", "-"),
                        "提升": round(vals.get("ours", 0) - vals.get("baseline", 0), 2) if isinstance(vals.get("ours", 0), (int, float)) else "-",
                    })
            if metric_rows:
                st.dataframe(pd.DataFrame(metric_rows), use_container_width=True, hide_index=True)
            else:
                st.info("暂无指标数据")
        else:
            st.info("暂无指标数据")

        # 消融实验
        experiments = report.get("experiments", {})
        if experiments:
            section_title("消融实验")
            ablation = experiments.get("ablation", [])
            if ablation:
                st.write("**消融项**：")
                for ab in ablation:
                    st.write(f"- {ab}")

            st.write(f"**Baseline**：{experiments.get('baseline', '-')}")
            st.write(f"**指标**：{', '.join(experiments.get('metrics', []))}")


# ============================================================================
# 页面 8：报告预览和导出页
# ============================================================================

elif page == "报告预览和导出页":
    gradient_title("报告预览和导出", "展示最终报告内容，支持 Markdown 导出")

    run_id = st.text_input("Run ID", value=st.session_state.get("last_run_id", ""))

    data, err = api_get(f"/runs/{run_id}/report")
    if err:
        st.error(err)
    else:
        report = data.get("report", {})
        selected = data.get("selected_hypothesis", {})

        if not report:
            st.info("暂无报告数据")
        else:
            # 导出按钮
            section_title("导出")
            col_md, col_html = st.columns(2)

            # 生成 Markdown 内容
            def _build_markdown():
                lines = []
                lines.append(f"# {report.get('paper_title', 'Final Report')}\n")
                lines.append(f"**Abstract**：{report.get('paper_abstract', '')}\n")
                lines.append("## Problem Statement\n")
                lines.append(report.get("problem_statement", "") + "\n")
                lines.append("## Rationale\n")
                lines.append(report.get("rationale", "") + "\n")
                lines.append("## Technical Details\n")
                lines.append(report.get("technical_details", "") + "\n")
                lines.append("## Methods\n")
                lines.append(report.get("methods", "") + "\n")
                lines.append("## Datasets\n")
                ds = report.get("datasets", {})
                if ds:
                    lines.append(f"- **名称**：{ds.get('name', '')}")
                    lines.append(f"- **类别**：{', '.join(ds.get('categories', []))}")
                lines.append("\n## Experiments\n")
                exp = report.get("experiments", {})
                if exp:
                    lines.append(f"- **Baseline**：{exp.get('baseline', '')}")
                    lines.append(f"- **指标**：{', '.join(exp.get('metrics', []))}")
                lines.append("\n## Results\n")
                results = report.get("results", {})
                if results:
                    lines.append("| 指标 | Baseline | Ours |")
                    lines.append("|---|---|---|")
                    for k, v in results.items():
                        if isinstance(v, dict):
                            lines.append(f"| {k} | {v.get('baseline', '-')} | {v.get('ours', '-')} |")
                lines.append("\n## References\n")
                for ref in report.get("references", []):
                    lines.append(f"- [{ref.get('paper_id', '')}] {ref.get('title', '')}")
                return "\n".join(lines)

            md_content = _build_markdown()

            with col_md:
                st.download_button(
                    "📥 下载 Markdown",
                    data=md_content.encode("utf-8"),
                    file_name=f"{run_id}_final_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col_html:
                st.download_button(
                    "📥 下载 HTML",
                    data=f"<html><body><pre>{md_content}</pre></body></html>".encode("utf-8"),
                    file_name=f"{run_id}_final_report.html",
                    mime="text/html",
                    use_container_width=True,
                )

            st.markdown("---")

            # 报告预览
            section_title("报告预览")
            st.markdown(md_content)

            st.markdown("---")

            # 选中的假设
            if selected:
                section_title("选中的假设")
                st.json(selected, expanded=1)

            # 字段完整性检查
            section_title("字段完整性检查")
            required_fields = [
                "problem_statement", "rationale", "technical_details",
                "datasets", "source", "paper_title", "paper_abstract",
                "methods", "experiments", "results", "references",
            ]
            check_cols = st.columns(4)
            for i, field in enumerate(required_fields):
                col = check_cols[i % 4]
                has_field = bool(report.get(field))
                col.write(f"{'✅' if has_field else '❌'} {field}")
