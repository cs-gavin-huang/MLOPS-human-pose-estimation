import os

from dotenv import load_dotenv

from config import cfg
from logs import log
from src.config_schemas.mlflow_schema import MLFlowConfig
from src.utils.run_command import run_shell_command
from task_download_weight_from_minio import (
    download_weight_from_minio,
    get_best_run,
    is_previous_weight_better,
    save_info_summary,
)
from task_train import (
    generate_run_name_by_date_time,
    run_train,
)
from task_version_data import (
    initialize_dvc,
    initialize_dvc_storage,
    update_data_version,
)

load_dotenv(".env")

MINIO_PORT = os.environ["MINIO_PORT"]
MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_ACCESS_KEY = os.environ["MINIO_SECRET_ACCESS_KEY"]
MLFLOW_BUCKET_NAME = os.environ["MLFLOW_BUCKET_NAME"]

""" 
这段代码是一个集成了数据版本控制、模型训练、权重验证、以及将容器镜像推送到 Docker Hub 的自动化流程，适用于机器学习模型的开发与部署。主要的工作流程包括 DVC 数据版本控制、MLflow 管理的模型训练、权重验证、以及基于验证结果的容器镜像推送。下面是详细的解释：

### 主要功能组件

#### 1. **环境变量加载**
   - **`load_dotenv`**：从 `.env` 文件加载环境变量，包含 MinIO 服务的访问密钥、端口、以及 MLflow 存储桶的相关信息。
   - 这些环境变量用于与 MinIO 和 MLflow 交互。

#### 2. **`DataVersion` 类**
   - 负责执行数据版本控制任务，主要通过 DVC 管理数据的版本。
   - **`initialize_dvc()`** 和 **`initialize_dvc_storage()`** 初始化 DVC 并配置远程存储（通常是使用 Google Cloud Storage 或 MinIO）。
   - **`update_data_version()`** 用于版本化数据，将新的数据版本推送到远程存储。

#### 3. **`ModelTraining` 类**
   - 负责执行模型训练任务。
   - 使用 `MLFlowConfig` 加载与 MLflow 相关的配置，通过 `run_train()` 进行模型训练，并将实验数据记录到 MLflow。
   - **`generate_run_name_by_date_time()`** 自动生成运行名称，确保实验名称唯一。

#### 4. **`WeightValidation` 类**
   - 验证新训练的模型权重是否优于之前的权重，决定是否更新模型。
   - **`get_best_run()`**：从 MLflow 获取当前实验中表现最好的模型运行（根据验证损失）。
   - **`is_previous_weight_better()`**：对比当前权重和之前保存的最优权重，判断是否需要更新。
   - 如果新权重优于之前的权重，则下载新的权重文件并保存更新。

#### 5. **`ImagePushingDockerHub` 类**
   - 如果权重被更新，执行 Docker 镜像构建和推送到 Docker Hub。
   - 先通过 `docker compose` 构建新的 Docker 镜像，随后使用 `docker push` 将镜像推送到 Docker Hub。

### 主程序执行逻辑

在 `__main__` 部分，整个流程按照以下顺序执行：
1. **数据版本控制**：调用 `DataVersion.run()` 初始化 DVC，并更新数据版本。
2. **模型训练**：调用 `ModelTraining.run()` 执行模型训练，并记录到 MLflow。
3. **权重验证**：调用 `WeightValidation.run()`，验证新模型权重是否比之前的模型更优。
4. **推送 Docker 镜像**：根据权重验证结果，决定是否构建并推送新的 Docker 镜像到 Docker Hub。
"""

class DataVersion:
    @staticmethod
    def run() -> None:
        log.info("=================== STARTING DATA VERSIONING TASK. ===================")
        initialize_dvc()
        initialize_dvc_storage(
            dvc_remote_name=cfg.dvc_remote_name,
            dvc_remote_url=cfg.dvc_remote_url,
        )
        object_version = os.path.join(cfg.data_root_path, cfg.label_subset_file)
        update_data_version(
            raw_data_folder=object_version,
            dvc_remote_name=cfg.dvc_remote_name,
        )
        log.info("=================== FINISHED DATA VERSIONING TASK. ===================")


class ModelTraining:
    @staticmethod
    def run() -> None:
        log.info("=================== STARTING TRAINING TASK. ===================")
        mlflow_config = MLFlowConfig()
        experiment_name = cfg.experiment_name
        run_name = generate_run_name_by_date_time()
        run_train(cfg, mlflow_config, experiment_name, run_name)
        log.info("=================== FINISHED TRAINING TASK. ===================")


class WeightValidation:
    @staticmethod
    def run() -> bool:
        update = False
        log.info("=================== STARTING WEIGHT VALIDATION TASK. ===================")
        info_summary_json_file = cfg.info_summary_file_path
        best_run = get_best_run(cfg.experiment_name)

        if len(best_run) == 0:
            raise ValueError(
                "No runs in the experiment 'openpose-human-pose-training' are in FINISHED status."
            )

        current_val_loss = float(best_run["tags.val_loss"])

        if not is_previous_weight_better(current_val_loss, info_summary_json_file):
            weight_artifact = os.path.join(
                best_run["artifact_uri"].split(":")[-1][1:],
                "model_state_dict_best",
                "state_dict.pth",
            )
            download_weight_from_minio(
                f"localhost:{MINIO_PORT}",
                MINIO_ACCESS_KEY,
                MINIO_SECRET_ACCESS_KEY,
                MLFLOW_BUCKET_NAME,
                weight_artifact,
                cfg.model_weight_path,
            )
            save_info_summary(best_run, info_summary_json_file)
            log.info(
                f"Model weight updated successfully. New weight saved to '{cfg.model_weight_path}'. "
                f"Summary information updated and stored in '{info_summary_json_file}'."
            )
            update = True
        else:
            log.info(
                f"No update needed for model weight. Current weight remains unchanged. "
                f"Summary information available at '{info_summary_json_file}'."
            )
            update = False
        log.info("=================== FINISHED WEIGHT VALIDATION TASK. ===================")

        return update


class ImagePushingDockerHub:
    @staticmethod
    def run(update: bool) -> None:
        if update:
            log.info(
                "=================== STARTING THE PROCESS OF PUSHING DOCKER IMAGE TO DOCKER HUB. ==================="
            )
            log.info(f"Start building image '{cfg.image_name}'")
            run_shell_command("docker compose -f docker-compose-app-cpu.yaml build")
            log.info(f"Finish building image '{cfg.image_name}'")
            log.info("Start pushing docker image to Docker Hub.")
            run_shell_command(f"docker push {cfg.image_name}")
            log.info("Finish pushing docker image to Docker Hub.")
            log.info(
                "=================== FINISHED THE PROCESS OF PUSHING DOCKER IMAGE TO DOCKER HUB. ==================="
            )
        else:
            log.info("No better weight to push")


if __name__ == "__main__":
    DataVersion.run()
    ModelTraining.run()
    update = WeightValidation.run()
    ImagePushingDockerHub.run(update)
