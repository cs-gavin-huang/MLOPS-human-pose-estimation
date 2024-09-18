# Make all targets .PHONY
.PHONY: $(shell sed -n -e '/^$$/ { n ; /^[^ .\#][^ ]*:/ { s/:.*$$// ; p ; } ; }' $(MAKEFILE_LIST))

SHELL = /usr/bin/env bash
USER_NAME = $(shell whoami)

# 这是需要进行代码验证或格式化的文件夹路径，例如源码文件夹 (src)、日志文件夹 (logs)、配置文件夹 (config) 和应用文件夹 (app)。
SRC_FOLDER_TO_VALIDATE = src
LOG_FOLDER_TO_VALIDATE = logs
CONFIG_FOLDER_TO_VALIDATE = config
APP_FOLDER_TO_VALIDATE = app
#  Docker Compose 文件的路径，用于启动 MinIO、MLflow、FastAPI 和 Jenkins 的 Docker 容器。
MINIO_DOCKER_COMPOSE_YAML = docker-compose-minio.yaml
MLFLOW_MINIO_POSTGRES_DOCKER_COMPOSE_YAML = docker-compose.yaml
APP_DOCKER_COMPOSE_YAML = docker-compose-app-gpu.yaml
JENKINS_DOCKER_COMPOSE_YAML = docker-compose-jenkins.yaml

export

# Returns true if the stem is a non-empty environment variable, or else raises an error.
guard-%:
	@#$(or ${$*}, $(error $* is not set))

# •	sort：使用 isort 对代码进行导入排序，确保所有 Python 文件按规则排序。
# •	sort-check：检查导入排序是否正确，但不会进行修复。
## Sort using isort
sort:
	poetry run isort --atomic $(SRC_FOLDER_TO_VALIDATE) $(LOG_FOLDER_TO_VALIDATE) $(CONFIG_FOLDER_TO_VALIDATE) $(APP_FOLDER_TO_VALIDATE) *.py

## Check sorting using isort
sort-check:
	poetry run isort --check-only --atomic $(SRC_FOLDER_TO_VALIDATE) $(LOG_FOLDER_TO_VALIDATE) $(CONFIG_FOLDER_TO_VALIDATE) $(APP_FOLDER_TO_VALIDATE) *.py

# •	lint：首先格式化和排序代码，然后使用 ruff 进行静态代码分析和自动修复。
# •	lint-check：仅检查代码的格式和排序，不做修改，并运行 ruff 检查。
## Format using ruff
format:
	poetry run ruff format $(SRC_FOLDER_TO_VALIDATE) $(LOG_FOLDER_TO_VALIDATE) $(CONFIG_FOLDER_TO_VALIDATE) $(APP_FOLDER_TO_VALIDATE) *.py

## Check format using ruff
format-check:
	poetry run ruff format --check $(SRC_FOLDER_TO_VALIDATE) $(LOG_FOLDER_TO_VALIDATE) $(CONFIG_FOLDER_TO_VALIDATE) $(APP_FOLDER_TO_VALIDATE) *.py

## Lint code
lint: format sort
	poetry run ruff check --fix $(SRC_FOLDER_TO_VALIDATE) $(LOG_FOLDER_TO_VALIDATE) $(CONFIG_FOLDER_TO_VALIDATE) $(APP_FOLDER_TO_VALIDATE) *.py

## Check linting
lint-check: up format-check sort-check
	poetry run ruff check $(SRC_FOLDER_TO_VALIDATE) $(LOG_FOLDER_TO_VALIDATE) $(CONFIG_FOLDER_TO_VALIDATE) $(APP_FOLDER_TO_VALIDATE) *.py

# •	clean-ruff-cache：清除 ruff 的缓存。
# •	clean-log：删除日志文件夹中的 .log 文件（如果存在）。
## Clean ruff cache
clean-ruff-cache:
	poetry run ruff clean

## Clean logging file
clean-log:
	if [ -n "$$(ls logs/*.log 2>/dev/null)" ]; then \
		rm logs/*.log; \
	fi

# •	down-all：停止所有与 MinIO、MLflow、Jenkins 相关的 Docker 容器。
## Down all docker container
down-all:
	docker compose -f ${MINIO_DOCKER_COMPOSE_YAML} -f ${MLFLOW_MINIO_POSTGRES_DOCKER_COMPOSE_YAML} -f ${JENKINS_DOCKER_COMPOSE_YAML} down
# •	minio：启动 MinIO 容器。
## Run Docker Compose to launch MinIO
minio: down-all
	docker compose -f ${MINIO_DOCKER_COMPOSE_YAML} up -d
# •	mlflow：启动 MLflow 容器，通常用于模型追踪。
## Run Docker Compose to set up MLflow for model tracking
mlflow: down-all
	docker compose -f ${MLFLOW_MINIO_POSTGRES_DOCKER_COMPOSE_YAML} up -d

# •	version-data-first：初始化 DVC（数据版本控制），删除 .dvc/ 目录并运行数据版本化脚本。
## Version data using DVC for the first time
version-data-first:
	rm -rf .dvc/
	poetry run python task_version_data.py

# •	version-data：运行数据版本化脚本 task_version_data.py。
## Version data using DVC
version-data:
	poetry run python task_version_data.py

# •	train：清理日志并运行训练任务 task_train.py。
## Run the training task locally
train: clean-log
	poetry run python task_train.py

# •	download-weight：从 MinIO 下载权重文件。
## Download weight from minio to local folder:
download-weight:
	poetry run python task_download_weight_from_minio.py

# •	jupyter：启动 Jupyter Lab，通常用于交互式编程或数据分析。
## Open jupyter lab
jupyter:
	poetry run jupyter lab

# •	app-local：本地运行 FastAPI 应用，监听 0.0.0.0，端口为 8000。
## Deploy the FastAPI app locally
app-local:
	poetry run uvicorn app.application:app --host 0.0.0.0 --port 8000

# •	app-docker：启动 FastAPI 应用的 Docker 容器。
## Deploy the FastAPI app to a Docker container
app-docker:
	docker compose -f ${APP_DOCKER_COMPOSE_YAML} up -d

## Run the whole pipeline
pipeline: mlflow clean-log
	poetry run python task_all.py
# •	jenkins：启动 Jenkins 容器，用于 CI/CD 管理。
## Run Docker Compose to launch Jenkins
jenkins:
	docker compose -f ${JENKINS_DOCKER_COMPOSE_YAML} up -d

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=36 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
