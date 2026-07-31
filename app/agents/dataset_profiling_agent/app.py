"""
Dataset Profiling Agent 展示页面（mock 闭环）

只读引用现有 Agent：
    from agent.dataset_profiling_agent import DatasetProfilingAgent

运行：
    streamlit run app.py
"""

import os
import io
import re
import json
import time
import sys
import contextlib

# 把本文件所在目录加入 sys.path，确保相对 import（agent.xxx, tools.xxx）
# 在被外部模块 import 时也能正常工作
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import streamlit as st
import numpy as np
import pandas as pd

# 检测 plotly 是否可用
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from agent.dataset_profiling_agent import DatasetProfilingAgent
from tools.dataset_scan import dataset_scan
from tools.annotation_parser import annotation_parser
from tools.image_quality import image_quality
from tools.opencv_image_analyzer import opencv_image_analyzer
from tools.plot_generator import plot_generator


# --------------------------------------------------------------------------
# 基础配置
# --------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATASET = os.path.join(BASE_DIR, "demo_dataset")

TOOL_ORDER = [
    "dataset_scan",
    "annotation_parser",
    "image_quality",
    "opencv_image_analyzer",
    "plot_generator",
]

TOOL_COLORS = {
    "dataset_scan":            "#22d3ee",
    "annotation_parser":       "#a78bfa",
    "image_quality":           "#f472b6",
    "opencv_image_analyzer":   "#fb923c",
    "plot_generator":          "#34d399",
    "unknown":                 "#94a3b8",
}

NAV_ITEMS = [
    "📊  数据集概览",
    "🏷️  标注分析",
    "🖼️  图像质量",
    "📐  图像分析",
    "📦  产物",
    "🔍  图像浏览",
    "📜  原始 JSON",
]

if __name__ == "__main__":
    st.set_page_config(
        page_title="Dataset Profiling Agent",
        page_icon="🔬",
        layout="wide",
    )


# --------------------------------------------------------------------------
# 深色主题 + 侧边栏导航样式
# --------------------------------------------------------------------------

CSS = """
<style>

/* 整体深色背景 */
.stApp {
    background: #0b0f1a;
    color: #e2e8f0;
}

/* 标题文字色 */
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
    color: #f1f5f9;
}

/* 普通正文 */
.stApp p, .stApp li, .stApp span {
    color: #cbd5e1;
}

/* 侧边栏背景 */
.stApp [data-testid="stSidebar"] {
    background: #0f1524;
    border-right: 1px solid rgba(148, 163, 184, 0.1);
}

/* 侧边栏隐藏 Streamlit 默认的导航文字区域上边距 */
.stApp [data-testid="stSidebarNav"] {
    display: none;
}

/* 侧边栏 radio 改造成导航样式 */
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] {
    width: 100%;
}
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"] {
    display: none;
}
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] > div > div {
    gap: 2px;
}
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] label {
    width: 100%;
    padding: 10px 14px;
    border-radius: 8px;
    cursor: pointer;
    border-left: 3px solid transparent;
    transition: all 0.15s ease;
    margin-bottom: 2px;
    background: transparent;
    display: flex;
    align-items: center;
    min-height: 36px;
}
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(244, 114, 182, 0.08);
}
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: rgba(244, 114, 182, 0.15);
    border-left-color: #f472b6;
}
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {
    color: #ffffff !important;
    font-weight: 500;
}
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] label p {
    color: #cbd5e1 !important;
    font-size: 14px;
    margin: 0;
    padding: 0;
}
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
    display: none !important;
}
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {
    display: none;
}
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] label > div:last-child {
    width: 100%;
    padding: 0;
}

/* 渐变标题 */
.gradient-title {
    background: linear-gradient(90deg, #f472b6, #8b5cf6, #22d3ee);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 4px;
}

/* 输入框 */
.stApp .stTextInput > div > div > input {
    background-color: rgba(15, 23, 42, 0.7);
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 10px;
}
.stApp .stTextInput > div > div > input:focus {
    border-color: #f472b6;
    box-shadow: 0 0 0 2px rgba(244, 114, 182, 0.25);
}
.stApp .stTextInput label {
    color: #94a3b8;
}

/* 按钮：粉紫渐变 */
.stApp div.stButton > button {
    background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    padding: 8px 22px;
    transition: all 0.2s ease;
}
.stApp div.stButton > button:hover {
    background: linear-gradient(135deg, #f472b6 0%, #a78bfa 100%);
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(236, 72, 153, 0.35);
}

/* 区块小标题 */
.section-title {
    font-size: 14px;
    font-weight: 600;
    color: #f8fafc;
    letter-spacing: 0.5px;
    margin: 0 0 14px 0;
    padding-left: 10px;
    border-left: 3px solid #f472b6;
}

/* 指标卡片 */
.metric-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.5), rgba(15, 21, 36, 0.5));
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 12px;
    padding: 16px 18px;
    height: 100%;
    transition: all 0.2s ease;
}
.metric-card:hover {
    border-color: rgba(244, 114, 182, 0.3);
}
.metric-card .metric-label {
    color: #94a3b8;
    font-size: 12px;
    margin-bottom: 6px;
}
.metric-card .metric-value {
    color: #f1f5f9;
    font-size: 24px;
    font-weight: 700;
    word-break: break-all;
}
.metric-card .metric-sub {
    color: #64748b;
    font-size: 11px;
    margin-top: 4px;
}

/* 调度流程示意 */
.flow-wrap {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin: 6px 0 14px 0;
}
.flow-step {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 999px;
    padding: 5px 13px;
    font-size: 12px;
    color: #cbd5e1;
}
.flow-arrow {
    color: #64748b;
    font-size: 14px;
}

/* 时间线步骤 */
.timeline-step {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.4), rgba(15, 21, 36, 0.4));
    border-left: 3px solid var(--accent, #f472b6);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.timeline-step .ts-head {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}
.timeline-step .ts-idx {
    background: var(--accent, #f472b6);
    color: #0f172a;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
}
.timeline-step .ts-name {
    color: #f1f5f9;
    font-weight: 600;
    font-size: 14px;
}
.timeline-step .ts-status {
    margin-left: auto;
    font-size: 11px;
    color: #34d399;
    background: rgba(52, 211, 153, 0.12);
    border: 1px solid rgba(52, 211, 153, 0.3);
    border-radius: 999px;
    padding: 2px 10px;
}
.timeline-step .ts-time {
    color: #64748b;
    font-size: 11px;
    margin-left: 32px;
}

/* 日志块 */
.stApp pre {
    background: rgba(2, 6, 23, 0.75) !important;
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 10px;
}

/* 通用卡片容器 */
.stApp [data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(15, 23, 42, 0.4);
    border-color: rgba(148, 163, 184, 0.15) !important;
    border-radius: 12px;
}

/* expander */
.stApp details {
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 10px;
}

/* 提示框颜色适配 */
.stApp .stAlert {
    border-radius: 10px;
}

/* dataframe / table 深色 */
.stApp [data-testid="stTable"] table {
    background: rgba(15, 23, 42, 0.5);
}
.stApp [data-testid="stTable"] th {
    background: rgba(30, 41, 59, 0.6);
    color: #e2e8f0;
}
.stApp [data-testid="stTable"] td {
    color: #cbd5e1;
}

/* 分隔线 */
.stApp hr {
    border-color: rgba(148, 163, 184, 0.15);
}

/* 数据表格模块容器 */
.data-card {
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 14px;
}
.data-card .card-title {
    color: #f8fafc;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 10px;
}

/* 进度条容器 */
.split-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}
.split-bar .split-label {
    width: 60px;
    font-size: 13px;
    color: #cbd5e1;
}
.split-bar .split-track {
    flex: 1;
    height: 10px;
    background: rgba(30, 41, 59, 0.6);
    border-radius: 5px;
    overflow: hidden;
}
.split-bar .split-fill {
    height: 100%;
    border-radius: 5px;
    transition: width 0.3s ease;
}
.split-bar .split-count {
    width: 70px;
    text-align: right;
    font-size: 12px;
    color: #94a3b8;
}

</style>
"""

if __name__ == "__main__":
    st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# 工具函数：数据规范化
# --------------------------------------------------------------------------

def to_native(obj):
    """递归把 numpy 类型转成原生 Python 类型。Plotly Figure 原样返回。"""
    # Plotly Figure 对象不处理
    try:
        from plotly.graph_objects import Figure as PlotlyFigure
        if isinstance(obj, PlotlyFigure):
            return obj
    except ImportError:
        pass
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_native(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def flatten_quality(quality_statistics):
    """
    把嵌套的 quality_statistics 拍平成 DataFrame。

    结构:
        {
          "train": {
            "good": {"path": "...", "num_images": N, "quality_statistics": {...}},
            ...
          },
          ...
        }
    """
    rows = []
    if not isinstance(quality_statistics, dict):
        return pd.DataFrame()

    for split, cats in quality_statistics.items():
        if not isinstance(cats, dict):
            continue
        for cat, info in cats.items():
            if not isinstance(info, dict):
                continue
            qs = info.get("quality_statistics", {}) or {}
            rows.append({
                "split": split,
                "category": cat,
                "path": info.get("path", ""),
                "num_images": info.get("num_images", 0),
                "blur_score": round(qs.get("blur_score_mean", 0), 2),
                "brightness": round(qs.get("brightness_mean", 4), 4),
                "noise_score": round(qs.get("noise_score_mean", 2), 2),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 工具函数：UI 组件
# --------------------------------------------------------------------------

def gradient_title(text, sub=""):
    html = f'<div class="gradient-title">{text}</div>'
    if sub:
        html += f'<p style="color:#94a3b8;margin-top:0;margin-bottom:14px;font-size:13px;">{sub}</p>'
    st.markdown(html, unsafe_allow_html=True)


def section_title(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def metric_card(label, value, sub=""):
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def flow_html(steps):
    parts = []
    for i, s in enumerate(steps):
        color = TOOL_COLORS.get(s, TOOL_COLORS["unknown"])
        parts.append(
            f'<div class="flow-step" style="border-color:{color}55;color:{color};">{s}</div>'
        )
        if i < len(steps) - 1:
            parts.append('<div class="flow-arrow">→</div>')
    return f'<div class="flow-wrap">{"".join(parts)}</div>'


def parse_log(log_text):
    pattern = re.compile(r"\[([^\]]+)\]\s*\[([^\]]+)\]\s*(\w+)")
    paired = {}
    for line in log_text.splitlines():
        m = pattern.search(line)
        if m:
            time_str, tool, status = m.group(1), m.group(2), m.group(3)
            if tool not in paired:
                paired[tool] = {"start": None, "finished": None, "extra": []}
            if status == "start":
                paired[tool]["start"] = time_str
            elif status == "finished":
                paired[tool]["finished"] = time_str

    sub_pattern = re.compile(r"调用(YOLO|VOC|COCO)解析器")
    for line in log_text.splitlines():
        if sub_pattern.search(line):
            if "annotation_parser" not in paired:
                paired["annotation_parser"] = {"start": None, "finished": None, "extra": []}
            paired["annotation_parser"]["extra"].append(line.strip())

    ordered = []
    for t in TOOL_ORDER:
        if t in paired:
            ordered.append((t, paired[t]))
        else:
            ordered.append((t, {"start": None, "finished": None, "extra": []}))
    return ordered


def timeline_html(ordered_tools):
    if not ordered_tools:
        st.info("没有捕获到调度日志。")
        return
    for idx, (tool, times) in enumerate(ordered_tools, start=1):
        color = TOOL_COLORS.get(tool, TOOL_COLORS["unknown"])
        extra = times.get("extra", [])
        has_finished = times["finished"] is not None
        has_start = times["start"] is not None

        if has_finished:
            status_label, status_color = "✓ finished", "#34d399"
        elif has_start:
            status_label, status_color = "… running", "#fbbf24"
        elif extra:
            status_label, status_color = "✓ 已调度", "#34d399"
        else:
            status_label, status_color = "pending", "#94a3b8"

        time_line = ""
        if has_start:
            time_line = f"start: {times['start']}"
            if has_finished:
                time_line += f"  →  finished: {times['finished']}"
        if extra:
            time_line = (time_line + "  ·  " if time_line else "") + extra[0]

        st.markdown(
            f'<div class="timeline-step" style="--accent:{color};">'
            f'<div class="ts-head">'
            f'<span class="ts-idx">{idx}</span>'
            f'<span class="ts-name">{tool}</span>'
            f'<span class="ts-status" style="color:{status_color};'
            f'background:{status_color}1f;border-color:{status_color}55;">{status_label}</span>'
            f'</div>'
            f'<div class="ts-time">{time_line}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def split_bars(splits):
    """渲染数据划分的进度条。"""
    if not isinstance(splits, dict) or not splits:
        st.markdown("_无划分信息_")
        return

    total = sum(int(v) for v in splits.values() if isinstance(v, (int, float)))
    if total == 0:
        st.markdown("_无图片_")
        return

    colors = {
        "train": "#34d399",
        "val": "#fbbf24",
        "test": "#f472b6",
    }

    html_parts = []
    for k, v in splits.items():
        v_int = int(v) if isinstance(v, (int, float)) else 0
        pct = (v_int / total * 100) if total > 0 else 0
        color = colors.get(k, "#94a3b8")
        html_parts.append(
            f'<div class="split-bar">'
            f'<div class="split-label">{k}</div>'
            f'<div class="split-track">'
            f'<div class="split-fill" style="width:{pct:.1f}%;background:{color};"></div>'
            f'</div>'
            f'<div class="split-count">{v_int} 张 ({pct:.1f}%)</div>'
            f'</div>'
        )
    st.markdown("".join(html_parts), unsafe_allow_html=True)


# --------------------------------------------------------------------------
# 侧边栏导航
# --------------------------------------------------------------------------

def render_sidebar(result):
    """在侧边栏渲染导航菜单，返回当前选中的标签。"""
    with st.sidebar:
        st.markdown(
            '<div style="padding:4px 0 16px 0;">'
            '<div style="font-size:16px;font-weight:700;color:#f1f5f9;">🔬 Dataset Profiling</div>'
            '<div style="font-size:12px;color:#64748b;margin-top:2px;">规则型智能体 · 数据集画像</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        if result is None:
            st.info("运行 Agent 后可查看各模块结果")
            return "📊  数据集概览"

        if "active_nav" not in st.session_state:
            st.session_state["active_nav"] = NAV_ITEMS[0]

        active = st.session_state["active_nav"]

        selected = st.radio(
            "导航",
            NAV_ITEMS,
            index=NAV_ITEMS.index(active) if active in NAV_ITEMS else 0,
            label_visibility="collapsed",
            key="sidebar_radio",
        )
        st.session_state["active_nav"] = selected
        return selected


# --------------------------------------------------------------------------
# 各模块渲染
# --------------------------------------------------------------------------

def render_overview(result):
    """数据集概览模块。"""
    section_title("核心指标")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("数据集名称", result.get("dataset_name", "—"))
    with c2:
        metric_card("图片数量", result.get("image_count", 0), "total")
    with c3:
        ann = result.get("annotation_format") or []
        metric_card("标注格式", ", ".join(ann) if isinstance(ann, list) and ann else "—")
    with c4:
        exts = result.get("image_extensions") or []
        metric_card("图片格式", ", ".join(exts) if isinstance(exts, list) and exts else "—")

    # 数据集路径
    ds_path = result.get("dataset_path", "")
    if ds_path:
        st.markdown(
            f'<div style="background:rgba(15,23,42,0.4);border:1px solid rgba(148,163,184,0.12);'
            f'border-radius:8px;padding:8px 14px;margin:10px 0;font-size:13px;">'
            f'<span style="color:#94a3b8;">📂 数据集路径：</span>'
            f'<code style="color:#f472b6;background:transparent;">{ds_path}</code>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    left, right = st.columns([2, 1])

    with left:
        section_title("数据划分")
        split_bars(result.get("splits", {}))

    with right:
        section_title("目录信息")
        image_dirs = result.get("image_dirs", [])
        mask_dirs = result.get("mask_dirs", [])
        ann_files = result.get("annotation_files", [])
        st.markdown(
            f'- 📁 image_dirs: **{len(image_dirs)}** 个  \n'
            f'- 🎭 mask_dirs: **{len(mask_dirs)}** 个  \n'
            f'- 📝 annotation_files: **{len(ann_files)}** 个'
        )

    # 路径详情（可展开）
    if image_dirs or mask_dirs or ann_files:
        with st.expander("查看所有路径详情", expanded=False):
            if image_dirs:
                st.markdown("**📁 图片目录 (image_dirs)**")
                for d in image_dirs:
                    st.markdown(f"- `{d}`")
            if mask_dirs:
                st.markdown("**🎭 Mask 目录 (mask_dirs)**")
                for d in mask_dirs:
                    st.markdown(f"- `{d}`")
            if ann_files:
                st.markdown("**📝 标注文件 (annotation_files)**")
                for f in ann_files:
                    st.markdown(f"- `{f}`")

    st.markdown("")
    section_title("调度执行日志")
    log_text = st.session_state.get("last_log", "")
    ordered = parse_log(log_text)
    if ordered:
        timeline_html(ordered)
    else:
        st.info("未捕获到 tool_log 事件。")

    with st.expander("查看原始 stdout 日志", expanded=False):
        st.code(log_text if log_text.strip() else "(无输出)", language="text")


def render_annotation(result):
    """标注分析模块。"""
    class_dist = result.get("class_distribution")
    bbox_stats = result.get("bbox_statistics")
    small_ratio = result.get("small_object_ratio")
    ann_format = result.get("annotation_format")

    if not class_dist and not bbox_stats:
        st.info("当前数据集未包含有效的标注文件（或标注文件格式不支持）。\n\n"
                "支持 COCO (.json) / VOC (.xml) / YOLO (.txt) 三种格式。")
        return

    section_title("标注概览")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        fmt = ann_format if isinstance(ann_format, str) else (ann_format[0] if isinstance(ann_format, list) and ann_format else "—")
        metric_card("标注格式", fmt)
    with c2:
        total = bbox_stats.get("total_bbox", 0) if bbox_stats else 0
        metric_card("目标框总数", total)
    with c3:
        n_classes = len(class_dist) if isinstance(class_dist, dict) else 0
        metric_card("类别数量", n_classes)
    with c4:
        ratio_str = f"{small_ratio:.1%}" if isinstance(small_ratio, (int, float)) else "—"
        metric_card("小目标比例", ratio_str)

    st.markdown("")
    left, right = st.columns([3, 2])

    with left:
        section_title("类别分布")
        if isinstance(class_dist, dict) and class_dist:
            df = pd.DataFrame(
                [(k, v) for k, v in class_dist.items()],
                columns=["类别", "数量"]
            ).sort_values("数量", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.markdown("_无类别分布_")

    with right:
        section_title("目标框统计")
        if isinstance(bbox_stats, dict) and bbox_stats:
            st.markdown(
                f'- 总面积: **{bbox_stats.get("total_bbox", 0)}** 个  \n'
                f'- 平均面积: **{bbox_stats.get("mean_area", 0):.1f}**  \n'
                f'- 最大面积: **{bbox_stats.get("max_area", 0):.1f}**  \n'
                f'- 最小面积: **{bbox_stats.get("min_area", 0):.1f}**'
            )
        else:
            st.markdown("_无 bbox 统计_")

    st.markdown("")
    section_title("小目标比例")
    if isinstance(small_ratio, (int, float)):
        st.markdown(
            f"当前小目标占比: **{small_ratio:.1%}**  \n"
            f"（阈值定义：bbox 面积 < 平均面积 × 0.5）"
        )
    else:
        st.markdown("_无小目标比例数据_")


def render_quality(result):
    """图像质量模块。"""
    qs = result.get("quality_statistics", {})
    qs = to_native(qs) if qs else {}

    if not qs or not isinstance(qs, dict):
        st.info("无图像质量统计数据。")
        return

    df = flatten_quality(qs)
    if df.empty:
        st.info("图像质量数据为空。")
        return

    section_title("图像质量总览")
    total_images = int(df["num_images"].sum())
    avg_blur = round(float(df["blur_score"].mean()), 2)
    avg_bright = round(float(df["brightness"].mean()), 4)
    avg_noise = round(float(df["noise_score"].mean()), 2)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("参与评估图片", total_images)
    with c2:
        metric_card("平均模糊度", avg_blur, "Laplacian 方差 · 越高越清晰")
    with c3:
        metric_card("平均亮度", avg_bright, "0=全黑 · 1=全亮")
    with c4:
        metric_card("平均噪声", avg_noise, "高斯残差 std · 越低越干净")

    st.markdown("")
    section_title("按 split / 类别明细")

    splits = sorted(df["split"].unique())
    tabs = st.tabs([s for s in splits])

    for i, split_name in enumerate(splits):
        with tabs[i]:
            sub_df = df[df["split"] == split_name].copy()
            sub_df = sub_df.sort_values("num_images", ascending=False)
            sub_df = sub_df[["category", "num_images", "blur_score", "brightness", "noise_score", "path"]]
            sub_df.columns = ["类别", "图片数", "模糊度", "亮度", "噪声", "路径"]
            st.dataframe(sub_df, use_container_width=True, hide_index=True)

    st.markdown("")
    section_title("质量指标对比（按类别）")
    chart_df = df.copy()
    chart_df["label"] = chart_df["split"] + " / " + chart_df["category"]
    chart_df = chart_df.sort_values("num_images", ascending=False).head(15)

    metric_choice = st.selectbox(
        "选择指标",
        ["blur_score", "brightness", "noise_score"],
        format_func=lambda x: {
            "blur_score": "模糊度（越高越清晰）",
            "brightness": "亮度",
            "noise_score": "噪声（越低越干净）",
        }.get(x, x),
        key="quality_metric_select",
    )
    st.bar_chart(
        chart_df.set_index("label")[metric_choice],
        use_container_width=True,
        color="#f472b6",
    )


def flatten_image_analysis(image_analysis):
    """把 image_analysis 拍平成 DataFrame。"""
    rows = []
    if not isinstance(image_analysis, dict):
        return pd.DataFrame()

    for split, cats in image_analysis.items():
        if not isinstance(cats, dict):
            continue
        for cat, info in cats.items():
            if not isinstance(info, dict):
                continue
            sd = info.get("image_size_distribution", {}) or {}
            dr = info.get("defect_ratio", {}) or {}
            rows.append({
                "split": split,
                "category": cat,
                "num_images": info.get("num_images", 0),
                "width_mean": round(sd.get("width_mean", 0), 1),
                "height_mean": round(sd.get("height_mean", 0), 1),
                "width_min": sd.get("width_min", 0),
                "width_max": sd.get("width_max", 0),
                "height_min": sd.get("height_min", 0),
                "height_max": sd.get("height_max", 0),
                "defect_mean": round(dr.get("mean", 0.0), 4),
                "defect_min": round(dr.get("min", 0.0), 4),
                "defect_max": round(dr.get("max", 0.0), 4),
                "has_mask": dr.get("has_mask", False),
            })
    return pd.DataFrame(rows)


def render_image_analysis(result):
    """图像分析模块（尺寸分布 + 缺陷比例 + train/test 差异）。"""
    ia = result.get("image_analysis", {})
    ia = to_native(ia) if ia else {}

    if not ia or not isinstance(ia, dict):
        st.info("无图像分析数据。")
        return

    df = flatten_image_analysis(ia)
    if df.empty:
        st.info("图像分析数据为空。")
        return

    # ---- 总览 ----
    section_title("图像分析总览")
    total_images = int(df["num_images"].sum())
    avg_w = round(float(df["width_mean"].mean()), 1)
    avg_h = round(float(df["height_mean"].mean()), 1)
    defect_rows = df[df["has_mask"]]
    avg_defect = round(float(defect_rows["defect_mean"].mean()) * 100, 2) if not defect_rows.empty else 0.0
    max_defect = round(float(defect_rows["defect_max"].max()) * 100, 2) if not defect_rows.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("参与分析图片", total_images)
    with c2:
        metric_card("平均宽度", f"{avg_w}", "px")
    with c3:
        metric_card("平均高度", f"{avg_h}", "px")
    with c4:
        metric_card("平均缺陷占比", f"{avg_defect}%", f"最大 {max_defect}%")

    # ---- 按 split 明细 ----
    st.markdown("")
    section_title("按 split / 类别明细")

    splits = sorted(df["split"].unique())
    tabs = st.tabs([s for s in splits])

    for i, split_name in enumerate(splits):
        with tabs[i]:
            sub_df = df[df["split"] == split_name].copy()
            sub_df = sub_df.sort_values("num_images", ascending=False)
            display_df = sub_df[["category", "num_images", "width_mean", "height_mean",
                                "width_min", "width_max", "height_min", "height_max",
                                "defect_mean", "defect_min", "defect_max", "has_mask"]].copy()
            display_df.columns = ["类别", "图片数", "宽均值", "高均值",
                                  "宽最小", "宽最大", "高最小", "高最大",
                                  "缺陷均值", "缺陷最小", "缺陷最大", "有mask"]
            # 缺陷列转百分比显示
            for col in ["缺陷均值", "缺陷最小", "缺陷最大"]:
                display_df[col] = display_df[col].apply(lambda x: f"{x*100:.2f}%")
            display_df["有mask"] = display_df["有mask"].apply(lambda x: "✓" if x else "✗")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ---- 缺陷比例对比图 ----
    st.markdown("")
    section_title("缺陷区域比例对比（按类别）")
    if not defect_rows.empty:
        chart_df = defect_rows.copy()
        chart_df["label"] = chart_df["split"] + " / " + chart_df["category"]
        chart_df = chart_df.sort_values("defect_mean", ascending=False)
        st.bar_chart(
            chart_df.set_index("label")["defect_mean"],
            use_container_width=True,
            color="#fb923c",
        )
    else:
        st.markdown("_无缺陷 mask 数据_")

    # ---- train/test 分布差异 ----
    st.markdown("")
    section_title("train/test 分布差异")
    diff = result.get("distribution_difference", {})
    diff = to_native(diff) if diff else {}

    if diff:
        c1, c2, c3 = st.columns(3)
        with c1:
            w_diff = diff.get("width_mean_difference", 0)
            metric_card("宽度差异", f"{w_diff:.1f}", "px · |train - test|")
        with c2:
            h_diff = diff.get("height_mean_difference", 0)
            metric_card("高度差异", f"{h_diff:.1f}", "px · |train - test|")
        with c3:
            d_diff = diff.get("defect_ratio_difference", 0)
            metric_card("缺陷比例差异", f"{d_diff*100:.2f}%", "|train - test|")
    else:
        st.markdown("_无 train/test 差异数据_")

    # ---- 尺寸分布对比图 ----
    st.markdown("")
    section_title("图像尺寸分布（按类别）")
    chart_df2 = df.copy()
    chart_df2["label"] = chart_df2["split"] + " / " + chart_df2["category"]
    chart_df2 = chart_df2.sort_values("num_images", ascending=False).head(15)
    st.bar_chart(
        chart_df2.set_index("label")[["width_mean", "height_mean"]],
        use_container_width=True,
    )


def build_figure_from_spec(spec):
    """
    根据图表数据 spec 构建 Plotly Figure。

    如果 plotly 不可用，返回 None（由调用方降级到 Streamlit 原生图表）。
    """
    if not PLOTLY_AVAILABLE:
        return None

    if not spec or not isinstance(spec, dict):
        return None

    chart_type = spec.get("type", "")
    data = spec.get("data", {})
    title = spec.get("title", "")
    orientation = spec.get("orientation", "h")
    xaxis_title = spec.get("xaxis_title", "")

    if chart_type == "pie":
        labels = data.get("labels", [])
        values = data.get("values", [])
        colors = data.get("colors", [])

        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=colors) if colors else None,
                textinfo="label+percent",
                textposition="outside",
                hovertemplate="<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<extra></extra>",
                textfont=dict(size=12),
            )
        ])

        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=15)),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            margin=dict(l=20, r=20, t=50, b=60),
            height=400,
        )
        return fig

    if chart_type in ("bar", "bar_grouped"):
        labels = data.get("labels", [])
        series_list = data.get("series", [])
        customdata = data.get("customdata")
        customdata_labels = data.get("customdata_labels", [])
        value_suffix = data.get("value_suffix", "")

        if not labels or not series_list:
            return None

        fig = go.Figure()

        for series in series_list:
            name = series.get("name", "")
            values = series.get("values", [])
            color = series.get("color", "#94a3b8")

            hovertemplate = f"<b>%{{y}}</b><br>{name}: %{{x}}{value_suffix}<extra></extra>"

            bar_kwargs = dict(
                name=name,
                y=labels,
                x=values,
                orientation=orientation,
                marker_color=color,
                hovertemplate=hovertemplate,
            )

            # 只给第一个 series 挂 customdata（缺陷图用）
            if customdata and series == series_list[0]:
                cd = [list(cd_tuple) for cd_tuple in customdata]
                bar_kwargs["customdata"] = cd
                cd_lines = ""
                for i, lbl in enumerate(customdata_labels):
                    cd_lines += f"{lbl}: %{{customdata[{i}]}}{value_suffix}<br>"
                bar_kwargs["hovertemplate"] = (
                    f"<b>%{{y}}</b><br>{name}: %{{x}}{value_suffix}<br>{cd_lines}<extra></extra>"
                )

            fig.add_trace(go.Bar(**bar_kwargs))

        barmode = "group" if chart_type == "bar_grouped" else "relative"

        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=15)),
            barmode=barmode,
            xaxis_title=xaxis_title,
            yaxis=dict(autorange="reversed"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            margin=dict(l=20, r=20, t=50, b=60),
            height=max(350, len(labels) * 50 + 100),
        )
        return fig

    return None


def render_chart_native(spec):
    """
    降级方案：用 Streamlit 原生图表渲染（无需 plotly）。

    利用 st.bar_chart / st.dataframe 展示数据。
    """
    if not spec or not isinstance(spec, dict):
        st.warning("图表数据为空")
        return

    chart_type = spec.get("type", "")
    data = spec.get("data", {})
    title = spec.get("title", "")

    if chart_type == "pie":
        labels = data.get("labels", [])
        values = data.get("values", [])

        if not labels:
            st.markdown("_无数据_")
            return

        # 用 DataFrame + st.bar_chart 模拟饼图效果
        df = pd.DataFrame({"类别": labels, "数量": values})
        st.dataframe(df, use_container_width=True, hide_index=True)

        # 用 st.metric 展示每个值
        cols = st.columns(len(labels))
        for i, (label, val) in enumerate(zip(labels, values)):
            with cols[i]:
                st.metric(label, val)

    elif chart_type in ("bar", "bar_grouped"):
        labels = data.get("labels", [])
        series_list = data.get("series", [])

        if not labels or not series_list:
            st.markdown("_无数据_")
            return

        # 构建 DataFrame
        chart_data = {"类别": labels}
        for series in series_list:
            chart_data[series.get("name", "")] = series.get("values", [])

        df = pd.DataFrame(chart_data)

        # 用 st.bar_chart 渲染（Streamlit 原生交互式图表）
        st.bar_chart(df.set_index("类别"), use_container_width=True)

        # 同时展示数据表格（可看到具体数值）
        with st.expander("查看具体数值"):
            st.dataframe(df, use_container_width=True, hide_index=True)


def render_artifacts(result):
    """产物模块：交互式图表 + 样本预览 + Observations。"""
    artifacts = result.get("artifacts", {})

    if not artifacts or not isinstance(artifacts, dict):
        st.info("无产物信息。")
        return

    section_title("生成产物")

    pj = artifacts.get("profile_json")
    charts = artifacts.get("interactive_charts", [])
    sample_images = artifacts.get("sample_images", [])
    file_tree = artifacts.get("file_tree", {})

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Profile JSON", pj if pj else "—", "完整数据画像文件")
    with c2:
        metric_card("交互式图表", f"{len(charts)} 张", "Plotly 可交互")
    with c3:
        metric_card("样本图片", f"{len(sample_images)} 张", "随机抽样")

    # ==================
    # 交互式图表
    # ==================
    st.markdown("")
    section_title("交互式统计图表")

    if charts:
        if not PLOTLY_AVAILABLE:
            st.caption("⚠️ 未安装 plotly，使用 Streamlit 原生图表（交互性有限）。安装后效果更佳：`pip install plotly`")

        for item in charts:
            st.markdown(f"**{item.get('title', item.get('id', '图表'))}**")

            if PLOTLY_AVAILABLE:
                fig = build_figure_from_spec(item)
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("图表数据格式不支持")
            else:
                # 降级到 Streamlit 原生图表
                render_chart_native(item)

            st.markdown("")
    else:
        st.markdown("_无交互式图表_")

    # ==================
    # 样本预览
    # ==================
    section_title("样本预览（随机抽样）")

    if sample_images:
        show_mask = st.checkbox("叠加缺陷 mask（红色半透明）", value=True)

        n_cols = st.slider("每行显示数量", 2, 6, 4, key="sample_cols")

        cols = st.columns(n_cols)

        for i, sample in enumerate(sample_images):
            col = cols[i % n_cols]

            with col:
                st.caption(sample.get("title", ""))

                img_path = sample.get("image_path", "")

                if img_path and os.path.exists(img_path):
                    img = cv2.imdecode(
                        np.fromfile(img_path, dtype=np.uint8),
                        cv2.IMREAD_COLOR
                    )

                    if img is not None:
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                        if show_mask and sample.get("mask_path"):
                            mask_path = sample["mask_path"]

                            if os.path.exists(mask_path):
                                mask = cv2.imdecode(
                                    np.fromfile(mask_path, dtype=np.uint8),
                                    cv2.IMREAD_GRAYSCALE
                                )

                                if mask is not None:
                                    overlay = np.zeros_like(img_rgb)
                                    overlay[mask > 0] = [255, 0, 0]
                                    img_rgb = cv2.addWeighted(
                                        img_rgb, 1.0, overlay, 0.4, 0
                                    )

                        st.image(img_rgb, use_container_width=True)
                    else:
                        st.warning("加载失败")
                else:
                    st.warning(f"文件不存在: `{img_path}`")
    else:
        st.markdown("_无样本图片_")

    # ==================
    # Observations
    # ==================
    st.markdown("")
    section_title("Observations")
    obs = result.get("observations", [])
    if obs:
        for o in obs:
            st.markdown(f"- {o}")
    else:
        st.markdown("_无 observations_")


def render_image_browser(result):
    """图像浏览模块：文件浏览器 + 对比功能。"""
    artifacts = result.get("artifacts", {})

    if not artifacts or not isinstance(artifacts, dict):
        st.info("无产物信息。")
        return

    file_tree = artifacts.get("file_tree", {})

    if not file_tree or not file_tree.get("splits"):
        st.info("无文件树数据。")
        return

    dataset_name = file_tree.get("dataset_name", "dataset")
    splits = file_tree.get("splits", {})
    dataset_path = file_tree.get("dataset_path", "")

    st.markdown(f"**数据集**: {dataset_name}")

    # ==================
    # Tab: 文件浏览 / 对比
    # ==================
    tab_browse, tab_compare = st.tabs(["📁 文件浏览", "🔀 对比"])

    # ------------------
    # Tab 1: 文件浏览
    # ------------------
    with tab_browse:
        section_title("选择文件查看")

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            split_names = list(splits.keys())
            selected_split = st.selectbox(
                "Split",
                split_names,
                key="browse_split"
            )

        categories = splits.get(selected_split, {})
        category_names = list(categories.keys()) if categories else []

        with col2:
            selected_category = st.selectbox(
                "Category",
                category_names if category_names else ["(无)"],
                key="browse_category"
            )

        files = categories.get(selected_category, []) if categories else []

        with col3:
            selected_file = st.selectbox(
                "文件",
                files if files else ["(无)"],
                key="browse_file"
            )

        # 显示选中的文件
        if files and selected_file != "(无)":
            file_path = os.path.join(
                dataset_path, selected_split, selected_category, selected_file
            )

            st.markdown(f"**路径**: `{file_path}`")

            if os.path.exists(file_path):
                img = cv2.imdecode(
                    np.fromfile(file_path, dtype=np.uint8),
                    cv2.IMREAD_COLOR
                )

                if img is not None:
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                    # 尺寸信息
                    h, w = img.shape[:2]
                    st.caption(f"尺寸: {w} × {h} px · 通道: {img.shape[2] if len(img.shape) > 2 else 1}")

                    # mask 叠加选项
                    show_mask = st.checkbox(
                        "叠加缺陷 mask",
                        value=True,
                        key="browse_mask"
                    )

                    if show_mask:
                        mask_dir = os.path.join(
                            dataset_path, "ground_truth", selected_category
                        )

                        mask_name = os.path.splitext(selected_file)[0] + "_mask.png"
                        mask_path = os.path.join(mask_dir, mask_name)

                        if os.path.exists(mask_path):
                            mask = cv2.imdecode(
                                np.fromfile(mask_path, dtype=np.uint8),
                                cv2.IMREAD_GRAYSCALE
                            )

                            if mask is not None:
                                overlay = np.zeros_like(img_rgb)
                                overlay[mask > 0] = [255, 0, 0]

                                defect_pixels = cv2.countNonZero(mask)
                                total_pixels = mask.shape[0] * mask.shape[1]
                                ratio = defect_pixels / total_pixels * 100

                                img_rgb = cv2.addWeighted(
                                    img_rgb, 1.0, overlay, 0.4, 0
                                )

                                st.caption(
                                    f"缺陷像素: {defect_pixels} / {total_pixels} "
                                    f"({ratio:.2f}%)"
                                )

                                # 同时显示 mask
                                st.image(img_rgb, use_container_width=True)

                                with st.expander("查看原始 mask"):
                                    st.image(mask, use_container_width=True)
                            else:
                                st.image(img_rgb, use_container_width=True)
                        else:
                            st.image(img_rgb, use_container_width=True)
                            st.caption("该类别无对应 mask（正常样本）")
                    else:
                        st.image(img_rgb, use_container_width=True)
            else:
                st.warning(f"文件不存在: `{file_path}`")
        else:
            st.info("请选择一个文件查看")

    # ------------------
    # Tab 2: 对比
    # ------------------
    with tab_compare:
        section_title("选择文件进行对比")

        n_slots = st.slider("对比数量", 2, 4, 2, key="compare_count")

        slots = []

        for i in range(n_slots):
            with st.container():
                st.markdown(f"**槽位 {i+1}**")

                sc1, sc2, sc3 = st.columns([1, 1, 1])

                with sc1:
                    split_opts = list(splits.keys())
                    s_split = st.selectbox(
                        "Split",
                        split_opts,
                        key=f"cmp_split_{i}"
                    )

                cats = splits.get(s_split, {})
                cat_opts = list(cats.keys()) if cats else []

                with sc2:
                    s_cat = st.selectbox(
                        "Category",
                        cat_opts if cat_opts else ["(无)"],
                        key=f"cmp_cat_{i}"
                    )

                files_cmp = cats.get(s_cat, []) if cats else []

                with sc3:
                    s_file = st.selectbox(
                        "文件",
                        files_cmp if files_cmp else ["(无)"],
                        key=f"cmp_file_{i}"
                    )

                if files_cmp and s_file != "(无)":
                    fp = os.path.join(
                        dataset_path, s_split, s_cat, s_file
                    )
                    slots.append({
                        "title": f"{s_split}/{s_cat}/{s_file}",
                        "path": fp,
                    })

                st.markdown("")

        # 并排显示
        if len(slots) >= 2:
            section_title("对比结果")

            show_mask_cmp = st.checkbox(
                "叠加缺陷 mask",
                value=True,
                key="compare_mask"
            )

            cols = st.columns(len(slots))

            for i, slot in enumerate(slots):
                with cols[i]:
                    st.caption(slot["title"])

                    fp = slot["path"]

                    if os.path.exists(fp):
                        img = cv2.imdecode(
                            np.fromfile(fp, dtype=np.uint8),
                            cv2.IMREAD_COLOR
                        )

                        if img is not None:
                            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                            h, w = img.shape[:2]
                            st.caption(f"{w} × {h} px")

                            if show_mask_cmp:
                                # 推断 mask 路径
                                parts = slot["title"].split("/")
                                cat = parts[1] if len(parts) >= 2 else ""

                                mask_name = os.path.splitext(parts[-1])[0] + "_mask.png"
                                mask_path = os.path.join(
                                    dataset_path, "ground_truth", cat, mask_name
                                )

                                if os.path.exists(mask_path):
                                    mask = cv2.imdecode(
                                        np.fromfile(mask_path, dtype=np.uint8),
                                        cv2.IMREAD_GRAYSCALE
                                    )

                                    if mask is not None:
                                        overlay = np.zeros_like(img_rgb)
                                        overlay[mask > 0] = [255, 0, 0]

                                        defect_px = cv2.countNonZero(mask)
                                        total_px = mask.shape[0] * mask.shape[1]
                                        ratio = defect_px / total_px * 100

                                        img_rgb = cv2.addWeighted(
                                            img_rgb, 1.0, overlay, 0.4, 0
                                        )

                                        st.caption(f"缺陷占比: {ratio:.2f}%")

                            st.image(img_rgb, use_container_width=True)
                    else:
                        st.warning(f"不存在: `{fp}`")
        else:
            st.info("请至少选择 2 个文件进行对比")


def render_raw_json(result):
    """原始 JSON 模块。"""
    section_title("Agent.run 完整返回")
    native = to_native(result)
    st.json(native, expanded=True)


# --------------------------------------------------------------------------
# 页面主体
# --------------------------------------------------------------------------

if __name__ == "__main__":
    gradient_title(
        "Dataset Profiling Agent",
        "规则型智能体 · 调度 4 个 Tool 对数据集做画像",
    )

    st.markdown(flow_html(TOOL_ORDER), unsafe_allow_html=True)

    # 输入区
    cols = st.columns([4, 1])
    with cols[0]:
        dataset_path = st.text_input(
            "数据集路径（dataset_path）",
            value=DEFAULT_DATASET,
            help="默认指向项目内的 demo_dataset，开箱即跑",
        )
    with cols[1]:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        run_clicked = st.button("运行 Agent", use_container_width=True)

    # session_state 初始化
    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None
    if "last_log" not in st.session_state:
        st.session_state["last_log"] = ""
    if "last_error" not in st.session_state:
        st.session_state["last_error"] = None
    if "last_path" not in st.session_state:
        st.session_state["last_path"] = None
    if "active_nav" not in st.session_state:
        st.session_state["active_nav"] = "📊  数据集概览"


def run_agent(path):
    """
    分步执行 Agent 的 5 个 Tool，用 st.status 实时展示每步进度。

    步骤顺序与 agent.run() 一致：
        dataset_scan → annotation_parser → image_quality → opencv_image_analyzer → plot_generator
    """
    buf = io.StringIO()

    status_container = st.status("正在启动 Agent...", expanded=True)
    status_container.update(label="🚀 Agent 已启动，开始调度 5 个 Tool", state="running")

    try:
        # ---- 步骤 1/5: dataset_scan ----
        status_container.update(
            label="📋 步骤 1/5: 扫描数据集结构 (dataset_scan)",
            state="running",
        )
        st.write("🔍 正在遍历目录，统计图片与标注文件...")
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            scan_result = dataset_scan(path)
        dt = time.time() - t0
        n_img = scan_result.get("image_count", 0)
        n_ann = len(scan_result.get("annotation_files", []))
        splits = scan_result.get("splits", {})
        splits_str = " / ".join(f"{k}={v}" for k, v in splits.items()) if splits else "无划分"
        st.write(f"   ✓ 用时 {dt:.1f}s · 图片 **{n_img}** 张 · 标注文件 **{n_ann}** 个 · 划分: {splits_str}")

        # ---- 步骤 2/5: annotation_parser ----
        status_container.update(
            label="🏷️ 步骤 2/5: 解析标注文件 (annotation_parser)",
            state="running",
        )
        ann_files = scan_result.get("annotation_files", [])
        merged_class_distribution = {}
        merged_bbox = []
        merged_small_ratios = []
        annotation_format = None
        valid_count = 0

        if ann_files:
            st.write(f"🔍 正在解析 {len(ann_files)} 个候选标注文件...")
            t0 = time.time()
            with contextlib.redirect_stdout(buf):
                for ann_file in ann_files:
                    try:
                        ann_result = annotation_parser(ann_file)
                    except Exception:
                        continue
                    if not ann_result.get("is_valid", False):
                        continue
                    valid_count += 1
                    annotation_format = ann_result.get("annotation_format", annotation_format)
                    for cls, cnt in ann_result.get("class_distribution", {}).items():
                        merged_class_distribution[cls] = merged_class_distribution.get(cls, 0) + cnt
                    bbox_stats = ann_result.get("bbox_statistics", {})
                    cnt = bbox_stats.get("total_bbox", 0)
                    if cnt > 0:
                        merged_bbox.append((cnt, bbox_stats.get("mean_area", 0), bbox_stats.get("min_area", 0), bbox_stats.get("max_area", 0)))
                        ratio = ann_result.get("small_object_ratio", 0)
                        merged_small_ratios.append((ratio, cnt))
            dt = time.time() - t0

            if merged_bbox:
                total_bbox = sum(i[0] for i in merged_bbox)
                mean_area = sum(i[0] * i[1] for i in merged_bbox) / total_bbox
                min_area = min(i[2] for i in merged_bbox)
                max_area = max(i[3] for i in merged_bbox)
            else:
                total_bbox = mean_area = min_area = max_area = 0

            if merged_small_ratios:
                tc = sum(c for _, c in merged_small_ratios)
                small_obj_ratio = sum(r * c for r, c in merged_small_ratios) / tc
            else:
                small_obj_ratio = 0

            annotation_result = {
                "annotation_format": annotation_format,
                "annotation_file_count": len(ann_files),
                "valid_annotation_count": valid_count,
                "class_distribution": merged_class_distribution,
                "bbox_statistics": {"total_bbox": total_bbox, "mean_area": mean_area, "max_area": max_area, "min_area": min_area},
                "small_object_ratio": small_obj_ratio,
            }
            st.write(f"   ✓ 用时 {dt:.1f}s · 有效: **{valid_count}/{len(ann_files)}** · 格式: **{annotation_format or '—'}** · 类别: **{len(merged_class_distribution)}** · 目标框: **{total_bbox}**")
        else:
            st.write("   ⚠ 未找到标注文件，跳过此步骤")
            annotation_result = {}

        # ---- 步骤 3/5: image_quality ----
        status_container.update(
            label="🖼️ 步骤 3/5: 分析图像质量 (image_quality)",
            state="running",
        )
        st.write("🔍 正在逐张计算模糊度 / 亮度 / 噪声（这可能需要一些时间）...")
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            quality_result = image_quality(path)
        dt = time.time() - t0
        n_splits = len(quality_result.get("quality_statistics", {}))
        st.write(f"   ✓ 用时 {dt:.1f}s · 完成 **{n_splits}** 个数据划分的质量分析")

        # ---- 步骤 4/5: opencv_image_analyzer ----
        status_container.update(
            label="📐 步骤 4/5: 图像分析 (opencv_image_analyzer)",
            state="running",
        )
        st.write("🔍 正在分析图像尺寸 / 缺陷区域比例 / train-test 差异...")
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            image_analysis_result = opencv_image_analyzer(path)
        dt = time.time() - t0
        n_cat = sum(
            len(cats) for cats in image_analysis_result.get("image_analysis", {}).values()
        )
        has_diff = "distribution_difference" in image_analysis_result
        st.write(f"   ✓ 用时 {dt:.1f}s · 分析 **{n_cat}** 个类别 · 差异分析: {'✓' if has_diff else '✗'}")

        # ---- 步骤 5/5: plot_generator ----
        status_container.update(
            label="📊 步骤 5/5: 生成可视化产物 (plot_generator)",
            state="running",
        )
        st.write("🔍 正在生成图表与样本可视化...")
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            plot_result = plot_generator({
                "scan": scan_result,
                "quality": quality_result,
                "analysis": image_analysis_result,
            })
        dt = time.time() - t0
        n_plots = len(plot_result.get("artifacts", {}).get("interactive_charts", []))
        n_samples = len(plot_result.get("artifacts", {}).get("sample_images", []))
        st.write(f"   ✓ 用时 {dt:.1f}s · 生成 **{n_plots}** 张交互式图表 · **{n_samples}** 张样本图")

        # ---- 合并结果（与 agent.run() 行为一致）----
        result = {
            **scan_result,
            **annotation_result,
            **quality_result,
            **image_analysis_result,
            **plot_result,
            "observations": [
                "Most defects occupy less than 5% of image area.",
                "Texture categories show higher intra-class variation than object categories.",
            ],
        }

        status_container.update(
            label="✅ Agent 运行完成（5/5 步骤全部成功）",
            state="complete",
            expanded=False,
        )

        return to_native(result), buf.getvalue(), None

    except Exception as e:  # noqa: BLE001
        status_container.update(
            label=f"❌ 运行失败: {type(e).__name__}",
            state="error",
        )
        st.write(f"   ✗ 异常: {e}")
        return None, buf.getvalue(), f"{type(e).__name__}: {e}"


if __name__ == "__main__":
    if run_clicked:
        if not dataset_path or not os.path.isdir(dataset_path):
            st.session_state["last_error"] = f"路径不存在或不是目录：{dataset_path}"
            st.session_state["last_result"] = None
            st.session_state["last_log"] = ""
            st.session_state["last_path"] = dataset_path
        else:
            result, log_text, err = run_agent(dataset_path)
            st.session_state["last_result"] = result
            st.session_state["last_log"] = log_text
            st.session_state["last_error"] = err
            st.session_state["last_path"] = dataset_path
            st.session_state["active_nav"] = "📊  数据集概览"

    result = st.session_state["last_result"]
    error = st.session_state["last_error"]

    if error:
        st.error(f"运行失败：{error}")
        st.caption(
            "可能原因：目录结构不符合预期，或图像读取失败。"
            "建议使用默认的 demo_dataset。"
        )

    # 侧边栏导航
    active_nav = render_sidebar(result)

    # 主内容区
    st.markdown("---")

    if result is None and error is None:
        st.markdown(
            '<div style="margin-top:20px;color:#94a3b8;text-align:center;padding:40px 0;">'
            '<div style="font-size:18px;margin-bottom:8px;">👈 点击「运行 Agent」开始</div>'
            '<div style="font-size:13px;">'
            'Agent 会依次调度 dataset_scan → annotation_parser → image_quality → plot_generator'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    elif result is not None:
        if "数据集概览" in active_nav:
            render_overview(result)
        elif "标注分析" in active_nav:
            render_annotation(result)
        elif "图像质量" in active_nav:
            render_quality(result)
        elif "图像分析" in active_nav:
            render_image_analysis(result)
        elif "产物" in active_nav:
            render_artifacts(result)
        elif "图像浏览" in active_nav:
            render_image_browser(result)
        elif "原始 JSON" in active_nav:
            render_raw_json(result)
