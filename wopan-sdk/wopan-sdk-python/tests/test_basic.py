"""
WoPan SDK 基础测试
"""

import unittest
from wopan_sdk import WoClient, Upload2CFile, Upload2COption
from wopan_sdk.consts import *
from wopan_sdk.exceptions import WoPanException, WoPanCryptoException
from wopan_sdk.crypto import Crypto
import io


class TestCrypto(unittest.TestCase):
    """测试加密功能"""

    def setUp(self):
        """设置测试环境"""
        self.crypto = Crypto()

    def test_set_access_token(self):
        """测试设置访问令牌"""
        # 正常的令牌
        token = "12345678901234567890"
        self.crypto.set_access_token(token)
        self.assertIsNotNone(self.crypto.access_key)

        # 过短的令牌
        with self.assertRaises(WoPanCryptoException):
            self.crypto.set_access_token("short")

    def test_encrypt_decrypt(self):
        """测试加密解密"""
        # 测试 API User 渠道加密
        original = "Hello, WoPan!"
        encrypted = self.crypto.user_encrypt(original)
        decrypted = self.crypto.user_decrypt(encrypted)
        self.assertEqual(original, decrypted)

        # 测试 WoHome 渠道加密（需要先设置 access_token）
        self.crypto.set_access_token("12345678901234567890")
        encrypted = self.crypto.wo_home_encrypt(original)
        decrypted = self.crypto.wo_home_decrypt(encrypted)
        self.assertEqual(original, decrypted)


class TestWoClient(unittest.TestCase):
    """测试客户端功能"""

    def setUp(self):
        """设置测试环境"""
        self.client = WoClient.default()

    def test_client_initialization(self):
        """测试客户端初始化"""
        # 测试默认创建
        client = WoClient.default()
        self.assertIsNotNone(client)

        # 测试使用访问令牌创建
        client = WoClient.default_with_access_token("test_token_1234567890")
        self.assertEqual(client.access_token, "test_token_1234567890")

    def test_set_access_token(self):
        """测试设置访问令牌"""
        token = "test_access_token_1234567890"
        self.client.set_access_token(token)
        self.assertEqual(self.client.access_token, token)

    def test_get_file_type(self):
        """测试获取文件类型"""
        # 视频文件
        self.assertEqual(self.client.get_file_type("video.mp4"), "1")
        self.assertEqual(self.client.get_file_type("video.avi"), "1")

        # 图片文件
        self.assertEqual(self.client.get_file_type("image.jpg"), "2")
        self.assertEqual(self.client.get_file_type("image.png"), "2")

        # 音频文件
        self.assertEqual(self.client.get_file_type("audio.mp3"), "3")

        # 文档文件
        self.assertEqual(self.client.get_file_type("document.pdf"), "4")

        # 未知文件
        self.assertEqual(self.client.get_file_type("unknown.xyz"), "5")
        self.assertEqual(self.client.get_file_type("noextension"), "5")


class TestUploadFile(unittest.TestCase):
    """测试上传文件类"""

    def test_upload_file_creation(self):
        """测试创建上传文件对象"""
        content = io.BytesIO(b"test content")
        upload_file = Upload2CFile(
            name="test.txt",
            size=12,
            content=content,
            content_type="text/plain",
        )

        self.assertEqual(upload_file.name, "test.txt")
        self.assertEqual(upload_file.size, 12)
        self.assertEqual(upload_file.content_type, "text/plain")


class TestUploadOption(unittest.TestCase):
    """测试上传选项类"""

    def test_upload_option_defaults(self):
        """测试上传选项默认值"""
        option = Upload2COption()
        self.assertIsNone(option.on_progress)
        self.assertEqual(option.retry_times, 3)
        self.assertIsNone(option.on_retry)

    def test_upload_option_custom(self):
        """测试自定义上传选项"""
        def progress_callback(current, total):
            pass

        def retry_callback(err, name, index, size):
            pass

        option = Upload2COption(
            on_progress=progress_callback, retry_times=5, on_retry=retry_callback
        )

        self.assertEqual(option.on_progress, progress_callback)
        self.assertEqual(option.retry_times, 5)
        self.assertEqual(option.on_retry, retry_callback)


class TestConstants(unittest.TestCase):
    """测试常量定义"""

    def test_space_types(self):
        """测试空间类型常量"""
        self.assertEqual(SPACE_TYPE_PERSONAL, "0")
        self.assertEqual(SPACE_TYPE_FAMILY, "1")
        self.assertEqual(SPACE_TYPE_PRIVATE, "4")

    def test_sort_rules(self):
        """测试排序规则常量"""
        self.assertEqual(SORT_NAME_ASC, 1)
        self.assertEqual(SORT_NAME_DESC, 2)
        self.assertEqual(SORT_SIZE_ASC, 3)
        self.assertEqual(SORT_SIZE_DESC, 4)
        self.assertEqual(SORT_TIME_ASC, 5)
        self.assertEqual(SORT_TIME_DESC, 6)


if __name__ == "__main__":
    unittest.main()
