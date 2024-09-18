import json
import os

from typing import (
    List,
    Tuple,
)

from tqdm import tqdm


# 用于从指定的路径加载训练集和验证集的图像、掩码、元数据列表

# •	输入参数：
def retrieve_data_path(
    data_root_path: str, # 	•	data_root_path: 数据的根目录路径。
    train_mask_data_path: str, # 	•	train_mask_data_path: 训练集掩码数据的路径。
    val_mask_data_path: str, # 	•	val_mask_data_path: 验证集掩码数据的路径。
    label_file: str, # 	•	label_file: 标签文件的名称（JSON格式），包含所有图像的元数据信息。
) -> Tuple[list, list, list, list, list, list]:
# •	返回值：
# 	•	返回6个列表：
# 	•	train_img_list: 训练集图像路径列表。
# 	•	train_mask_list: 训练集掩码路径列表。
# 	•	train_meta_list: 训练集元数据列表。
# 	•	val_img_list: 验证集图像路径列表。
# 	•	val_mask_list: 验证集掩码路径列表。
# 	•	val_meta_list: 验证集元数据列表。


    label_file_json_path = os.path.join(data_root_path, label_file)
	# 1.	使用 json.load 读取标签文件中的数据。
    with open(label_file_json_path) as file:
        label_data = json.load(file)["root"]

    train_img_list, val_img_list = [], []
    train_mask_list, val_mask_list = [], []
    train_meta_list, val_meta_list = [], []

    for data in label_data:
        img_path = os.path.join(data_root_path, data["img_paths"])
        mask_path = (
            train_mask_data_path + data["img_paths"][-16:-4] + ".jpg"
            if data["isValidation"] == 0
            else val_mask_data_path + data["img_paths"][-16:-4] + ".jpg"
        )
        # 2.	根据 isValidation 字段判断数据属于训练集还是验证集，将对应的图像路径、掩码路径、元数据分别加入相应的列表中。
        if data["isValidation"] == 0:
            train_img_list.append(img_path)
            train_mask_list.append(mask_path)
            train_meta_list.append(data)
        else:
            val_img_list.append(img_path)
            val_mask_list.append(mask_path)
            val_meta_list.append(data)
    # 3.	返回训练集和验证集的图像、掩码及元数据列表。
    return (
        train_img_list,
        train_mask_list,
        train_meta_list,
        val_img_list,
        val_mask_list,
        val_meta_list,
    )

# 输入参数：
# 	•	meta_list: 包含子集数据的元数据列表。
# 	•	save_file: 要保存的文件路径。
def generate_label_file_for_subset_data(meta_list: List[dict], save_file: str) -> str:
    # •	返回值：
	# •   	返回生成的标签文件的路径。
    
    #     1.	将元数据列表 meta_list 包装成一个字典形式，键名为 “root”。
    subset_data = {"root": meta_list}
    total_iterations = len(meta_list)

    #     2.	使用 json.dumps 将字典转换为带有缩进的JSON字符串。
    subset_data_str = json.dumps(subset_data, indent=2)

    #     3.	打开目标文件 save_file，并写入生成的JSON字符串。
    with open(save_file, "w") as outfile:
        #     4.	使用 tqdm 显示进度条，更新子集数据的生成进度。
        with tqdm(total=total_iterations, desc="Generating label file") as pbar:
            outfile.write(subset_data_str)
            pbar.update(total_iterations)

    return save_file
