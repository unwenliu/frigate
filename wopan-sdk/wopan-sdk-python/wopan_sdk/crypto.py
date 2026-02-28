"""
WoPan SDK 加密功能模块
实现 AES 加密/解密功能
"""

import base64
from typing import Optional
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from .consts import DEFAULT_IV, DEFAULT_CLIENT_SECRET, CHANNEL_API_USER
from .exceptions import WoPanCryptoException


class Crypto:
    """加密工具类"""

    def __init__(self, client_secret: Optional[str] = None, iv: Optional[str] = None):
        """
        初始化加密工具

        Args:
            client_secret: 客户端密钥
            iv: 初始化向量
        """
        self.key = (client_secret or DEFAULT_CLIENT_SECRET).encode("utf-8")
        self.iv = (iv or DEFAULT_IV).encode("utf-8")
        self.access_key: Optional[bytes] = None

    def set_access_token(self, token: str) -> None:
        """
        设置访问令牌并生成 access_key

        Args:
            token: 访问令牌

        Raises:
            WoPanCryptoException: 如果令牌无效
        """
        if len(token) < 16:
            raise WoPanCryptoException("Invalid access token, length must be >= 16")
        self.access_key = token[:16].encode("utf-8")

    def _get_key(self, channel: str) -> bytes:
        """
        根据渠道获取加密密钥

        Args:
            channel: 渠道类型

        Returns:
            加密密钥
        """
        if channel == CHANNEL_API_USER:
            return self.key
        return self.access_key or self.key

    def encrypt_bytes(self, data: bytes, channel: str = CHANNEL_API_USER) -> str:
        """
        加密字节数据

        Args:
            data: 待加密的字节数据
            channel: 渠道类型

        Returns:
            Base64 编码的加密数据

        Raises:
            WoPanCryptoException: 加密失败
        """
        try:
            key = self._get_key(channel)
            cipher = AES.new(key, AES.MODE_CBC, self.iv)
            padded_data = pad(data, AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            return base64.b64encode(encrypted).decode("utf-8")
        except Exception as e:
            raise WoPanCryptoException(f"Encryption failed: {str(e)}")

    def encrypt(self, content: str, channel: str = CHANNEL_API_USER) -> str:
        """
        加密字符串

        Args:
            content: 待加密的字符串
            channel: 渠道类型

        Returns:
            Base64 编码的加密数据
        """
        return self.encrypt_bytes(content.encode("utf-8"), channel)

    def decrypt(self, content: str, channel: str = CHANNEL_API_USER) -> str:
        """
        解密字符串

        Args:
            content: Base64 编码的加密数据
            channel: 渠道类型

        Returns:
            解密后的字符串

        Raises:
            WoPanCryptoException: 解密失败
        """
        try:
            key = self._get_key(channel)
            cipher = AES.new(key, AES.MODE_CBC, self.iv)
            encrypted_data = base64.b64decode(content)
            decrypted = cipher.decrypt(encrypted_data)
            unpadded_data = unpad(decrypted, AES.block_size)
            return unpadded_data.decode("utf-8")
        except Exception as e:
            raise WoPanCryptoException(f"Decryption failed: {str(e)}")

    def user_encrypt(self, content: str) -> str:
        """
        用户渠道加密

        Args:
            content: 待加密的字符串

        Returns:
            Base64 编码的加密数据
        """
        return self.encrypt(content, CHANNEL_API_USER)

    def user_decrypt(self, content: str) -> str:
        """
        用户渠道解密

        Args:
            content: Base64 编码的加密数据

        Returns:
            解密后的字符串
        """
        return self.decrypt(content, CHANNEL_API_USER)

    def wo_home_encrypt(self, content: str) -> str:
        """
        WoHome 渠道加密

        Args:
            content: 待加密的字符串

        Returns:
            Base64 编码的加密数据
        """
        return self.encrypt(content, "wohome")

    def wo_home_decrypt(self, content: str) -> str:
        """
        WoHome 渠道解密

        Args:
            content: Base64 编码的加密数据

        Returns:
            解密后的字符串
        """
        return self.decrypt(content, "wohome")
