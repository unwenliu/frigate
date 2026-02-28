"""
WoPan SDK 异常类定义
"""


class WoPanException(Exception):
    """WoPan SDK 基础异常类"""

    pass


class WoPanAuthException(WoPanException):
    """认证异常"""

    pass


class OpenListAuthException(WoPanException):
    """OpenList 管理后台认证异常"""

    pass


class WoPanUploadException(WoPanException):
    """上传异常"""

    pass


class WoPanFileException(WoPanException):
    """文件操作异常"""

    pass


class WoPanCryptoException(WoPanException):
    """加密异常"""

    pass
