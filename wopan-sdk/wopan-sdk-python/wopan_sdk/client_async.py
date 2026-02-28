"""
WoPan SDK 异步客户端核心类
"""

import json
import hashlib
import time
import random
import aiohttp
import asyncio
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from .crypto import Crypto
from .consts import *
from .exceptions import WoPanException, WoPanAuthException


@dataclass
class File:
    """文件信息"""

    family_id: Optional[int]
    fid: str
    creator: str
    size: int
    create_time: str
    name: str
    shooting_time: str
    id: str
    type: int
    thumb_url: str
    file_type: str


@dataclass
class QueryAllFilesData:
    """查询所有文件结果"""

    files: list[File]


@dataclass
class CreateDirectoryData:
    """创建目录结果"""

    id: str


@dataclass
class GetDownloadUrlData:
    """获取下载链接结果"""

    fid: str
    download_url: str


@dataclass
class GetDownloadUrlV2Data:
    """获取下载链接 V2 结果"""

    type: int
    list: list[GetDownloadUrlData]


def _calculate_header(channel: str, key: str) -> Dict[str, Any]:
    """
    计算请求头

    Args:
        channel: 渠道类型
        key: API 密钥

    Returns:
        请求头字典
    """
    res_time = int(time.time() * 1000)
    req_seq = random.randint(10000, 99999)
    version = ""

    # 计算签名
    sign_str = f"{key}{res_time}{req_seq}{channel}{version}"
    sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest()

    return {
        "key": key,
        "resTime": res_time,
        "reqSeq": req_seq,
        "channel": channel,
        "sign": sign,
        "version": version,
    }


class WoClientAsync:
    """
    WoPan 网盘异步客户端

    提供网盘 API 的核心功能，包括文件上传、下载、管理等操作
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        ps_token: Optional[str] = None,
        user_agent: Optional[str] = None,
        debug: bool = False,
        proxy: Optional[str] = None,
        connector: Optional[aiohttp.BaseConnector] = None,
    ):
        """
        初始化客户端

        Args:
            access_token: 访问令牌
            refresh_token: 刷新令牌
            ps_token: 私有空间令牌
            user_agent: 用户代理
            debug: 是否启用调试模式
            proxy: 代理地址
            connector: aiohttp 连接器
        """
        self.access_token = access_token or ""
        self.refresh_token = refresh_token or ""
        self.ps_token = ps_token or ""
        self.ua = user_agent or DEFAULT_UA

        # 初始化加密工具
        self.crypto = Crypto()

        # 设置访问令牌
        if self.access_token:
            self.crypto.set_access_token(self.access_token)

        # 设置代理
        self.proxy = proxy

        # 初始化连接器
        self._connector = connector
        self._session: Optional[aiohttp.ClientSession] = None

        # 调试模式
        self.debug = debug

        # 回调函数
        self.on_refresh_token: Optional[Callable[[str, str], None]] = None

        # 缓存
        self._zone_url: Optional[str] = None
        self._zone_url_initialized = False
        self._dir_cache: Dict[str, str] = {}  # 路径到目录ID的缓存

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def _init_session(self) -> None:
        """初始化 HTTP 会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=300)
            connector = self._connector or aiohttp.TCPConnector(ssl=False)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
            )

    async def close(self) -> None:
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            # 等待连接器关闭
            if self._session.connector:
                await self._session.connector.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self._session is None or self._session.closed:
            await self._init_session()
        return self._session

    def set_access_token(self, token: str) -> None:
        """设置访问令牌"""
        self.access_token = token
        self.crypto.set_access_token(token)

    def set_refresh_token(self, token: str) -> None:
        """设置刷新令牌"""
        self.refresh_token = token

    def set_ps_token(self, token: str) -> None:
        """设置私有空间令牌"""
        self.ps_token = token

    def get_token(self) -> tuple[str, str]:
        """获取令牌"""
        return self.access_token, self.refresh_token

    def set_user_agent(self, user_agent: str) -> "WoClientAsync":
        """设置用户代理"""
        self.ua = user_agent
        return self

    def set_debug(self, debug: bool) -> "WoClientAsync":
        """设置调试模式"""
        self.debug = debug
        return self

    def set_proxy(self, proxy: str) -> "WoClientAsync":
        """设置代理"""
        self.proxy = proxy
        return self

    def on_refresh_token_callback(self, callback: Callable[[str, str], None]) -> None:
        """设置令牌刷新回调"""
        self.on_refresh_token = callback

    def _build_request_body(
        self, channel: str, param: Dict[str, Any], other: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        构建请求体

        Args:
            channel: 渠道类型
            param: 参数字典
            other: 其他参数

        Returns:
            加密后的请求体
        """
        body = param.copy()
        if other:
            body.update(other)

        # 加密参数
        body_str = json.dumps(body, separators=(",", ":"))
        encrypted = self.crypto.encrypt(body_str, channel)

        return encrypted

    async def _request(
        self,
        channel: str,
        key: str,
        param: Dict[str, Any],
        other: Optional[Dict[str, Any]] = None,
        resp_class: Optional[type] = None,
        retry: bool = True,
    ) -> Optional[Any]:
        """
        发送请求

        Args:
            channel: 渠道类型
            key: API 方法
            param: 参数
            other: 其他参数
            resp_class: 响应类
            retry: 是否重试

        Returns:
            响应数据

        Raises:
            WoPanException: 请求失败
        """
        url = f"{DEFAULT_BASE_URL}/{channel}/dispatcher"

        # 构建请求头
        headers = {
            "Origin": "https://pan.wo.cn",
            "Referer": "https://pan.wo.cn/",
            "Content-Type": "application/json",
            "User-Agent": self.ua,
        }

        if self.access_token:
            headers["Accesstoken"] = self.access_token

        # 计算签名头
        header = _calculate_header(channel, key)

        # 构建请求体
        body_data = self._build_request_body(channel, param, other)

        request_body = {"header": header, "body": body_data}

        if self.debug:
            print(f"[DEBUG] Request URL: {url}")
            print(f"[DEBUG] Request Headers: {headers}")
            print(f"[DEBUG] Request Body: {json.dumps(request_body, indent=2)}")

        session = await self._get_session()

        try:
            async with session.post(url, headers=headers, json=request_body, proxy=self.proxy) as response:
                response.raise_for_status()

                resp_data = await response.json()

                if self.debug:
                    print(f"[DEBUG] Response: {json.dumps(resp_data, indent=2)}")

                # 检查状态
                if resp_data.get("STATUS") != "200":
                    raise WoPanException(
                        f"Request failed: {resp_data.get('STATUS')} - {resp_data.get('MSG')}"
                    )

                rsp = resp_data.get("RSP", {})
                if rsp.get("RSP_CODE") != "0000":
                    # 如果是令牌过期且允许重试，则刷新令牌后重试
                    if (
                        retry
                        and channel != CHANNEL_API_USER
                        and rsp.get("RSP_CODE") == "9999"
                    ):
                        await self._refresh_token()
                        return await self._request(channel, key, param, other, resp_class, False)

                    raise WoPanException(
                        f"Request failed: {rsp.get('RSP_CODE')} - {rsp.get('RSP_DESC')}"
                    )

                # 解析响应数据
                data_str = rsp.get("DATA", "")
                if data_str and resp_class:
                    # 如果数据被加密，则解密
                    if data_str.startswith('"') and data_str.endswith('"'):
                        data_str = self.crypto.decrypt(data_str[1:-1], channel)

                    return json.loads(data_str)

                return None

        except aiohttp.ClientError as e:
            raise WoPanException(f"HTTP request failed: {str(e)}")

    async def _refresh_token(self) -> None:
        """刷新令牌"""
        # 这里应该实现实际的令牌刷新逻辑
        # 如果有设置回调函数，则调用
        if self.on_refresh_token:
            # 实际实现中应该调用刷新令牌 API
            pass

    async def request_api_user(
        self,
        key: str,
        param: Dict[str, Any],
        other: Optional[Dict[str, Any]] = None,
        resp_class: Optional[type] = None,
    ) -> Optional[Any]:
        """
        发送 api-user 请求

        Args:
            key: API 方法
            param: 参数
            other: 其他参数
            resp_class: 响应类

        Returns:
            响应数据
        """
        return await self._request(CHANNEL_API_USER, key, param, other, resp_class)

    async def request_wo_home(
        self,
        key: str,
        param: Dict[str, Any],
        other: Optional[Dict[str, Any]] = None,
        resp_class: Optional[type] = None,
    ) -> Optional[Any]:
        """
        发送 wohome 请求

        Args:
            key: API 方法
            param: 参数
            other: 其他参数
            resp_class: 响应类

        Returns:
            响应数据
        """
        return await self._request(CHANNEL_WO_HOME, key, param, other, resp_class)

    def get_file_type(self, filename: str) -> str:
        """
        获取文件类型

        Args:
            filename: 文件名

        Returns:
            文件类型
        """
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if not ext:
            return "5"

        # 文件类型映射（简化版）
        file_type_map = {
            # 视频
            "mp4": "1",
            "avi": "1",
            "mkv": "1",
            "mov": "1",
            "wmv": "1",
            # 图片
            "jpg": "2",
            "jpeg": "2",
            "png": "2",
            "gif": "2",
            "bmp": "2",
            # 音频
            "mp3": "3",
            "wav": "3",
            "flac": "3",
            "aac": "3",
            # 文档
            "pdf": "4",
            "doc": "4",
            "docx": "4",
            "xls": "4",
            "xlsx": "4",
            "ppt": "4",
            "pptx": "4",
            "txt": "4",
        }

        return file_type_map.get(ext, "5")

    @staticmethod
    def default_with_access_token(access_token: str) -> "WoClientAsync":
        """
        使用访问令牌创建默认客户端

        Args:
            access_token: 访问令牌

        Returns:
            WoClientAsync 实例
        """
        return WoClientAsync(access_token=access_token)

    @staticmethod
    def default_with_refresh_token(refresh_token: str) -> "WoClientAsync":
        """
        使用刷新令牌创建默认客户端

        Args:
            refresh_token: 刷新令牌

        Returns:
            WoClientAsync 实例
        """
        return WoClientAsync(refresh_token=refresh_token)

    @staticmethod
    def default() -> "WoClientAsync":
        """
        创建默认客户端

        Returns:
            WoClientAsync 实例
        """
        return WoClientAsync(user_agent=DEFAULT_UA)
