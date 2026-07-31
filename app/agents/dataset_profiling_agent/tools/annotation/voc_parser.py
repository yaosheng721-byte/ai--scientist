"""
VOC Annotation Parser

验证逻辑:
    读取 XML 后检查根标签是否为 <annotation>。
    如果不是有效的 VOC 文件，返回 is_valid=False。

输出格式与 coco_parser 一致:
    {
        "annotation_format": "VOC",
        "is_valid": True/False,
        "class_distribution": {...},
        "bbox_statistics": {...},
        "small_object_ratio": float
    }

注意:
    VOC 格式一个 XML 文件对应一张图片，
    所以这里统计的是单张图片的标注信息。
    Agent 层应遍历所有 XML 文件汇总。
"""

import xml.etree.ElementTree as ET


def parse_voc(annotation_path):
    """
    VOC annotation parser

    参数:
        annotation_path:
            VOC xml 路径

    返回:
        annotation 统计信息
    """

    # 1. 读取 XML
    try:
        tree = ET.parse(annotation_path)
        root = tree.getroot()
    except ET.ParseError:
        return {
            "annotation_format": "VOC",
            "is_valid": False,
            "error": "文件不是有效的 XML",
        }
    except Exception:
        return {
            "annotation_format": "VOC",
            "is_valid": False,
            "error": "无法读取文件",
        }

    # 2. 验证根标签
    if root.tag != "annotation":
        return {
            "annotation_format": "VOC",
            "is_valid": False,
            "error": f"根标签不是 <annotation>，而是 <{root.tag}>",
        }

    # 3. 解析类别分布
    objects = root.findall("object")

    class_distribution = {}

    for obj in objects:
        name_elem = obj.find("name")
        if name_elem is not None and name_elem.text:
            class_name = name_elem.text.strip()
            class_distribution[class_name] = (
                class_distribution.get(class_name, 0) + 1
            )

    # 4. bbox 统计
    areas = []

    for obj in objects:
        bndbox = obj.find("bndbox")
        if bndbox is not None:
            xmin_elem = bndbox.find("xmin")
            ymin_elem = bndbox.find("ymin")
            xmax_elem = bndbox.find("xmax")
            ymax_elem = bndbox.find("ymax")

            if all(elem is not None for elem in [xmin_elem, ymin_elem, xmax_elem, ymax_elem]):
                try:
                    xmin = float(xmin_elem.text)
                    ymin = float(ymin_elem.text)
                    xmax = float(xmax_elem.text)
                    ymax = float(ymax_elem.text)
                    area = (xmax - xmin) * (ymax - ymin)
                    areas.append(area)
                except (ValueError, TypeError):
                    pass

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

    # 5. 小目标比例
    # COCO 标准: area < 32*32 = 1024
    COCO_SMALL_THRESHOLD = 32 * 32

    if areas:
        small_objects = [
            a for a in areas
            if a < COCO_SMALL_THRESHOLD
        ]
        small_object_ratio = len(small_objects) / len(areas)
    else:
        small_object_ratio = 0

    result = {
        "annotation_format": "VOC",
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
