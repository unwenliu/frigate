"""
WoPan SDK 异步客户端扩展
注入异步上传和文件系统方法
"""

from .upload_async import _inject_upload_async_methods
from .api_fs_async import _inject_filesystem_async_methods

# 注入方法到 WoClientAsync 类
_inject_upload_async_methods()
_inject_filesystem_async_methods()

# 导出异步客户端
from .client_async import WoClientAsync
from .upload_async import Upload2CFile, Upload2COption

__all__ = ["WoClientAsync", "Upload2CFile", "Upload2COption"]
