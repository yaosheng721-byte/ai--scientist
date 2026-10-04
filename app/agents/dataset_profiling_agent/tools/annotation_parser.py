"""
Annotation Parser Tool

作用：
    解析数据集标注文件(COCO/VOC/YOLO)

当前阶段：
    使用模拟数据，验证 Agent 调用流程和输出格式

后续实现：
    1. 自动识别标注格式
    2. COCO json解析
    3. VOC xml解析
    4. YOLO txt解析
"""

from pathlib import Path

from app.agents.dataset_profiling_agent.tools.annotation.coco_parser import parse_coco
from app.agents.dataset_profiling_agent.tools.annotation.voc_parser import parse_voc
from app.agents.dataset_profiling_agent.tools.annotation.yolo_parser import parse_yolo


def detect_annotation_format(annotation_path):
    """
    自动判断标注格式

    返回:
        coco / voc / yolo
    """

    path = Path(annotation_path)


    if path.suffix == ".json":
        return "COCO"


    elif path.suffix == ".xml":
        return "VOC"


    elif path.suffix == ".txt":
        return "YOLO"


    else:
        raise ValueError(
            "Unknown annotation format"
        )

def annotation_parser(annotation_path):
    """
    Annotation Parser Tool

    参数:
        annotation_path:
            标注文件路径

    输出:
        annotation statistics
    """

    annotation_format = detect_annotation_format(
        annotation_path
    )

    if annotation_format == "COCO":
        result = parse_coco(
            annotation_path
        )

    elif annotation_format == "VOC":

        result = parse_voc(
            annotation_path
        )

    elif annotation_format == "YOLO":

        result = parse_yolo(
            annotation_path
        )

    # result = {
    #
    #     "annotation_format": "COCO",
    #
    #     "class_distribution": {
    #         "defect_a": 120,
    #         "defect_b": 80,
    #         "defect_c": 50
    #     },
    #
    #
    #     "bbox_statistics": {
    #
    #         "total_bbox": 250,
    #
    #         "mean_area": 1350,
    #
    #         "max_area": 8500,
    #
    #         "min_area": 100
    #
    #     },
    #
    #
    #     "small_object_ratio": 0.35
    #
    # }


    return result


if __name__ == "__main__":
    annotation_path = "test.json"


    result = annotation_parser(
        annotation_path
    )


    print(result)
