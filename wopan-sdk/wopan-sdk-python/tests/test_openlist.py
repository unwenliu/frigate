"""
OpenList 相关功能测试
"""

import unittest
from unittest.mock import patch, Mock
from wopan_sdk import WoClient, OpenlistConfig
from wopan_sdk.exceptions import OpenListAuthException
from wopan_sdk.consts import DEFAULT_OPENLIST_BASE_URL, DEFAULT_OPENLIST_TIMEOUT


class TestOpenlistConfig(unittest.TestCase):
    """测试 OpenlistConfig 配置类"""

    def test_config_creation_required_fields(self):
        """测试创建配置对象（必填字段）"""
        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        )

        self.assertEqual(config.admin_token, "test-admin-token")
        self.assertEqual(config.storage_id, 123)

    def test_config_creation_with_all_fields(self):
        """测试创建配置对象（所有字段）"""
        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123,
            base_url="https://custom.openlist.com",
            timeout=60,
            verify_ssl=True
        )

        self.assertEqual(config.base_url, "https://custom.openlist.com")
        self.assertEqual(config.timeout, 60)
        self.assertTrue(config.verify_ssl)

    def test_config_defaults(self):
        """测试配置默认值"""
        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        )

        self.assertEqual(config.base_url, "")
        self.assertEqual(config.timeout, DEFAULT_OPENLIST_TIMEOUT)
        self.assertFalse(config.verify_ssl)  # 默认与项目风格保持一致

    def test_config_is_frozen(self):
        """测试配置类是不可变的"""
        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        )

        # 尝试修改应该抛出异常
        with self.assertRaises(Exception):  # FrozenInstanceError
            config.admin_token = "new-token"


class TestDefaultWithOpenlist(unittest.TestCase):
    """测试 default_with_openlist 方法"""

    def setUp(self):
        """设置测试环境"""
        self.valid_config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        )

    @patch('wopan_sdk.client.requests.get')
    def test_success(self, mock_get):
        """测试成功获取令牌"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "test-access-token-12345"  # >= 16 字符
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # 调用方法
        client = WoClient.default_with_openlist(self.valid_config)

        # 验证
        self.assertIsNotNone(client)
        self.assertEqual(client.access_token, "test-access-token-12345")

        # 验证请求参数
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("id", call_args.kwargs["params"])
        self.assertEqual(call_args.kwargs["params"]["id"], 123)
        self.assertEqual(call_args.kwargs["headers"]["Authorization"], "test-admin-token")

    @patch('wopan_sdk.client.requests.get')
    def test_custom_base_url(self, mock_get):
        """测试自定义 BaseURL"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {"token_info": {"access_token": "custom-url-token-12345678"}}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123,
            base_url="https://custom.openlist.com"
        )

        client = WoClient.default_with_openlist(config)

        self.assertEqual(client.access_token, "custom-url-token-12345678")

        # 验证使用了自定义 URL
        call_args = mock_get.call_args
        self.assertTrue(call_args.args[0].startswith("https://custom.openlist.com"))

    @patch('wopan_sdk.client.requests.get')
    def test_empty_admin_token(self, mock_get):
        """测试空 admin_token"""
        config = OpenlistConfig(
            admin_token="",
            storage_id=123
        )

        with self.assertRaises(OpenListAuthException) as context:
            WoClient.default_with_openlist(config)

        self.assertIn("admin_token is required", str(context.exception))
        mock_get.assert_not_called()

    @patch('wopan_sdk.client.requests.get')
    def test_empty_storage_id(self, mock_get):
        """测试零值 storage_id"""
        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=0
        )

        with self.assertRaises(OpenListAuthException) as context:
            WoClient.default_with_openlist(config)

        self.assertIn("storage_id must be a positive integer", str(context.exception))
        mock_get.assert_not_called()

    def test_negative_storage_id(self):
        """测试负数 storage_id"""
        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=-1
        )

        with self.assertRaises(OpenListAuthException) as context:
            WoClient.default_with_openlist(config)

        self.assertIn("storage_id must be a positive integer", str(context.exception))

    @patch('wopan_sdk.client.requests.get')
    def test_api_error_response(self, mock_get):
        """测试 API 返回错误"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 401,
            "message": "Unauthorized: Invalid admin token"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with self.assertRaises(OpenListAuthException) as context:
            WoClient.default_with_openlist(self.valid_config)

        self.assertIn("OpenList API returned error", str(context.exception))
        self.assertIn("code=401", str(context.exception))

    @patch('wopan_sdk.client.requests.get')
    def test_empty_access_token(self, mock_get):
        """测试 API 返回空 access_token"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": ""
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with self.assertRaises(OpenListAuthException) as context:
            WoClient.default_with_openlist(self.valid_config)

        self.assertIn("empty access_token", str(context.exception))

    @patch('wopan_sdk.client.requests.get')
    def test_missing_token_info(self, mock_get):
        """测试响应中缺少 token_info"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with self.assertRaises(OpenListAuthException) as context:
            WoClient.default_with_openlist(self.valid_config)

        self.assertIn("empty access_token", str(context.exception))

    @patch('wopan_sdk.client.requests.get')
    def test_network_error(self, mock_get):
        """测试网络请求失败"""
        import requests
        mock_get.side_effect = requests.RequestException("Connection refused")

        with self.assertRaises(OpenListAuthException) as context:
            WoClient.default_with_openlist(self.valid_config)

        self.assertIn("Failed to request OpenList API", str(context.exception))

    @patch('wopan_sdk.client.requests.get')
    def test_json_parse_error(self, mock_get):
        """测试 JSON 解析失败"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with self.assertRaises(OpenListAuthException) as context:
            WoClient.default_with_openlist(self.valid_config)

        self.assertIn("Failed to parse OpenList API response", str(context.exception))

    @patch('wopan_sdk.client.requests.get')
    def test_large_storage_id(self, mock_get):
        """测试大整数 storage_id"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {"token_info": {"access_token": "large-token-12345678"}}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # 使用大整数的 storage_id
        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=999999
        )

        client = WoClient.default_with_openlist(config)

        self.assertEqual(client.access_token, "large-token-12345678")

        # 验证参数正确传递（requests 会自动转换）
        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs["params"]["id"], 999999)

    @patch('wopan_sdk.client.requests.get')
    def test_verify_ssl_true(self, mock_get):
        """测试 SSL 验证启用"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {"token_info": {"access_token": "ssl-token-123456789"}}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123,
            verify_ssl=True
        )

        WoClient.default_with_openlist(config)

        # 验证 verify_ssl 参数
        call_args = mock_get.call_args
        self.assertTrue(call_args.kwargs["verify"])

    @patch('wopan_sdk.client.requests.get')
    def test_verify_ssl_false(self, mock_get):
        """测试 SSL 验证禁用"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {"token_info": {"access_token": "no-ssl-token-12345678"}}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123,
            verify_ssl=False
        )

        WoClient.default_with_openlist(config)

        # 验证 verify_ssl 参数
        call_args = mock_get.call_args
        self.assertFalse(call_args.kwargs["verify"])

    @patch('wopan_sdk.client.requests.get')
    def test_custom_timeout(self, mock_get):
        """测试自定义超时"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {"token_info": {"access_token": "timeout-token-12345678"}}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        config = OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123,
            timeout=120
        )

        WoClient.default_with_openlist(config)

        # 验证 timeout 参数
        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs["timeout"], 120)


class TestDefaultWithOpenlistSimple(unittest.TestCase):
    """测试 default_with_openlist_simple 方法"""

    @patch('wopan_sdk.client.WoClient.default_with_openlist')
    def test_success(self, mock_default_with_openlist):
        """测试简化版本成功获取令牌"""
        # 创建模拟客户端
        mock_client = Mock()
        mock_client.access_token = "simple-token"
        mock_default_with_openlist.return_value = mock_client

        # 调用简化方法
        client = WoClient.default_with_openlist_simple("admin-token", 123)

        # 验证
        self.assertIsNotNone(client)
        self.assertEqual(client.access_token, "simple-token")

        # 验证正确调用了完整方法
        mock_default_with_openlist.assert_called_once()
        call_args = mock_default_with_openlist.call_args[0][0]
        self.assertIsInstance(call_args, OpenlistConfig)
        self.assertEqual(call_args.admin_token, "admin-token")
        self.assertEqual(call_args.storage_id, 123)


class TestOpenListAuthException(unittest.TestCase):
    """测试 OpenListAuthException 异常类"""

    def test_exception_creation(self):
        """测试创建异常"""
        exception = OpenListAuthException("Test error message")
        self.assertEqual(str(exception), "Test error message")

    def test_exception_is_wopan_exception(self):
        """测试异常继承关系"""
        from wopan_sdk.exceptions import WoPanException

        exception = OpenListAuthException("Test error")
        self.assertIsInstance(exception, WoPanException)

    def test_exception_raise_and_catch(self):
        """测试抛出和捕获异常"""
        with self.assertRaises(OpenListAuthException):
            raise OpenListAuthException("Test error")


if __name__ == "__main__":
    unittest.main()
