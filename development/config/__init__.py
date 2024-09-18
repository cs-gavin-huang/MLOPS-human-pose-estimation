# 从 load_cfg.py 文件中导入了 DictDotNotation 类和 cfg 对象。这样，其他模块可以通过导入这个 __init__.py 文件来访问配置。
from .load_cfg import (
    DictDotNotation,
    cfg,
)
