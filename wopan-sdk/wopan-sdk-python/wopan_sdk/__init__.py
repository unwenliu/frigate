"""
WoPan SDK for Python
网盘 Python SDK
"""

from .client import (
    WoClient,
    OpenlistConfig,
    FamilyUserCurrentEncodeData,
    File,
    SystemDir,
)
from .consts import *
from .exceptions import *
from .upload import Upload2CFile, Upload2COption

# 导入扩展模块以注入方法
from . import client_extended

# 导入异步客户端扩展（会自动注入异步方法）
from . import client_extended_async
from .client_async import WoClientAsync

__version__ = "0.1.0"
__all__ = [
    "WoClient",
    "WoClientAsync",
    "Upload2CFile",
    "Upload2COption",
    "WoPanException",
    "WoPanAuthException",
    "OpenListAuthException",
    "WoPanUploadException",
    "OpenlistConfig",
]
