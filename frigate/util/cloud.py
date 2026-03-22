"""
云存储服务工具类

提供云存储文件访问能力，用于录像回放时从云端获取文件下载链接
"""

import logging
import os
import time
import threading
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class CloudStorageService:
    """
    云存储服务

    提供：
    - 单例模式，避免重复初始化客户端
    - 下载链接缓存（TTL 1小时）
    - 线程安全的并发访问
    """

    _instance = None
    _config_hash = None
    _lock = threading.Lock()

    def __new__(cls, config):
        """
        单例模式，避免重复初始化

        当配置发生变化时，创建新实例
        """
        # 计算配置哈希
        cloud_config = config.record.cloud_upload
        config_hash = hash((
            cloud_config.openlist_base_url,
            cloud_config.openlist_admin_token,
            cloud_config.openlist_storage_id,
        ))

        with cls._lock:
            if cls._instance is None or cls._config_hash != config_hash:
                cls._instance = super().__new__(cls)
                cls._config_hash = config_hash
                cls._instance._initialized = False

        return cls._instance

    def __init__(self, config):
        """
        初始化云存储服务

        Args:
            config: FrigateConfig 实例
        """
        if self._initialized:
            return

        self.config = config
        self._client = None
        self._download_url_cache: Dict[str, tuple] = {}  # fid -> (url, expire_time)
        self._cache_ttl = 3600  # 1小时缓存
        self._cache_lock = threading.Lock()
        self._initialized = True

        # 初始化 wopan 客户端
        self._init_client()

    def _init_client(self) -> bool:
        """
        初始化 wopan 客户端

        Returns:
            True 表示成功，False 表示失败
        """
        cloud_config = self.config.record.cloud_upload

        if not cloud_config.enabled:
            logger.debug("Cloud upload is disabled")
            return False

        try:
            import sys
            # 添加 wopan-sdk 到路径
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            wopan_sdk_path = os.path.join(project_root, 'wopan-sdk', 'wopan-sdk-python')
            if os.path.exists(wopan_sdk_path) and wopan_sdk_path not in sys.path:
                sys.path.insert(0, wopan_sdk_path)

            from wopan_sdk import WoClient, OpenlistConfig

            openlist_config = OpenlistConfig(
                admin_token=cloud_config.openlist_admin_token,
                storage_id=cloud_config.openlist_storage_id,
                base_url=cloud_config.openlist_base_url,
            )

            self._client = WoClient.default_with_openlist(openlist_config)
            logger.info("CloudStorageService initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize CloudStorageService: {e}")
            self._client = None
            return False

    def get_download_url(self, fid: str) -> Optional[str]:
        """
        获取文件下载链接

        使用缓存机制减少 API 调用，缓存有效期 1 小时

        Args:
            fid: 云文件 ID

        Returns:
            下载链接或 None（获取失败时）
        """
        if not self._client:
            logger.debug("Cloud client not initialized")
            return None

        if not fid:
            logger.debug("Empty fid provided")
            return None

        # 检查缓存
        with self._cache_lock:
            if fid in self._download_url_cache:
                url, expire_time = self._download_url_cache[fid]
                if time.time() < expire_time:
                    logger.debug(f"Cache hit for fid: {fid}...")
                    return url
                else:
                    # 缓存过期，删除
                    del self._download_url_cache[fid]
                    logger.debug(f"Cache expired for fid: {fid}...")

        # 获取新链接
        try:
            from wopan_sdk.consts import SPACE_TYPE_PERSONAL

            # 优先尝试 V2 API
            url = self._get_download_url_v2(fid)
            if url:
                return url

            # 回退到 V1 API
            logger.debug(f"V2 API failed, trying V1 API for fid: {fid}...")
            result = self._client.get_download_url(SPACE_TYPE_PERSONAL, [fid])

            if result and len(result) > 0:
                url = result[0].download_url
                if url:
                    # 缓存结果
                    with self._cache_lock:
                        self._download_url_cache[fid] = (url, time.time() + self._cache_ttl)

                    logger.debug(f"Got download URL via V1 for fid: {fid}...")
                    return url

            logger.warning(f"No download URL returned for fid: {fid}... (result: {result})")
            return None

        except Exception as e:
            logger.error(f"Failed to get download URL for {fid}...: {e}", exc_info=True)
            return None

    def _get_download_url_v2(self, fid: str) -> Optional[str]:
        """
        使用 V2 API 获取文件下载链接

        Args:
            fid: 云文件 ID

        Returns:
            下载链接或 None（获取失败时）
        """
        try:
            result = self._client.get_download_url_v2([fid])

            if result and result.list and len(result.list) > 0:
                url = result.list[0].download_url
                if url:
                    # 缓存结果
                    with self._cache_lock:
                        self._download_url_cache[fid] = (url, time.time() + self._cache_ttl)

                    logger.debug(f"Got download URL via V2 for fid: {fid}...")
                    return url

            logger.debug(f"V2 API returned no URL for fid: {fid}... (result: {result})")
            return None

        except Exception as e:
            logger.debug(f"V2 API failed for fid {fid}...: {e}")
            return None

    def is_available(self) -> bool:
        """
        检查云存储服务是否可用

        Returns:
            True 表示可用，False 表示不可用
        """
        return self._client is not None

    def clear_cache(self) -> None:
        """清空下载链接缓存"""
        with self._cache_lock:
            self._download_url_cache.clear()
            logger.info("Download URL cache cleared")

    def get_cache_size(self) -> int:
        """获取缓存大小"""
        with self._cache_lock:
            return len(self._download_url_cache)


# 模块级单例获取函数
_cloud_service_instance: Optional[CloudStorageService] = None
_cloud_service_lock = threading.Lock()


def get_cloud_storage_service(config) -> Optional[CloudStorageService]:
    """
    获取云存储服务实例（模块级单例）

    Args:
        config: FrigateConfig 实例

    Returns:
        CloudStorageService 实例或 None（如果云存储未启用）
    """
    global _cloud_service_instance

    cloud_config = config.record.cloud_upload
    if not cloud_config.enabled:
        return None

    with _cloud_service_lock:
        if _cloud_service_instance is None:
            try:
                _cloud_service_instance = CloudStorageService(config)
            except Exception as e:
                logger.error(f"Failed to create CloudStorageService: {e}")
                return None

        return _cloud_service_instance
