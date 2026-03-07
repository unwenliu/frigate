"""
OpenList 自动刷新功能测试
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
import threading
import time
from wopan_sdk import WoClient, OpenlistConfig
from wopan_sdk.exceptions import OpenListAuthException


class TestOpenListAutoRefresh(unittest.TestCase):
    """测试 OpenList 自动刷新 access_token 功能"""

    @patch('wopan_sdk.client.requests.get')
    def test_config_is_cached(self, mock_get):
        """测试 OpenList 配置被正确缓存"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "initial-token-12345678abcd"  # >= 16 字符
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # 创建客户端
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))

        # 验证客户端创建成功
        self.assertIsNotNone(client)
        self.assertEqual(client.access_token, "initial-token-12345678abcd")

        # 验证配置被缓存（通过检查私有字段）
        self.assertIsNotNone(client._openlist_config)
        self.assertEqual(client._openlist_config.admin_token, "test-admin-token")
        self.assertEqual(client._openlist_config.storage_id, 123)

    @patch('wopan_sdk.client.requests.get')
    def test_refresh_from_openlist_success(self, mock_get):
        """测试从 OpenList 成功刷新令牌"""
        # 第一次调用用于初始化
        mock_response_init = Mock()
        mock_response_init.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "initial-token-12345678"
                }
            }
        }
        mock_response_init.raise_for_status = Mock()

        # 第二次调用用于刷新
        mock_response_refresh = Mock()
        mock_response_refresh.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "refreshed-token-12345678"
                }
            }
        }
        mock_response_refresh.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_init, mock_response_refresh]

        # 创建客户端
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))

        # 验证初始令牌
        self.assertEqual(client.access_token, "initial-token-12345678")

        # 调用刷新令牌方法
        client._refresh_from_openlist()

        # 验证令牌已刷新
        self.assertEqual(client.access_token, "refreshed-token-12345678")

        # 验证请求次数
        self.assertEqual(mock_get.call_count, 2)

    @patch('wopan_sdk.client.requests.get')
    def test_refresh_from_openlist_api_error(self, mock_get):
        """测试刷新令牌时 API 返回错误"""
        # 第一次调用成功（初始化）
        mock_response_init = Mock()
        mock_response_init.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "initial-token-12345678"
                }
            }
        }
        mock_response_init.raise_for_status = Mock()

        # 第二次调用返回错误
        mock_response_error = Mock()
        mock_response_error.json.return_value = {
            "code": 401,
            "message": "Unauthorized: Token expired"
        }
        mock_response_error.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_init, mock_response_error]

        # 创建客户端
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))

        # 调用刷新令牌方法应该抛出异常
        with self.assertRaises(OpenListAuthException) as context:
            client._refresh_from_openlist()

        self.assertIn("code=401", str(context.exception))

    @patch('wopan_sdk.client.requests.get')
    def test_refresh_from_openlist_empty_token(self, mock_get):
        """测试刷新令牌时返回空令牌"""
        # 初始化成功
        mock_response_init = Mock()
        mock_response_init.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "initial-token-12345678"
                }
            }
        }
        mock_response_init.raise_for_status = Mock()

        # 刷新返回空令牌
        mock_response_empty = Mock()
        mock_response_empty.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": ""
                }
            }
        }
        mock_response_empty.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_init, mock_response_empty]

        # 创建客户端
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))

        # 调用刷新令牌方法应该抛出异常
        with self.assertRaises(OpenListAuthException) as context:
            client._refresh_from_openlist()

        self.assertIn("empty access_token", str(context.exception))

    @patch('wopan_sdk.client.requests.get')
    def test_refresh_from_openlist_network_error(self, mock_get):
        """测试刷新令牌时网络请求失败"""
        import requests

        # 初始化成功
        mock_response_init = Mock()
        mock_response_init.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "initial-token-12345678"
                }
            }
        }
        mock_response_init.raise_for_status = Mock()

        # 刷新时网络错误
        mock_get.side_effect = [
            mock_response_init,
            requests.RequestException("Connection refused")
        ]

        # 创建客户端
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))

        # 调用刷新令牌方法应该抛出异常
        with self.assertRaises(OpenListAuthException) as context:
            client._refresh_from_openlist()

        self.assertIn("Failed to refresh token", str(context.exception))

    @patch('wopan_sdk.client.requests.get')
    def test_refresh_token_uses_openlist(self, mock_get):
        """测试 RefreshToken 优先使用 OpenList"""
        # 初始化成功
        mock_response_init = Mock()
        mock_response_init.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "initial-token-12345678"
                }
            }
        }
        mock_response_init.raise_for_status = Mock()

        # 刷新成功
        mock_response_refresh = Mock()
        mock_response_refresh.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "refreshed-token-12345678"
                }
            }
        }
        mock_response_refresh.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_init, mock_response_refresh]

        # 创建客户端
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))

        # 验证初始令牌
        self.assertEqual(client.access_token, "initial-token-12345678")

        # 调用 RefreshToken
        client._refresh_token()

        # 验证令牌已刷新
        self.assertEqual(client.access_token, "refreshed-token-12345678")

        # 验证使用了 OpenList（通过请求次数）
        self.assertEqual(mock_get.call_count, 2)

    @patch('wopan_sdk.client.requests.get')
    def test_refresh_token_fallback_to_callback(self, mock_get):
        """测试 RefreshToken 回退到回调函数"""
        # 初始化成功
        mock_response_init = Mock()
        mock_response_init.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "initial-token-12345678"
                }
            }
        }
        mock_response_init.raise_for_status = Mock()
        mock_get.return_value = mock_response_init

        # 创建没有 OpenList 配置的客户端
        client = WoClient(access_token="initial-token-12345678")
        self.assertIsNone(client._openlist_config)

        # 设置回调函数
        callback_called = threading.Event()

        def mock_callback(access_token, refresh_token):
            client.set_access_token("callback-token-12345678")
            callback_called.set()

        client.on_refresh_token = mock_callback

        # 调用 RefreshToken
        client._refresh_token()

        # 等待回调执行
        callback_called.wait(timeout=1)

        # 验证回调被调用且令牌已更新
        self.assertTrue(callback_called.is_set())
        self.assertEqual(client.access_token, "callback-token-12345678")

    @patch('wopan_sdk.client.requests.get')
    def test_concurrent_refresh_safety(self, mock_get):
        """测试并发刷新的线程安全性"""
        request_count = [0]  # 使用列表以便在闭包中修改
        lock = threading.Lock()

        def create_mock_response(token):
            """创建模拟响应"""
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 200,
                "message": "success",
                "data": {
                    "token_info": {
                        "access_token": token
                    }
                }
            }
            mock_response.raise_for_status = Mock()

            # 模拟网络延迟
            original_get = mock_response.raise_for_status

            def delayed_get():
                with lock:
                    request_count[0] += 1
                time.sleep(0.01)  # 10ms 延迟
                return original_get()

            mock_response.raise_for_status = delayed_get

            return mock_response

        # 设置多个响应
        responses = [
            create_mock_response(f"token-{i:02d}-1234567890abcd")
            for i in range(20)  # 足够的响应数量
        ]
        mock_get.side_effect = responses

        # 创建客户端
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))

        # 并发调用刷新
        num_threads = 10
        threads = []
        errors = []

        def refresh_worker():
            try:
                client._refresh_token()
            except Exception as e:
                errors.append(e)

        for _ in range(num_threads):
            thread = threading.Thread(target=refresh_worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=5)

        # 检查是否有错误
        if errors:
            self.fail(f"Errors occurred during concurrent refresh: {errors}")

        # 验证令牌非空
        self.assertIsNotNone(client.access_token)
        self.assertNotEqual(client.access_token, "")

        # 验证请求次数合理（应该等于线程数，因为有锁保护）
        # 注意：这里可能不完全是 num_threads，因为初始化也用了一次
        self.assertLessEqual(request_count[0], num_threads + 1)

    @patch('wopan_sdk.client.requests.get')
    def test_multiple_refreshes(self, mock_get):
        """测试多次刷新令牌"""
        # 创建多个响应
        responses = []
        for i in range(6):  # 1 次初始化 + 5 次刷新
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 200,
                "message": "success",
                "data": {
                    "token_info": {
                        "access_token": f"token-{i:02d}-1234567890ab"
                    }
                }
            }
            mock_response.raise_for_status = Mock()
            responses.append(mock_response)

        mock_get.side_effect = responses

        # 创建客户端
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))

        # 验证初始令牌
        self.assertEqual(client.access_token, "token-00-1234567890ab")

        # 多次刷新
        for i in range(1, 6):
            client._refresh_from_openlist()
            self.assertEqual(client.access_token, f"token-{i:02d}-1234567890ab")

        # 验证请求次数
        self.assertEqual(mock_get.call_count, 6)

    @patch('wopan_sdk.client.requests.get')
    def test_refresh_with_custom_base_url(self, mock_get):
        """测试使用自定义 BaseURL 刷新令牌"""
        custom_url = "https://custom.openlist.com"

        # 初始化响应
        mock_response_init = Mock()
        mock_response_init.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "initial-token-12345678"
                }
            }
        }
        mock_response_init.raise_for_status = Mock()

        # 刷新响应
        mock_response_refresh = Mock()
        mock_response_refresh.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "refreshed-token-12345678"
                }
            }
        }
        mock_response_refresh.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_init, mock_response_refresh]

        # 创建客户端（使用自定义 URL）
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123,
            base_url=custom_url
        ))

        # 刷新令牌
        client._refresh_from_openlist()

        # 验证使用了自定义 URL
        call_args = mock_get.call_args_list
        # 第一次调用（初始化）和第二次调用（刷新）都应该使用自定义 URL
        for args in call_args:
            url = args[0][0] if args[0] else args[1].get('url', '')
            self.assertTrue(url.startswith(custom_url))

    @patch('wopan_sdk.client.requests.get')
    def test_refresh_with_custom_timeout(self, mock_get):
        """测试使用自定义超时刷新令牌"""
        custom_timeout = 120

        mock_response_init = Mock()
        mock_response_init.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "initial-token-12345678"
                }
            }
        }
        mock_response_init.raise_for_status = Mock()

        mock_response_refresh = Mock()
        mock_response_refresh.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "refreshed-token-12345678"
                }
            }
        }
        mock_response_refresh.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_init, mock_response_refresh]

        # 创建客户端（使用自定义超时）
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123,
            timeout=custom_timeout
        ))

        # 刷新令牌
        client._refresh_from_openlist()

        # 验证使用了自定义超时
        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs["timeout"], custom_timeout)

    @patch('wopan_sdk.client.requests.get')
    def test_refresh_with_debug_mode(self, mock_get):
        """测试调试模式下的刷新"""
        mock_response_init = Mock()
        mock_response_init.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "initial-token-12345678"
                }
            }
        }
        mock_response_init.raise_for_status = Mock()

        mock_response_refresh = Mock()
        mock_response_refresh.json.return_value = {
            "code": 200,
            "message": "success",
            "data": {
                "token_info": {
                    "access_token": "refreshed-token-12345678"
                }
            }
        }
        mock_response_refresh.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_init, mock_response_refresh]

        # 创建客户端（启用调试模式）
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))
        client.debug = True

        # 刷新令牌（应该打印调试信息）
        # 这里只是验证不会出错，实际输出需要手动检查
        try:
            client._refresh_from_openlist()
            self.assertEqual(client.access_token, "refreshed-token-12345678")
        except Exception as e:
            self.fail(f"Refresh with debug mode failed: {e}")

    @patch('wopan_sdk.client.requests.get')
    def test_refresh_lock_prevents_race(self, mock_get):
        """测试刷新锁防止竞态条件"""
        # 创建会延迟的响应
        def create_slow_response(token):
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 200,
                "message": "success",
                "data": {
                    "token_info": {
                        "access_token": token
                    }
                }
            }

            def slow_raise_for_status():
                time.sleep(0.05)  # 50ms 延迟

            mock_response.raise_for_status = slow_raise_for_status
            return mock_response

        responses = [
            create_slow_response(f"token-{i:02d}-1234567890abcd")
            for i in range(15)
        ]
        mock_get.side_effect = responses

        # 创建客户端
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))

        # 快速连续调用多次刷新
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=client._refresh_token)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=10)

        # 验证最终状态一致
        self.assertIsNotNone(client.access_token)

        # 验证请求次数合理（由于锁的存在，应该少于或等于线程数+初始化）
        # 这里只验证不会崩溃


class TestRefreshTokenIntegration(unittest.TestCase):
    """集成测试：刷新令牌的完整流程"""

    @patch('wopan_sdk.client.requests.get')
    def test_full_refresh_cycle(self, mock_get):
        """测试完整的刷新周期"""
        # 模拟令牌生命周期
        responses = [
            # 初始化
            Mock(**{
                "json.return_value": {
                    "code": 200,
                    "message": "success",
                    "data": {"token_info": {"access_token": "token-init-1234567890abc"}}
                },
                "raise_for_status": Mock()
            }),
            # 第一次刷新
            Mock(**{
                "json.return_value": {
                    "code": 200,
                    "message": "success",
                    "data": {"token_info": {"access_token": "token-refresh-1-12345678"}}
                },
                "raise_for_status": Mock()
            }),
            # 第二次刷新
            Mock(**{
                "json.return_value": {
                    "code": 200,
                    "message": "success",
                    "data": {"token_info": {"access_token": "token-refresh-2-12345678"}}
                },
                "raise_for_status": Mock()
            }),
        ]

        mock_get.side_effect = responses

        # 创建客户端
        client = WoClient.default_with_openlist(OpenlistConfig(
            admin_token="test-admin-token",
            storage_id=123
        ))

        # 验证初始状态
        self.assertEqual(client.access_token, "token-init-1234567890abc")

        # 第一次刷新
        client._refresh_token()
        self.assertEqual(client.access_token, "token-refresh-1-12345678")

        # 第二次刷新
        client._refresh_token()
        self.assertEqual(client.access_token, "token-refresh-2-12345678")

        # 验证请求次数
        self.assertEqual(mock_get.call_count, 3)


if __name__ == "__main__":
    unittest.main()
