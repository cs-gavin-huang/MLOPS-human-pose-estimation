# 生成一个用于验证子集数据的标签文件。它通过命令行传递参数（num_samples）来控制生成子集的样本数量
import argparse 	# •	argparse 用于解析命令行参数。
import os 	# •	os 用于操作系统路径管理。

from config import cfg 	# •	cfg 是配置文件，用于管理数据路径等配置信息。
from logs import log 	# •	log 是日志模块，用于记录信息。
from src.utils.manage_data_path import (
    generate_label_file_for_subset_data, 	# •	generate_label_file_for_subset_data 用于生成子集数据的标签文件。
    retrieve_data_path, 	# •	retrieve_data_path 用于获取训练和验证集的图像、掩码和元数据列表。
)


if __name__ == "__main__":
    # 从命令行获取参数：通过argparse库，用户可以通过命令行传递一个参数--num_samples，指定需要生成子集数据的样本数量。
    parser = argparse.ArgumentParser(description="Generating label file for subset data")
    parser.add_argument(
        "--num_samples",
        metavar="N",
        type=int,
        help="Number of samples to generate subset data",
    )
    args = parser.parse_args()
    # 数据路径处理：使用retrieve_data_path函数来获取训练集和验证集的图像列表、掩码列表、元数据列表。数据路径的配置通过cfg对象传入。
    num_sample = args.num_samples
    (
        train_img_list,
        train_mask_list,
        train_meta_list,
        val_img_list,
        val_mask_list,
        val_meta_list,
    ) = retrieve_data_path(
        cfg.data_root_path,
        cfg.train_mask_data_path,
        cfg.val_mask_data_path,
        cfg.label_file,
    )

# 这段代码的功能是从验证集 (`val_meta_list`) 中选取一定数量的样本，生成一个包含这些样本的标签文件，并将其保存到指定的路径中。让我们逐步解释：
# ### 1. **`sample_meta_list = val_meta_list[:num_sample]`**
#    - 这里的 `val_meta_list` 是验证集的元数据列表，包含了验证集中所有图像、掩码、关节坐标等信息。
#    - `num_sample` 是一个用户通过命令行传入的整数，表示要从验证集中选取多少个样本。
#    - `val_meta_list[:num_sample]` 使用列表切片操作，从 `val_meta_list` 中提取前 `num_sample` 个元数据，组成一个新的列表 `sample_meta_list`，这个列表将用于生成标签文件。
    sample_meta_list = val_meta_list[:num_sample]
# ### 2. **`save_output_file = os.path.join(cfg.data_root_path, cfg.label_subset_file)`**
#    - 这里使用 `os.path.join` 函数构造保存标签文件的完整路径。
#    - `cfg.data_root_path` 是数据存储的根路径，通常是一个目录路径，比如 `/data/pose_estimation`。
#    - `cfg.label_subset_file` 是子集标签文件的名称，比如 `subset_label.json`。
#    - `os.path.join(cfg.data_root_path, cfg.label_subset_file)` 将根路径和文件名连接起来，生成完整的文件路径，如 `/data/pose_estimation/subset_label.json`，并将其赋值给 `save_output_file` 变量。
    save_output_file = os.path.join(cfg.data_root_path, cfg.label_subset_file)
# ### 3. **`output_label_file_path = generate_label_file_for_subset_data(sample_meta_list, save_output_file)`**
#    - `generate_label_file_for_subset_data` 是一个函数，用于将子集数据写入一个标签文件。
#    - `sample_meta_list` 是前面提取的验证集子集的元数据列表，它包含了将要写入标签文件的数据。
#    - `save_output_file` 是文件的保存路径（前面生成的路径），决定了生成的标签文件保存在哪里。
#    - 调用 `generate_label_file_for_subset_data(sample_meta_list, save_output_file)` 函数，会把 `sample_meta_list` 中的数据写入文件 `save_output_file`，并返回生成的标签文件路径。
#    - `output_label_file_path` 保存了生成的标签文件的路径，用于记录或日志输出。
    output_label_file_path = generate_label_file_for_subset_data(
        sample_meta_list, save_output_file
    )
# ### 总结：
# - **功能**：从验证集数据中提取前 `num_sample` 个样本（即子集），并将它们的元数据保存为一个标签文件，文件名和路径由 `cfg` 配置决定。
# - **步骤**：
#   1. 从验证集的元数据中提取指定数量的样本，生成一个子集元数据列表。
#   2. 构造保存该子集标签文件的完整路径。
#   3. 调用函数将该子集数据保存为一个 JSON 文件，并返回保存文件的路径。
    log.info(f"The output label json file path: {output_label_file_path}")
