"""
Dataset Scan Tool

作用：
    扫描数据集目录结构，获取数据集基础信息。

功能：
    1. 统计图片数量
    2. 获取图片目录
    3. 查找annotation标注文件
    4. 判断标注格式(COCO/VOC/YOLO)
    5. 查找mask目录
    6. 统计train/val/test划分情况

输入：
    dataset_path:
        数据集路径

输出：
    {
        "dataset_name": 数据集名称,
        "image_count": 图片数量,
        "splits": 数据划分,
        "image_dirs": 图片目录,
        "annotation_files": 标注文件,
        "mask_dirs": mask目录,
        "image_extensions": 图片格式,
        "annotation_format": 标注格式
    }

当前阶段：
    已完成基础扫描功能，
    为后续 Annotation Parser、
    Image Quality Analyzer 等 Tool 提供数据路径信息。

后续扩展：
    1. 增加更多数据集格式识别
    2. 增强异常目录检测
    3. 支持自定义数据集规则
"""


import os

from app.agents.dataset_profiling_agent.logs.tool_logger import tool_log


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg"
}


ANNOTATION_EXTENSIONS = {
    '.json',
    '.xml',
    '.txt'
}


MASK_DIR_NAMES = {
    "mask",
    "masks",
    "ground_truth",
    "groundtruth"
}

NON_ANNOTATION_TEXT_NAMES = {
    "readme.txt",
    "license.txt",
    "licence.txt",
    "classes.txt",
    "notes.txt",
}


def _is_yolo_label_file(file_path):
    """Only accept numeric YOLO box rows, or empty files inside labels folders.

    A .txt suffix alone is not enough: datasets commonly include README/license
    files. Empty per-image YOLO label files are valid when stored under labels/.
    """
    path = os.path.normpath(file_path)
    filename = os.path.basename(path).lower()
    if filename in NON_ANNOTATION_TEXT_NAMES:
        return False

    try:
        with open(file_path, "r", encoding="utf-8-sig") as handle:
            lines = [line.strip() for line in handle if line.strip()]
    except (OSError, UnicodeError):
        return False

    if not lines:
        return any(part.lower() in {"label", "labels"} for part in path.split(os.sep))

    for line in lines:
        values = line.split()
        if len(values) != 5:
            return False
        try:
            class_id = int(values[0])
            x_center, y_center, width, height = map(float, values[1:])
        except ValueError:
            return False
        if class_id < 0 or not all(0.0 <= value <= 1.0 for value in (x_center, y_center, width, height)):
            return False
        if width == 0 or height == 0:
            return False
    return True



def dataset_scan(dataset_path):
    """
    Dataset Scan Tool入口函数

    功能：
        扫描指定数据集目录，
        返回数据集结构信息。

    输入：
        dataset_path:
            数据集路径

    输出：
        dict:
            数据集基础信息

    调用者：
        DatasetProfilingAgent

    """

    if not os.path.isdir(dataset_path):
        raise ValueError(f"数据集路径不存在或不是目录：{dataset_path}")

    tool_log(
        "dataset_scan",
        "start"
    )

    splits = {
        "train": 0,
        "val": 0,
        "test": 0
    }

    dataset_name = os.path.basename(dataset_path)

    image_count = 0

    image_extensions = set()
    #统计图片数量
    image_dirs = set()
    annotation_files = set()
    mask_dirs = set()
    annotation_formats = set()
    category_distribution = {}

    for root, dirs, files in os.walk(dataset_path):
        # Mask 目录中的图片是标注掩码，不应计入数据集原图数量。
        # 同时跳过其全部子目录，避免嵌套结构再次把 Mask 算作普通图片。
        rel_path = os.path.relpath(root, dataset_path)
        path_parts = rel_path.split(os.sep)
        folder_name = os.path.basename(root)
        is_mask_directory = any(part.lower() in MASK_DIR_NAMES for part in path_parts)

        if folder_name.lower() in MASK_DIR_NAMES:
            mask_dirs.add(root)

        if is_mask_directory:
            continue

        for file in files:
            ext = os.path.splitext(file)[1].lower()

            if ext in IMAGE_EXTENSIONS:
                image_count += 1
                image_extensions.add(ext)
                # 获取目录的功能
                image_dirs.add(root)
                #统计train val test各自数量
                # 用相对路径的第一级目录判断（支持 train/good、test/broken_large 等嵌套结构）
                if path_parts and path_parts[0] in splits:
                    splits[path_parts[0]] += 1
                    if len(path_parts) >= 2:
                        split_name, category_name = path_parts[0], path_parts[1]
                        split_categories = category_distribution.setdefault(split_name, {})
                        split_categories[category_name] = split_categories.get(category_name, 0) + 1

            #扫描annotation_files（标记文件 ）
            if ext in ANNOTATION_EXTENSIONS and (ext != ".txt" or _is_yolo_label_file(os.path.join(root, file))):
                annotation_files.add(os.path.join(root, file))

    for file in annotation_files:
        ext = os.path.splitext(file)[1].lower()

        if ext == ".json":
            annotation_formats.add("COCO")

        elif ext == ".xml":
            annotation_formats.add("VOC")

        elif ext == ".txt":
            annotation_formats.add("YOLO")

    result = {
              "dataset_name": dataset_name,

              "dataset_path": dataset_path,

              "image_count": image_count,

              "splits": splits,

              "image_dirs": list(image_dirs),

              "annotation_files": list(annotation_files),

              "mask_dirs": list(mask_dirs),

              "image_extensions":list(image_extensions),

              "annotation_format": list(annotation_formats),

              "category_distribution": category_distribution,

            }

    tool_log(
        "dataset_scan","finished"
    )


    return result
