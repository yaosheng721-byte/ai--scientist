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
            except Exception:
                continue

            if not ann_result.get("is_valid", False):
                continue

            valid_annotation_count += 1
            annotation_format = ann_result.get("annotation_format", annotation_format)

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

        annotation_result = {
            "annotation_format": annotation_format,
            "annotation_file_count": len(annotation_files),
            "valid_annotation_count": valid_annotation_count,
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

        observations = _generate_observations_safely({
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

        }


        return result


def _generate_observations_safely(profile_data: dict) -> list[str]:
    """调用 LLM 生成 observations，失败时回退到默认观察。"""
    try:
        observations = generate_observations(profile_data)
        if observations:
            return observations
    except Exception as e:
        # LLM 调用失败（API Key 未配置 / 网络错误 / 限流等），回退到默认观察
        pass

    # 默认观察（LLM 不可用时兜底）
    return [
        "⚠️ LLM 观察生成失败，以下为默认观察",
        "建议检查 .env 中的 DASHSCOPE_API_KEY 是否已配置",
        f"数据集路径：{profile_data.get('scan', {}).get('dataset_path', '未知')}",
    ]
