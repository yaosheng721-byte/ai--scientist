"""
OpenCV Image Analyzer Tool

作用：
    用 OpenCV 读取图像，做图像层面的分析。

功能：
    1. 图像尺寸分布（宽高统计）
    2. 缺陷区域比例（读 ground_truth mask）
    3. train/test 分布差异

输入：
    dataset_path:
        数据集路径

输出：
    {
        "dataset_path": ...,
        "image_analysis": {
            "train": {
                "good": {
                    "path": ...,
                    "num_images": N,
                    "image_size_distribution": {...},
                    "defect_ratio": {...}
                }
            },
            "test": { ... }
        },
        "distribution_difference": {
            "width_mean_difference": ...,
            "height_mean_difference": ...,
            "defect_ratio_difference": ...
        }
    }
"""

from pathlib import Path

import json
import numpy as np
import cv2

from app.agents.dataset_profiling_agent.logs.tool_logger import tool_log


IMAGE_SUFFIX = [
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
]


def analyze_folder(folder_path):
    """
    分析单个图片文件夹

    返回:
        图像数量
        图像尺寸分布
        缺陷区域比例
    """

    width_list = []
    height_list = []

    defect_ratios = []

    image_count = 0


    # =================================
    # 定位对应的 ground_truth mask 目录
    #
    # 例如:
    #   test/broken_large/  (folder_path)
    #   → ground_truth/broken_large/  (mask_dir)
    #
    # good 类没有 mask
    # =================================

    mask_dir = (
        folder_path.parent.parent
        / "ground_truth"
        / folder_path.name
    )

    has_mask = mask_dir.is_dir()


    # =================================
    # 递归读取图片
    # =================================

    for file in folder_path.rglob("*"):

        if not file.is_file():
            continue

        if file.suffix.lower() not in IMAGE_SUFFIX:
            continue


        # 解决 Windows 中文路径问题

        img = cv2.imdecode(
            np.fromfile(
                str(file),
                dtype=np.uint8
            ),
            cv2.IMREAD_COLOR
        )

        if img is None:
            continue

        image_count += 1


        # ==================
        # 图像尺寸
        # ==================

        height, width = img.shape[:2]

        width_list.append(width)

        height_list.append(height)


        # ==================
        # 缺陷区域比例
        #
        # 读对应 mask:
        #   test/broken_large/000.png
        #   → ground_truth/broken_large/000_mask.png
        # ==================

        if has_mask:

            mask_name = file.stem + "_mask.png"

            mask_path = mask_dir / mask_name

            if mask_path.exists():

                mask = cv2.imdecode(
                    np.fromfile(
                        str(mask_path),
                        dtype=np.uint8
                    ),
                    cv2.IMREAD_GRAYSCALE
                )

                if mask is not None:

                    total_pixels = (
                        mask.shape[0]
                        * mask.shape[1]
                    )

                    if total_pixels > 0:

                        defect_pixels = cv2.countNonZero(
                            mask
                        )

                        ratio = defect_pixels / total_pixels

                        defect_ratios.append(ratio)


    # ==================
    # 空目录处理
    # ==================

    if image_count == 0:

        return {
            "num_images": 0,
            "image_size_distribution": {
                "width_mean": 0,
                "height_mean": 0,
                "width_min": 0,
                "width_max": 0,
                "height_min": 0,
                "height_max": 0
            },
            "defect_ratio": {
                "mean": None,
                "min": None,
                "max": None,
                "has_mask": has_mask,
                "mask_count": 0,
            }
        }


    # ==================
    # 图像尺寸统计
    # ==================

    size_dist = {
        "width_mean": float(np.mean(width_list)),
        "height_mean": float(np.mean(height_list)),
        "width_min": int(min(width_list)),
        "width_max": int(max(width_list)),
        "height_min": int(min(height_list)),
        "height_max": int(max(height_list))
    }


    # ==================
    # 缺陷比例统计
    # ==================

    if defect_ratios:

        defect_ratio = {
            "mean": float(np.mean(defect_ratios)),
            "min": float(min(defect_ratios)),
            "max": float(max(defect_ratios)),
            "has_mask": True,
            "mask_count": len(defect_ratios),
        }

    else:

        defect_ratio = {
            "mean": None,
            "min": None,
            "max": None,
            "has_mask": has_mask,
            "mask_count": 0,
        }


    result = {
        "num_images": image_count,
        "image_size_distribution": size_dist,
        "defect_ratio": defect_ratio
    }

    return result



def calculate_split_mean(split_result):
    """
    计算 train/test 整体的平均尺寸和缺陷比例

    用于 distribution_difference 对比
    """

    width_sum = 0.0
    height_sum = 0.0
    image_count = 0
    defect_sum = 0.0
    mask_count = 0

    for category in split_result.values():

        sd = category.get("image_size_distribution", {})

        count = int(category.get("num_images", 0) or 0)
        width_sum += float(sd.get("width_mean", 0) or 0) * count
        height_sum += float(sd.get("height_mean", 0) or 0) * count
        image_count += count

        dr = category.get("defect_ratio", {})

        measured_masks = int(dr.get("mask_count", 0) or 0)
        if measured_masks and dr.get("mean") is not None:
            defect_sum += float(dr["mean"]) * measured_masks
            mask_count += measured_masks


    return {
        "width_mean": width_sum / image_count if image_count else 0.0,
        "height_mean": height_sum / image_count if image_count else 0.0,
        "defect_ratio_mean": defect_sum / mask_count if mask_count else None,
    }



def opencv_image_analyzer(dataset_path):
    """
    OpenCV Image Analyzer Tool 入口函数

    参数:
        dataset_path:
            数据集路径

    输出:
        dict:
            图像尺寸分布 + 缺陷区域比例 + train/test 差异
    """

    tool_log(
        "opencv_image_analyzer",
        "start"
    )

    dataset_path = Path(dataset_path)


    result = {
        "dataset_path": str(dataset_path),
        "image_analysis": {}
    }


    # ==================
    # 扫描 train/test
    # ==================

    for split_dir in dataset_path.iterdir():

        if not split_dir.is_dir():
            continue

        # 跳过 ground_truth 目录

        if split_dir.name == "ground_truth":
            continue

        # 跳过非数据目录（如 license.txt 所在目录）

        split_name = split_dir.name

        if split_name not in ("train", "test", "val"):
            continue


        result["image_analysis"][split_name] = {}


        # ==================
        # 扫描类别
        # ==================

        for category_dir in split_dir.iterdir():

            if not category_dir.is_dir():
                continue

            category_name = category_dir.name

            result["image_analysis"][split_name][category_name] = {
                "path": str(category_dir),
                **analyze_folder(category_dir)
            }


    # ==================
    # train/test 差异分析
    # ==================

    if (
        "train" in result["image_analysis"]
        and
        "test" in result["image_analysis"]
    ):

        train_mean = calculate_split_mean(
            result["image_analysis"]["train"]
        )

        test_mean = calculate_split_mean(
            result["image_analysis"]["test"]
        )

        result["distribution_difference"] = {
            "width_mean_difference": abs(
                train_mean["width_mean"]
                -
                test_mean["width_mean"]
            ),
            "height_mean_difference": abs(
                train_mean["height_mean"]
                -
                test_mean["height_mean"]
            ),
            "defect_ratio_difference": (
                abs(train_mean["defect_ratio_mean"] - test_mean["defect_ratio_mean"])
                if train_mean["defect_ratio_mean"] is not None
                and test_mean["defect_ratio_mean"] is not None
                else None
            )
        }

    else:

        result["distribution_difference"] = {
            "width_mean_difference": 0.0,
            "height_mean_difference": 0.0,
            "defect_ratio_difference": 0.0
        }


    tool_log(
        "opencv_image_analyzer",
        "finished"
    )

    return result



if __name__ == "__main__":

    dataset_path = (
        r"D:\PythonProject\dataset_profiling_agent\demo_dataset\MVTec\bottle"
    )

    result = opencv_image_analyzer(
        dataset_path
    )

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
            default=lambda x: float(x)
        )
    )
