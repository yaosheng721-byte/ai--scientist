import os

from app.agents.dataset_profiling_agent.agent.base_agent import BaseAgent
from app.agents.dataset_profiling_agent.tools.annotation_parser import annotation_parser
from app.agents.dataset_profiling_agent.tools.dataset_scan import dataset_scan
from app.agents.dataset_profiling_agent.tools.image_quality import image_quality
from app.agents.dataset_profiling_agent.tools.opencv_image_analyzer import opencv_image_analyzer
from app.agents.dataset_profiling_agent.tools.plot_generator import plot_generator
from app.core.llm import generate_observations



class DatasetProfilingAgent(BaseAgent):

    def run(self, input_data, progress_callback=None):

        def report(progress, node, message):
            if progress_callback:
                progress_callback(progress, node, message)

        dataset_path = input_data["dataset_path"]

        report(5, "initializing", "正在初始化数据画像任务")

        scan_result = dataset_scan(
            dataset_path
        )
        report(15, "dataset_scan", "数据集目录扫描完成")

        # 遍历所有标注文件，跳过无效文件（如 README.json）
        annotation_files = scan_result.get("annotation_files", [])

        merged_class_distribution = {}
        merged_bbox = []          # [(count, mean, min, max), ...]
        merged_small_ratios = []  # [(ratio, count), ...]
        annotation_format = None
        valid_annotation_count = 0
        annotation_errors = []
        annotation_warning_groups = {}
        annotation_formats = set()

        annotation_total = len(annotation_files)
        for index, ann_file in enumerate(annotation_files):
            if annotation_total:
                annotation_progress = 15 + int(index / annotation_total * 15)
                report(
                    annotation_progress,
                    "annotation_parsing",
                    f"正在解析标注文件（{index + 1}/{annotation_total}）",
                )

            try:
                ann_result = annotation_parser(ann_file)
            except Exception as exc:
                annotation_errors.append({
                    "file": ann_file,
                    "format": _format_from_extension(ann_file),
                    "error": f"解析时发生异常：{type(exc).__name__}: {exc}",
                })
                continue

            if not ann_result.get("is_valid", False):
                annotation_errors.append({
                    "file": ann_file,
                    "format": ann_result.get("annotation_format", _format_from_extension(ann_file)),
                    "error": ann_result.get("error", "文件内容未通过格式校验"),
                })
                continue

            valid_annotation_count += 1
            parsed_format = ann_result.get("annotation_format")
            if parsed_format:
                annotation_formats.add(parsed_format)
            if ann_result.get("warning"):
                warning = ann_result["warning"]
                group = annotation_warning_groups.setdefault(warning, {"warning": warning, "count": 0, "files": []})
                group["count"] += 1
                if len(group["files"]) < 3:
                    group["files"].append(os.path.basename(ann_file))

            # 合并类别分布
            for cls, cnt in ann_result.get("class_distribution", {}).items():
                merged_class_distribution[cls] = (
                    merged_class_distribution.get(cls, 0) + cnt
                )

            # 合并 bbox 统计
            bbox_stats = ann_result.get("bbox_statistics", {})
            count = bbox_stats.get("total_bbox", 0)
            if count > 0:
                merged_bbox.append((
                    count,
                    bbox_stats.get("mean_area", 0),
                    bbox_stats.get("min_area", 0),
                    bbox_stats.get("max_area", 0),
                ))

            # 合并小目标比例（加权用）
            ratio = ann_result.get("small_object_ratio", 0)
            if count > 0:
                merged_small_ratios.append((ratio, count))

        report(30, "annotation_parsing", "标注信息解析完成")

        # 汇总 bbox
        if merged_bbox:
            total_bbox = sum(item[0] for item in merged_bbox)
            weighted_sum = sum(item[0] * item[1] for item in merged_bbox)
            mean_area = weighted_sum / total_bbox if total_bbox > 0 else 0
            min_area = min(item[2] for item in merged_bbox)
            max_area = max(item[3] for item in merged_bbox)
        else:
            total_bbox = 0
            mean_area = 0
            min_area = 0
            max_area = 0

        # 汇总小目标比例（按 bbox 数量加权）
        if merged_small_ratios:
            total_count = sum(c for _, c in merged_small_ratios)
            small_object_ratio = sum(r * c for r, c in merged_small_ratios) / total_count
        else:
            small_object_ratio = 0

        annotation_format = sorted(annotation_formats) or None
        annotation_result = {
            "annotation_format": annotation_format,
            "annotation_file_count": len(annotation_files),
            "valid_annotation_count": valid_annotation_count,
            "invalid_annotation_count": len(annotation_errors),
            "annotation_errors": annotation_errors,
            "annotation_warnings": list(annotation_warning_groups.values()),
            "class_distribution": merged_class_distribution,
            "bbox_statistics": {
                "total_bbox": total_bbox,
                "mean_area": mean_area,
                "max_area": max_area,
                "min_area": min_area,
            },
            "small_object_ratio": small_object_ratio,
        }

        quality_result = image_quality(
            dataset_path
        )
        report(50, "image_quality", "图像质量分析完成")

        image_analysis_result = opencv_image_analyzer(
            dataset_path
        )
        report(72, "image_analysis", "图像特征分析完成")

        plot_result = plot_generator({
            "scan": scan_result,
            "quality": quality_result,
            "analysis": image_analysis_result,
        })
        report(88, "plot_generation", "数据画像图表生成完成")

        observations, observation_warning = _generate_observations_safely({
            "scan": scan_result,
            "annotation": annotation_result,
            "quality": quality_result,
            "image_analysis": image_analysis_result,
        })
        report(96, "observation_generation", "数据观察结论生成完成")


        result = {

            **scan_result,

            **annotation_result,

            **quality_result,

            **image_analysis_result,

            **plot_result,

            "observations": observations,
            "observation_warning": observation_warning,

        }


        return result


def _format_from_extension(path: str) -> str:
    return {".json": "COCO?", ".xml": "VOC?", ".txt": "YOLO?"}.get(os.path.splitext(path)[1].lower(), "未知")


def _generate_observations_safely(profile_data: dict) -> tuple[list[str], str | None]:
    """调用 LLM 生成 observations，失败时回退到默认观察。"""
    try:
        observations = generate_observations(profile_data)
        if observations:
            return observations, None
    except Exception as e:
        # LLM 调用失败（API Key 未配置 / 网络错误 / 限流等），回退到默认观察
        print(f"[dataset_profiling] LLM observation generation failed: {type(e).__name__}: {e}")
        warning = f"AI 观察生成失败，已使用默认结论（{type(e).__name__}）"
    else:
        warning = "AI 观察生成没有返回内容，已使用默认结论"

    # 默认观察（LLM 不可用时兜底）
    return [
        "⚠️ LLM 观察生成失败，以下为默认观察",
        "建议检查 .env 中的 DASHSCOPE_API_KEY 是否已配置",
        f"数据集路径：{profile_data.get('scan', {}).get('dataset_path', '未知')}",
    ], warning
