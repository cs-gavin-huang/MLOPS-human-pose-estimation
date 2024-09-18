from pathlib import Path
from typing import Optional

import yaml

# 1. ROOT 和 CONFIG_FILE_PATH
# 	•	ROOT = Path(__file__).resolve().parent.parent：这里使用 pathlib.Path 来获取当前文件的父目录（通常是项目的根目录）。
# 	•	CONFIG_FILE_PATH = ROOT / "config" / "config.yaml"：定义了配置文件 config.yaml 的路径，位于项目根目录下的 config 文件夹中。
ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE_PATH = ROOT / "config" / "config.yaml"

# 这个类继承自 Python 的内置 dict，目的是允许通过“点操作符”（dot notation）访问字典中的键值。
# 比如：cfg.data_root_path 就像访问对象的属性一样，而不需要像普通字典那样 cfg['data_root_path']。
class DictDotNotation(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


# •	该函数用于定位配置文件 config.yaml，如果文件存在则返回文件路径，否则抛出 FileNotFoundError 异常。
def _find_config_file() -> Path:
    """Locate the configuration file."""
    # •	if CONFIG_FILE_PATH.is_file()：检查配置文件是否存在。
    if CONFIG_FILE_PATH.is_file():
        return CONFIG_FILE_PATH
    raise FileNotFoundError(f"Config file not found at {CONFIG_FILE_PATH}")

# 该函数用于加载配置文件的内容。
# 	•首先检查是否传入了配置文件路径 cfg_path，如果没有传入，则调用 _find_config_file() 来寻找默认的配置文件。
# 	•打开并读取 YAML 文件内容，如果内容无效或为空，则抛出 ValueError。
def load_config_file(cfg_path: Optional[Path] = None) -> Optional[dict]:
    if not cfg_path:
        cfg_path = _find_config_file()

    if cfg_path:
        with open(cfg_path, "r") as f:
            yaml_data = yaml.safe_load(f)
            if not yaml_data:
                raise ValueError("Invalid or empty YAML configuration")
            return yaml_data


# •	该函数调用 load_config_file 来加载配置文件，并将其转换为 DictDotNotation，从而允许使用“点操作符”来访问配置参数。
# •	返回值是一个 DictDotNotation 对象，包含配置文件中的所有键值。
def configure() -> DictDotNotation:
    cfg = load_config_file()
    cfg = DictDotNotation(cfg)
    return cfg


# •	cfg = configure()：调用 configure 函数，并将其返回的配置对象赋值给 cfg。这意味着你可以在项目中的任何地方使用 cfg 来访问配置文件中的内容。
cfg = configure()
