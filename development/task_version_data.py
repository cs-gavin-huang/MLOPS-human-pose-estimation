import os
import subprocess

from pathlib import Path

from loguru import logger

from config import cfg
# run_shell_command 是一个从 src.utils.run_command 中导入的辅助函数，用于在 shell 中执行命令
from src.utils.run_command import run_shell_command

# •	这个函数检查当前项目目录下是否已经初始化了 DVC。它通过检查当前目录下是否存在 .dvc 文件夹来判断。
def is_dvc_initialized() -> bool:
    # •	返回值：布尔值，表示 DVC 是否已初始化。
    return (Path().cwd() / ".dvc").exists()



# initialize_dvc()
# 	•	该函数用于初始化 DVC。如果 DVC 已经初始化，函数会输出日志并返回；否则，它会执行以下操作：
    # 	1.	调用 dvc init 命令，初始化 DVC。
    # 	2.	禁用 DVC 的分析功能 (dvc config core.analytics false)。
    # 	3.	启用自动分阶段 (dvc config core.autostage true)。
    # 	4.	使用 Git 将 .dvc 文件夹添加到版本控制并提交。
# 	•	使用 loguru 记录初始化过程中的信息。
def initialize_dvc() -> None:
    if is_dvc_initialized():
        logger.info("DVC is already initialized")
        return None
    logger.info("Initializing DVC...")
    # try:
    #     run_shell_command("git checkout -b dev")
    # except subprocess.CalledProcessError:
    #     run_shell_command("git checkout dev")
    run_shell_command("poetry run dvc init --subdir")
    run_shell_command("poetry run dvc config core.analytics false")
    run_shell_command("poetry run dvc config core.autostage true")
    run_shell_command("git add .dvc")
    run_shell_command("git commit -m 'feat: Initialize DVC'")

# initialize_dvc_storage(dvc_remote_name, dvc_remote_url)

# 	•	该函数用于配置 DVC 的远程存储，用于存储数据版本。
# 	•	如果没有配置 DVC 远程存储，则会添加远程存储，并将配置提交到 Git 中
def initialize_dvc_storage(dvc_remote_name: str, dvc_remote_url: str) -> None:
    if not run_shell_command("poetry run dvc remote list"):
        logger.info("Initialize DVC storage...")
        run_shell_command(f"poetry run dvc remote add -d {dvc_remote_name} {dvc_remote_url}")
        # 1.	analytics = false：这是 DVC 的一个设置，
            # 用来禁用 DVC 向开发者发送匿名使用统计数据。通过将其设置为 false，可以关闭分析功能，避免发送数据到 DVC 的服务器。
        # 2.	autostage = true：这个选项启用了自动暂存（autostage）功能。
            # 在 DVC 中，启用该选项后，任何 DVC 命令（例如 dvc add 或 dvc repro）都会自动将修改的文件暂存到 Git 中，避免手动执行 git add。
        # 3.	remote = gcs-storage：这是指定 DVC 使用的远程存储名称。
            # 这里的远程存储被命名为 gcs-storage，对应下面定义的 Google Cloud Storage (GCS) 存储配置。DVC 会将数据推送到这个远程存储。
        run_shell_command("git add .dvc/config")
        run_shell_command(f"git commit -m 'Configure remote storage at: {dvc_remote_url}'")
    else:
        logger.info("DVC storage was already initialized.")

# 该函数获取当前数据版本（通过 Git 标签来标记版本）。
def get_current_data_version() -> str:
    current_version = run_shell_command(
        "git tag --list | sort -t v -k 2 -g | tail -1 | sed 's/v//'"
    )
    return current_version


# 根据原始数据文件夹生成 DVC 创建的 .gitignore 文件路径。
# DVC 通常会自动生成 .gitignore 文件来忽略数据文件，而只跟踪其版本信息。
def get_gitignore_file_created_by_dvc(raw_data_folder: str) -> str:
    seperator = os.sep
    return os.path.join(seperator.join(raw_data_folder.split(seperator)[:-1]), ".gitignore")

# 新的数据版本提交到 DVC 远程存储，主要步骤包括：
def commit_new_data_version_to_dvc(raw_data_folder: str, dvc_remote_name: str) -> None:
    current_version = get_current_data_version().strip()
    if not current_version:
        current_version = "0"
    next_version = f"v{int(current_version)+1}"
    logger.info("Add data to dvc")
    # 	1.	添加数据到 DVC。
    run_shell_command(f"poetry run dvc add {raw_data_folder}")

    gitignore_file = get_gitignore_file_created_by_dvc(raw_data_folder)
    # 	2.	获取 .gitignore 文件，并将其与数据版本信息一同提交到 Git。
    run_shell_command(f"git add {raw_data_folder}.dvc {gitignore_file}")
    run_shell_command(
        f"git commit -m 'Updated data version from v{current_version} to {next_version}'"
    )
    # 	3.	为新版本创建 Git 标签，并推送到远程存储和 Git 仓库。
    run_shell_command(f"git tag -a {next_version} -m 'Versioning data: {next_version}'")
    logger.info(f"Push data version {next_version} to {dvc_remote_name}")
    run_shell_command(f"poetry run dvc push {raw_data_folder}.dvc --remote {dvc_remote_name}")
    run_shell_command("git push --follow-tags origin dev")
    run_shell_command("git push -f --tags origin dev")

# 检查数据的当前版本状态，判断是否有新的数据更改需要提交。
def update_data_version(raw_data_folder: str, dvc_remote_name: str) -> None:
    try:
        dvc_status = run_shell_command(f"poetry run dvc status {raw_data_folder}.dvc")
        if dvc_status == "Data and pipelines are up to date.\n":
            #     1. 如果数据和管道已经是最新的，它会记录状态并退出。
            logger.info(dvc_status)
            return None
        #     2. 如果有数据更改，则会调用 commit_new_data_version_to_dvc() 提交新版本。
        commit_new_data_version_to_dvc(raw_data_folder, dvc_remote_name)
    except subprocess.CalledProcessError:
        #     3. 如果数据从未被版本化，则首次执行版本化操作。
        logger.info("Versioning data the first time.")
        commit_new_data_version_to_dvc(raw_data_folder, dvc_remote_name)


if __name__ == "__main__":
    initialize_dvc()
    # 配置是从 cfg 变量加载的，其中包括远程存储名称 (dvc_remote_name)、远程存储路径 (dvc_remote_url)、
    # 数据根目录和标签子集文件路径 (cfg.data_root_path, cfg.label_subset_file)。
    initialize_dvc_storage(
        dvc_remote_name=cfg.dvc_remote_name,
        dvc_remote_url=cfg.dvc_remote_url,
    )
    object_version = os.path.join(cfg.data_root_path, cfg.label_subset_file)
    update_data_version(
        raw_data_folder=object_version,
        dvc_remote_name=cfg.dvc_remote_name,
    )
