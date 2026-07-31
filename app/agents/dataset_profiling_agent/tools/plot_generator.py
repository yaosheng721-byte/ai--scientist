"""
Plot Generator Tool

作用：
    生成数据集可视化图表数据与样本预览数据。

功能：
    1. 数据划分饼图数据
    2. 图像尺寸分布横向条形图数据
    3. 缺陷区域比例对比横向条形图数据
    4. 图像质量统计横向条形图数据
    5. 样本图片数据（供 app.py 渲染网格）
    6. 文件树（供 app.py 做文件浏览器和对比功能）

设计原则：
    - 不返回 Plotly Figure 对象，只返回 JSON 可序列化的图表数据
    - 由 app.py 在渲染时根据数据构建 Figure（避免 session_state 序列化问题）
    - 所有条形图横向放置，字段名称不旋转 90°
    - 标题格式：数据集名 / 部分

输入：
    profile_data:
        {
            "scan": scan_result,
            "quality": quality_result,
            "analysis": image_analysis_result,
        }

输出：
    {
        "artifacts": {
            "profile_json": "outputs/dataset_profile.json",
            "interactive_charts": [
                {
                    "id": "split_distribution",
                    "title": "bottle / 数据划分",
                    "type": "pie",
                    "data": {"labels": [...], "values": [...], "colors": [...]}
                },
                {
                    "id": "image_size_distribution",
                    "title": "bottle / 图像尺寸分布",
                    "type": "bar_grouped",
                    "orientation": "h",
                    "xaxis_title": "像素 (px)",
                    "data": {
                        "labels": [...],
                        "series": [{"name": "宽度", "values": [...], "color": "#22d3ee"}, ...]
                    }
                },
                ...
            ],
            "sample_images": [{"title": "train/good", "image_path": "...", "mask_path": null}, ...],
            "file_tree": {"dataset_name": "bottle", "dataset_path": "...", "splits": {...}}
        }
    }
"""

import os
import json
import random

from pathlib import Path

import numpy as np

from app.agents.dataset_profiling_agent.logs.tool_logger import tool_log


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")



def _ensure_output_dir():
    """确保输出目录存在。"""

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )



def build_split_chart_data(splits, dataset_name):
    """
    数据划分饼图数据

    返回 JSON 可序列化的 dict。
    """

    if not splits:
        return None

    labels = []
    values = []

    color_map = {
        "train": "#34d399",
        "test": "#f472b6",
        "val": "#fbbf24",
    }

    colors = []

    for k, v in splits.items():

        if not isinstance(v, (int, float)) or v == 0:
            continue

        labels.append(str(k))
        values.append(int(v))
        colors.append(color_map.get(k, "#94a3b8"))

    if not values:
        return None

    return {
        "id": "split_distribution",
        "title": f"{dataset_name} / 数据划分",
        "type": "pie",
        "data": {
            "labels": labels,
            "values": values,
            "colors": colors,
        },
    }



def build_image_size_chart_data(image_analysis, dataset_name):
    """
    图像尺寸分布横向条形图数据

    返回 JSON 可序列化的 dict。
    """

    if not image_analysis or not isinstance(image_analysis, dict):
        return None

    labels = []
    width_means = []
    height_means = []

    for split, cats in image_analysis.items():

        if not isinstance(cats, dict):
            continue

        for cat, info in cats.items():

            if not isinstance(info, dict):
                continue

            sd = info.get("image_size_distribution", {})

            if not sd:
                continue

            labels.append(f"{split}/{cat}")
            width_means.append(round(float(sd.get("width_mean", 0)), 1))
            height_means.append(round(float(sd.get("height_mean", 0)), 1))

    if not labels:
        return None

    return {
        "id": "image_size_distribution",
        "title": f"{dataset_name} / 图像尺寸分布",
        "type": "bar_grouped",
        "orientation": "h",
        "xaxis_title": "像素 (px)",
        "data": {
            "labels": labels,
            "series": [
                {"name": "宽度", "values": width_means, "color": "#22d3ee"},
                {"name": "高度", "values": height_means, "color": "#f472b6"},
            ],
        },
    }



def build_defect_ratio_chart_data(image_analysis, dataset_name):
    """
    缺陷区域比例对比横向条形图数据

    只展示有 mask 的 category。
    """

    if not image_analysis or not isinstance(image_analysis, dict):
        return None

    labels = []
    means = []
    mins = []
    maxs = []

    for split, cats in image_analysis.items():

        if not isinstance(cats, dict):
            continue

        for cat, info in cats.items():

            if not isinstance(info, dict):
                continue

            dr = info.get("defect_ratio", {})

            if not dr or not dr.get("has_mask", False):
                continue

            labels.append(f"{split}/{cat}")
            means.append(round(float(dr.get("mean", 0)) * 100, 2))
            mins.append(round(float(dr.get("min", 0)) * 100, 2))
            maxs.append(round(float(dr.get("max", 0)) * 100, 2))

    if not labels:
        return None

    return {
        "id": "defect_ratio_comparison",
        "title": f"{dataset_name} / 缺陷区域比例",
        "type": "bar",
        "orientation": "h",
        "xaxis_title": "缺陷占比 (%)",
        "data": {
            "labels": labels,
            "series": [
                {"name": "均值", "values": means, "color": "#fb923c"},
            ],
            "customdata": list(zip(mins, maxs)),
            "customdata_labels": ["最小", "最大"],
            "value_suffix": "%",
        },
    }



def build_quality_chart_data(quality_statistics, dataset_name):
    """
    图像质量统计横向条形图数据

    三个维度分别返回独立的 chart spec：
      - 模糊度
      - 亮度
      - 噪声

    返回 list（可能包含 0~3 个 chart spec）。
    """

    if not quality_statistics or not isinstance(quality_statistics, dict):
        return []

    labels = []
    blur_means = []
    brightness_means = []
    noise_means = []

    for split, cats in quality_statistics.items():

        if not isinstance(cats, dict):
            continue

        for cat, info in cats.items():

            if not isinstance(info, dict):
                continue

            qs = info.get("quality_statistics", {})

            if not qs:
                continue

            labels.append(f"{split}/{cat}")
            blur_means.append(round(float(qs.get("blur_score_mean", 0)), 2))
            brightness_means.append(round(float(qs.get("brightness_mean", 0)), 4))
            noise_means.append(round(float(qs.get("noise_score_mean", 0)), 4))

    if not labels:
        return []

    charts = []

    # 模糊度
    charts.append({
        "id": "quality_blur",
        "title": f"{dataset_name} / 图像质量 - 模糊度",
        "type": "bar",
        "orientation": "h",
        "xaxis_title": "模糊度 (Laplacian 方差，越大越清晰)",
        "data": {
            "labels": labels,
            "series": [
                {"name": "模糊度", "values": blur_means, "color": "#a78bfa"},
            ],
        },
    })

    # 亮度
    charts.append({
        "id": "quality_brightness",
        "title": f"{dataset_name} / 图像质量 - 亮度",
        "type": "bar",
        "orientation": "h",
        "xaxis_title": "亮度 (灰度均值 / 255，越低越暗)",
        "data": {
            "labels": labels,
            "series": [
                {"name": "亮度", "values": brightness_means, "color": "#fbbf24"},
            ],
        },
    })

    # 噪声
    charts.append({
        "id": "quality_noise",
        "title": f"{dataset_name} / 图像质量 - 噪声",
        "type": "bar",
        "orientation": "h",
        "xaxis_title": "噪声 (残差标准差，越大噪声越多)",
        "data": {
            "labels": labels,
            "series": [
                {"name": "噪声", "values": noise_means, "color": "#60a5fa"},
            ],
        },
    })

    return charts



def collect_sample_images(scan_result):
    """
    收集样本图片

    每个 split/category 随机抽 1 张图。
    如果有对应的 mask，记录 mask 路径。
    """

    dataset_path = scan_result.get("dataset_path", "")

    if not dataset_path or not os.path.isdir(dataset_path):
        return []

    dataset_path = Path(dataset_path)

    image_suffix = {".jpg", ".jpeg", ".png", ".bmp"}

    samples = []

    for split_dir in dataset_path.iterdir():

        if not split_dir.is_dir():
            continue

        if split_dir.name == "ground_truth":
            continue

        if split_dir.name not in ("train", "test", "val"):
            continue

        split_name = split_dir.name

        for category_dir in split_dir.iterdir():

            if not category_dir.is_dir():
                continue

            category_name = category_dir.name

            images = [
                f for f in category_dir.iterdir()
                if f.is_file() and f.suffix.lower() in image_suffix
            ]

            if not images:
                continue

            chosen = random.choice(images)

            mask_dir = (
                category_dir.parent.parent
                / "ground_truth"
                / category_name
            )

            mask_path = None

            if mask_dir.is_dir():

                mask_name = chosen.stem + "_mask.png"

                candidate = mask_dir / mask_name

                if candidate.exists():
                    mask_path = str(candidate)

            samples.append({
                "title": f"{split_name}/{category_name}",
                "image_path": str(chosen),
                "mask_path": mask_path,
            })

    return samples



def build_file_tree(scan_result):
    """
    构建文件树

    扫描数据集目录，构建:
    {
        "dataset_name": "bottle",
        "dataset_path": "...",
        "splits": {
            "train": {"good": ["000.png", "001.png", ...]},
            "test": {"broken_large": [...], ...}
        }
    }
    """

    dataset_path = scan_result.get("dataset_path", "")

    if not dataset_path or not os.path.isdir(dataset_path):
        return {}

    dataset_path = Path(dataset_path)

    dataset_name = scan_result.get("dataset_name", dataset_path.name)

    image_suffix = {".jpg", ".jpeg", ".png", ".bmp"}

    tree = {
        "dataset_name": dataset_name,
        "dataset_path": str(dataset_path),
        "splits": {}
    }

    for split_dir in dataset_path.iterdir():

        if not split_dir.is_dir():
            continue

        if split_dir.name == "ground_truth":
            continue

        if split_dir.name not in ("train", "test", "val"):
            continue

        split_name = split_dir.name

        tree["splits"][split_name] = {}

        for category_dir in split_dir.iterdir():

            if not category_dir.is_dir():
                continue

            category_name = category_dir.name

            files = sorted([
                f.name for f in category_dir.iterdir()
                if f.is_file() and f.suffix.lower() in image_suffix
            ])

            if files:
                tree["splits"][split_name][category_name] = files

    return tree



def plot_generator(profile_data):
    """
    Plot Generator Tool 入口函数

    返回 JSON 可序列化的图表数据（不含 Plotly Figure 对象）。
    由 app.py 在渲染时根据数据构建 Figure。
    """

    tool_log(
        "plot_generator",
        "start"
    )

    _ensure_output_dir()

    scan = profile_data.get("scan", {})
    quality = profile_data.get("quality", {})
    analysis = profile_data.get("analysis", {})

    dataset_name = scan.get("dataset_name", "")

    if not dataset_name:
        dataset_path = scan.get("dataset_path", "")
        dataset_name = os.path.basename(dataset_path) if dataset_path else "dataset"

    interactive_charts = []

    # ==================
    # 1. 数据划分饼图
    # ==================

    chart_split = build_split_chart_data(
        scan.get("splits", {}),
        dataset_name
    )

    if chart_split:
        interactive_charts.append(chart_split)

    # ==================
    # 2. 图像尺寸分布
    # ==================

    chart_size = build_image_size_chart_data(
        analysis.get("image_analysis", {}),
        dataset_name
    )

    if chart_size:
        interactive_charts.append(chart_size)

    # ==================
    # 3. 缺陷比例对比
    # ==================

    chart_defect = build_defect_ratio_chart_data(
        analysis.get("image_analysis", {}),
        dataset_name
    )

    if chart_defect:
        interactive_charts.append(chart_defect)

    # ==================
    # 4. 图像质量统计（三个维度分开）
    # ==================

    quality_charts = build_quality_chart_data(
        quality.get("quality_statistics", {}),
        dataset_name
    )

    for qc in quality_charts:
        interactive_charts.append(qc)

    # ==================
    # 5. 样本图片
    # ==================

    sample_images = collect_sample_images(scan)

    # ==================
    # 6. 文件树
    # ==================

    file_tree = build_file_tree(scan)

    # ==================
    # 7. 保存 profile JSON
    # ==================

    profile_json_path = os.path.join(OUTPUT_DIR, "dataset_profile.json")

    try:

        profile_summary = {
            "dataset_name": scan.get("dataset_name", ""),
            "dataset_path": scan.get("dataset_path", ""),
            "image_count": scan.get("image_count", 0),
            "splits": scan.get("splits", {}),
            "annotation_format": scan.get("annotation_format", []),
            "image_extensions": scan.get("image_extensions", []),
            "quality_statistics": quality.get("quality_statistics", {}),
            "image_analysis": analysis.get("image_analysis", {}),
            "distribution_difference": analysis.get("distribution_difference", {}),
            "file_tree": file_tree,
        }

        with open(profile_json_path, "w", encoding="utf-8") as f:
            json.dump(
                profile_summary,
                f,
                indent=4,
                ensure_ascii=False,
                default=lambda x: float(x)
                    if isinstance(x, (np.floating, np.integer))
                    else str(x)
            )

    except Exception:
        pass

    result = {
        "artifacts": {
            "profile_json": profile_json_path,
            "interactive_charts": interactive_charts,
            "sample_images": sample_images,
            "file_tree": file_tree,
        }
    }

    tool_log(
        "plot_generator",
        "finished"
    )

    return result
