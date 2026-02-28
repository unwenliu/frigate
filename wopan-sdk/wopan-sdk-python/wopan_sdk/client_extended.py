"""
WoPan SDK 客户端扩展
注入上传和文件系统方法
"""

from .upload import _inject_upload_methods
from .api_fs import _inject_filesystem_methods

# 注入方法到 WoClient 类
_inject_upload_methods()
_inject_filesystem_methods()

# 导出客户端
from .client import WoClient
from .upload import Upload2CFile, Upload2COption

__all__ = ["WoClient", "Upload2CFile", "Upload2COption"]
