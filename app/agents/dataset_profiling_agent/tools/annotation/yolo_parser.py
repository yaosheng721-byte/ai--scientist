"""
YOLO Annotation Parser

验证逻辑:
    读取 TXT 后检查每行是否为 "class_id x_center y_center width height"。
    如果不是有效的 YOLO 文件，返回 is_valid=False。

输出格式与 coco_parser 一致:
    {
        "annotation_format": "YOLO",
        "is_valid": True/False,
        "class_distribution": {...},
        "bbox_statistics": {...},
        "small_object_ratio": float
    }

注意:
    YOLO 格式一个 TXT 文件对应一张图片，
    bbox 坐标是归一化的（0~1，相对于图片宽高），
    面积也是归一化的（0~1）。
    Agent 层应遍历所有 TXT 文件汇总。
"""

import os


def parse_yolo(annotation_path):
    """
    YOLO annotation parser

    参数:
        annotation_path:
            YOLO txt 路径

    返回:
        annotation 统计信息
    """

    # 1. 读取 TXT
    try:
        with open(
            annotation_path,
            "r",
            encoding="utf-8"
        ) as f:
            lines = f.readlines()
    except (UnicodeDecodeError, OSError):
        return {
            "annotation_format": "YOLO",
            "is_valid": False,
            "error": "无法读取文件",
        }

    # 2. 验证 YOLO 格式
    # 每行格式: class_id x_center y_center width height
    # 所有值都是数字
    valid_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 5:
            # 可能不是 YOLO 标注文件（如 README.txt）
            return {
                "annotation_format": "YOLO",
                "is_valid": False,
                "error": "文件内容不是 YOLO 格式（每行至少需要 5 个数字）",
            }
        try:
            class_id = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])
            valid_lines.append((class_id, x, y, w, h))
        except ValueError:
            return {
                "annotation_format": "YOLO",
                "is_valid": False,
                "error": "文件内容不是 YOLO 格式（包含非数字内容）",
            }

    if not valid_lines:
        return {
            "annotation_format": "YOLO",
            "is_valid": False,
            "error": "文件内容为空或不是 YOLO 格式",
        }

    # 3. 尝试找到 classes.txt
    parent_dir = os.path.dirname(annotation_path)
    classes_file = os.path.join(parent_dir, "classes.txt")

    class_names = {}
    if os.path.exists(classes_file):
        try:
            with open(classes_file, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    name = line.strip()
                    if name:
                        class_names[i] = name
        except Exception:
            pass

    # 4. 统计类别分布
    class_distribution = {}

    for class_id, _, _, _, _ in valid_lines:
        class_name = class_names.get(class_id, f"class_{class_id}")
        class_distribution[class_name] = (
            class_distribution.get(class_name, 0) + 1
        )

    # 5. bbox 统计
    # YOLO 的 bbox 是归一化的，面积也是归一化的（0~1）
    areas = [w * h for _, _, _, w, h in valid_lines]

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
    # YOLO 坐标归一化，COCO 标准的 32x32 像素不适用
    # 用归一化面积 < 0.02（约 14x14 像素在 100x100 图上）作为阈值
    YOLO_SMALL_THRESHOLD = 0.02

    if areas:
        small_objects = [
            a for a in areas
            if a < YOLO_SMALL_THRESHOLD
        ]
        small_object_ratio = len(small_objects) / len(areas)
    else:
        small_object_ratio = 0

    result = {
        "annotation_format": "YOLO",
        "is_valid": True,
        "class_distribution": class_distribution,
        "bbox_statistics": {
            "total_bbox": total_bbox,
            "mean_area": mean_area,
            "max_area": max_area,
            "min_area": min_area,
        },
        "small_object_ratio": small_object_ratio,
        "note": "bbox 面积为归一化值（0~1），非像素面积",
    }

    return result
