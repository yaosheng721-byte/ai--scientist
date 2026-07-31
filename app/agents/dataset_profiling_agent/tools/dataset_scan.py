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

    for root, dirs, files in os.walk(dataset_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()

            if ext in IMAGE_EXTENSIONS:
                image_count += 1
                image_extensions.add(ext)
                # 获取目录的功能
                image_dirs.add(root)
                #统计train val test各自数量
                # 用相对路径的第一级目录判断（支持 train/good、test/broken_large 等嵌套结构）
                rel_path = os.path.relpath(root, dataset_path)
                path_parts = rel_path.split(os.sep)
                if path_parts and path_parts[0] in splits:
                    splits[path_parts[0]] += 1

            #扫描annotation_files（标记文件 ）
            if ext in ANNOTATION_EXTENSIONS:
                annotation_files.add(os.path.join(root, file))

        # mask_dirs（掩码）
        folder_name = os.path.basename(root)
        if folder_name in MASK_DIR_NAMES:
            mask_dirs.add(root)

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

            }

    tool_log(
        "dataset_scan","finished"
    )


    return result