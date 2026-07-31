# from pathlib import Path
#
# import json
# import numpy as np
# import cv2
#
# from app.agents.dataset_profiling_agent.logs.tool_logger import tool_log
#
#
#
# def analyze_folder(folder_path):
#     """
#     分析单个图片文件夹
#
#     例如:
#         train/good
#         test/broken_large
#
#     返回:
#         该文件夹图片质量统计
#     """
#
#
#     blur_score_total = 0
#     brightness_total = 0
#     noise_score_total = 0
#
#     image_count = 0
#
#
#     image_suffix = [
#         ".jpg",
#         ".jpeg",
#         ".png",
#         ".bmp"
#     ]
#
#
#     #递归读取图片
#     for file in folder_path.rglob("*"):
#
#
#         if not file.is_file():
#             continue
#
#
#         if file.suffix.lower() not in image_suffix:
#             continue
#
#
#
#         img = cv2.imread(
#             str(file)
#         )
#
#
#         if img is None:
#             continue
#
#
#         image_count += 1
#
#
#
#         # 灰度图
#         gray = cv2.cvtColor(
#             img,
#             cv2.COLOR_BGR2GRAY
#         )
#
#
#         # ----------------
#         # Blur
#         # Laplacian方差
#         # ----------------
#
#         lap = cv2.Laplacian(
#             gray,
#             cv2.CV_64F
#         )
#
#
#         blur_score = lap.var()
#
#
#         blur_score_total += blur_score
#
#
#
#         # ----------------
#         # Brightness
#         # ----------------
#
#         brightness = gray.mean() / 255
#
#
#         brightness_total += brightness
#
#
#
#         # ----------------
#         # Noise
#         # Gaussian残差
#         # ----------------
#
#         smooth = cv2.GaussianBlur(
#             gray,
#             (5,5),
#             0
#         )
#
#
#         noise = np.std(
#             gray - smooth
#         )
#
#
#         noise_score_total += noise
#
#
#
#     if image_count > 0:
#
#
#         result = {
#
#             "num_images": image_count,
#
#
#             "quality_statistics": {
#
#                 "blur_score_mean":
#                     blur_score_total / image_count,
#
#
#                 "brightness_mean":
#                     brightness_total / image_count,
#
#
#                 "noise_score_mean":
#                     noise_score_total / image_count
#
#             }
#
#         }
#
#
#     else:
#
#
#         result = {
#
#             "num_images":0,
#
#             "quality_statistics":{
#
#                 "blur_score_mean":0,
#
#                 "brightness_mean":0,
#
#                 "noise_score_mean":0
#
#             }
#
#         }
#
#
#     return result
#
#
#
#
#
# def image_quality(dataset_path):
#
#
#     tool_log(
#         "image_quality",
#         "start"
#     )
#
#
#     dataset_path = Path(dataset_path)
#
#
#
#     result = {
#
#         "dataset_path":str(dataset_path),
#
#         "quality_statistics":{}
#
#     }
#
#
#
#     #扫描一级目录
#     #例如 train/test
#
#     for split_dir in dataset_path.iterdir():
#
#
#         if not split_dir.is_dir():
#             continue
#
#
#
#         split_name = split_dir.name
#
#
#
#         result["quality_statistics"][split_name] = {}
#
#
#
#         #扫描二级目录
#         #例如 good/broken_large
#
#         for category_dir in split_dir.iterdir():
#
#
#             if not category_dir.is_dir():
#                 continue
#
#
#
#             category_name = category_dir.name
#
#
#
#             result["quality_statistics"][split_name][category_name] = {
#
#
#                 "path":str(category_dir),
#
#
#                 **analyze_folder(
#                     category_dir
#                 )
#
#             }
#
#
#
#     tool_log(
#         "image_quality",
#         "finished"
#     )
#
#
#     return result
#
#
# if __name__ == "__main__":
#
#     dataset_path = (
#         r"D:\PythonProject\dataset_profiling_agent\demo_dataset\MVTec\cable"
#     )
#
#
#     result = image_quality(
#         dataset_path
#     )
#
#     print(
#         json.dumps(
#             result,
#             indent=4,
#             ensure_ascii=False
#         )
#     )

from pathlib import Path

import json
import numpy as np
import cv2

from app.agents.dataset_profiling_agent.logs.tool_logger import tool_log



def analyze_folder(folder_path):
    """
    分析单个图片文件夹

    例如:
        train/good
        test/broken_large

    返回:
        图片数量
        图像质量统计（模糊/亮度/噪声）
    """


    blur_score_total = 0
    brightness_total = 0
    noise_score_total = 0

    image_count = 0


    image_suffix = [
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp"
    ]


    #递归读取图片
    for file in folder_path.rglob("*"):


        if not file.is_file():
            continue


        if file.suffix.lower() not in image_suffix:
            continue



        #解决Windows中文路径问题
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
        # 灰度图
        # ==================

        gray = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2GRAY
        )



        # ==================
        # Blur
        # Laplacian方差
        # ==================

        lap = cv2.Laplacian(
            gray,
            cv2.CV_64F
        )


        blur_score = lap.var()


        blur_score_total += blur_score



        # ==================
        # Brightness
        # ==================

        brightness = gray.mean() / 255


        brightness_total += brightness



        # ==================
        # Noise
        # Gaussian残差
        # ==================

        smooth = cv2.GaussianBlur(
            gray,
            (5,5),
            0
        )


        noise = np.std(
            gray - smooth
        )


        noise_score_total += noise



    # ==================
    # 空目录处理
    # ==================

    if image_count == 0:

        return {

            "num_images":0,

            "quality_statistics":{

                "blur_score_mean":0,

                "brightness_mean":0,

                "noise_score_mean":0

            }

        }



    result = {

        "num_images":image_count,

        "quality_statistics":{

            "blur_score_mean":
                blur_score_total / image_count,

            "brightness_mean":
                brightness_total / image_count,

            "noise_score_mean":
                noise_score_total / image_count

        }

    }

    return result




def image_quality(dataset_path):


    tool_log(
        "image_quality",
        "start"
    )


    dataset_path = Path(dataset_path)



    result = {

        "dataset_path":
            str(dataset_path),

        "quality_statistics":{}

    }



    #====================
    # 扫描train/test
    #====================

    for split_dir in dataset_path.iterdir():


        if not split_dir.is_dir():
            continue


        #跳过mask
        if split_dir.name == "ground_truth":
            continue



        split_name = split_dir.name


        result["quality_statistics"][split_name] = {}



        #====================
        # 扫描类别
        #====================

        for category_dir in split_dir.iterdir():


            if not category_dir.is_dir():
                continue



            category_name = category_dir.name



            result["quality_statistics"][split_name][category_name] = {


                "path":
                    str(category_dir),


                **analyze_folder(
                    category_dir
                )

            }



    tool_log(
        "image_quality",
        "finished"
    )


    return result





if __name__ == "__main__":


    dataset_path = (
        r"D:\PythonProject\dataset_profiling_agent\demo_dataset\MVTec\cable"
    )


    result = image_quality(
        dataset_path
    )


    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )