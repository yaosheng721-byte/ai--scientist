import json


def parse_coco(annotation_path):
    """
    COCO annotation parser

    参数:
        annotation_path:
            COCO json 路径

    返回:
        annotation 统计信息

    验证逻辑:
        读取 JSON 后检查是否包含 COCO 必需字段
        （images / annotations / categories）。
        如果不是有效的 COCO 文件，返回 is_valid=False。
    """

    # 1. 读取 json
    try:
        with open(
            annotation_path,
            "r",
            encoding="utf-8"
        ) as f:
            coco_data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {
            "annotation_format": "COCO",
            "is_valid": False,
            "error": "文件不是有效的 JSON",
        }

    # 2. 验证 COCO 必需字段
    if not isinstance(coco_data, dict):
        return {
            "annotation_format": "COCO",
            "is_valid": False,
            "error": "JSON 顶层不是 dict",
        }

    required_keys = {"images", "annotations", "categories"}
    missing = required_keys - set(coco_data.keys())

    if missing:
        return {
            "annotation_format": "COCO",
            "is_valid": False,
            "error": f"缺少 COCO 必需字段: {missing}",
        }

    # 3. 类别映射
    category_map = {}

    for category in coco_data["categories"]:
        category_map[
            category["id"]
        ] = category["name"]

    # 4. 统计类别数量
    class_distribution = {}

    for ann in coco_data["annotations"]:
        category_id = ann["category_id"]
        class_name = category_map.get(
            category_id,
            "unknown"
        )
        if class_name not in class_distribution:
            class_distribution[class_name] = 0
        class_distribution[class_name] += 1

    # 5. bbox 统计
    areas = []

    for ann in coco_data["annotations"]:
        bbox = ann["bbox"]
        width = bbox[2]
        height = bbox[3]
        area = width * height
        areas.append(area)

    if len(areas) > 0:
        total_bbox = len(areas)
        mean_area = sum(areas) / len(areas)
        max_area = max(areas)
        min_area = min(areas)
    else:
        total_bbox = 0
        mean_area = 0
        max_area = 0
        min_area = 0

    # 6. 小目标比例
    # COCO 标准: area < 32*32 = 1024
    COCO_SMALL_THRESHOLD = 32 * 32  # 1024

    if areas:
        small_objects = [
            a for a in areas
            if a < COCO_SMALL_THRESHOLD
        ]
        small_object_ratio = (
            len(small_objects) / len(areas)
        )
    else:
        small_object_ratio = 0

    result = {
        "annotation_format": "COCO",
        "is_valid": True,
        "class_distribution": class_distribution,
        "bbox_statistics": {
            "total_bbox": total_bbox,
            "mean_area": mean_area,
            "max_area": max_area,
            "min_area": min_area,
        },
        "small_object_ratio": small_object_ratio,
    }

    return result
