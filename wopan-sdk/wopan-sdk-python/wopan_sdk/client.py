"""
WoPan SDK 客户端核心类
"""

import json
import hashlib
import time
import random
import threading
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
import requests
from .crypto import Crypto
from .consts import *
from .exceptions import WoPanException, WoPanAuthException, OpenListAuthException


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
    preview_url: str = ""
    file_unique_value: str = ""
    file_detail_link: str = ""
    is_collected: int = 0
    collect_time: str = ""


@dataclass
class SystemDir:
    """系统目录信息"""

    dir_name: str
    dir_type: str
    note: str
    lowest_app_version: str
    lowest_support_app_version: int
    icon: str
    create_time: str


@dataclass
class QueryAllFilesData:
    """查询所有文件结果"""

    files: list[File]
    systemDirs: list[SystemDir] = None

    def __post_init__(self):
        if self.systemDirs is None:
            self.systemDirs = []

        # 将 files 列表中的 dict 转换为 File 对象
        if self.files:
            converted_files = []
            for f in self.files:
                if isinstance(f, dict):
                    converted_files.append(File(
                        family_id=f.get("familyId"),
                        fid=f.get("fid", ""),
                        creator=f.get("creator", ""),
                        size=f.get("size", 0),
                        create_time=f.get("createTime", ""),
                        name=f.get("name", ""),
                        shooting_time=f.get("shootingTime", ""),
                        id=f.get("id", ""),
                        type=f.get("type", 0),
                        thumb_url=f.get("thumbUrl", ""),
                        file_type=f.get("fileType", ""),
                        preview_url=f.get("previewUrl", ""),
                        file_unique_value=f.get("fileUniqueValue", ""),
                        file_detail_link=f.get("fileDetailLink", ""),
                        is_collected=f.get("isCollected", 0),
                        collect_time=f.get("collectTime", ""),
                    ))
                else:
                    converted_files.append(f)
            self.files = converted_files

        # 将 systemDirs 列表中的 dict 转换为 SystemDir 对象
        if self.systemDirs:
            converted_dirs = []
            for sd in self.systemDirs:
                if isinstance(sd, dict):
                    converted_dirs.append(SystemDir(
                        dir_name=sd.get("dirName", ""),
                        dir_type=sd.get("dirType", ""),
                        note=sd.get("note", ""),
                        lowest_app_version=sd.get("lowestAppVersion", ""),
                        lowest_support_app_version=sd.get("lowestSupportAppVersion", 0),
                        icon=sd.get("icon", ""),
                        create_time=sd.get("createTime", ""),
                    ))
                else:
                    converted_dirs.append(sd)
            self.systemDirs = converted_dirs


@dataclass
class CreateDirectoryData:
    """创建目录结果"""

    id: str


@dataclass
class GetDownloadUrlData:
    """获取下载链接结果"""

    fid: str
    download_url: str = ""

    def __post_init__(self):
        # 处理从 JSON 传入的 dict 情况（驼峰命名转蛇形命名）
        if isinstance(self.fid, dict):
            data = self.fid
            self.fid = data.get("fid", "")
            self.download_url = data.get("downloadUrl", "")


@dataclass
class GetDownloadUrlV2Data:
    """获取下载链接 V2 结果"""

    type: int
    list: list[GetDownloadUrlData]

    def __post_init__(self):
        # 将 list 中的 dict 转换为 GetDownloadUrlData 对象
        if self.list:
            converted_list = []
            for item in self.list:
                if isinstance(item, dict):
                    converted_list.append(GetDownloadUrlData(
                        fid=item.get("fid", ""),
                        download_url=item.get("downloadUrl", "")
                    ))
                else:
                    converted_list.append(item)
            self.list = converted_list


@dataclass
class FamilyUserCurrentEncodeData:
    """家庭用户当前编码信息"""

    count: str
    defaultHomeId: int
    defaultHomeName: str
    groupHeadUrl: str
    groupName: str
    id: int
    memberRole: str
    ownerId: str
    unreadFlag: str


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


class WoClient:
    """
    WoPan 网盘客户端

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

        # 初始化 HTTP 会话
        self.session = requests.Session()
        self.session.verify = False

        # 设置代理
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

        # 调试模式
        self.debug = debug

        # 回调函数
        self.on_refresh_token: Optional[Callable[[str, str], None]] = None

        # 缓存
        self._zone_url: Optional[str] = None
        self._zone_url_initialized = False
        self._dir_cache: Dict[str, str] = {}  # 路径到目录ID的缓存

        # OpenList 配置（用于自动刷新 access_token）
        self._openlist_config: Optional["OpenlistConfig"] = None

        # 刷新锁（防止并发刷新）
        self._refreshing_lock = threading.Lock()

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

    def set_user_agent(self, user_agent: str) -> "WoClient":
        """设置用户代理"""
        self.ua = user_agent
        return self

    def set_debug(self, debug: bool) -> "WoClient":
        """设置调试模式"""
        self.debug = debug
        return self

    def set_proxy(self, proxy: str) -> "WoClient":
        """设置代理"""
        self.session.proxies = {"http": proxy, "https": proxy}
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
            构建后的请求体（包含加密的 param）
        """
        # 如果 param 为空，直接返回 other
        if not param:
            return other.copy() if other else {}

        # 只加密 param 部分（与 Go SDK 保持一致）
        param_str = json.dumps(param, separators=(",", ":"))
        encrypted_param = self.crypto.encrypt(param_str, channel)

        # 构建响应体：包含加密的 param 和 other 字段
        body = (other or {}).copy()
        body["param"] = encrypted_param

        return body

    def _request(
        self,
        channel: str,
        key: str,
        param: Dict[str, Any],
        other: Optional[Dict[str, Any]] = None,
        resp_class: Optional[type] = None,
        retry: bool = True,
        allowed_codes: Optional[list[str]] = None,
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
            allowed_codes: 允许的响应码列表（默认为 ["0000"]）
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

        try:
            response = self.session.post(url, headers=headers, json=request_body)
            response.raise_for_status()

            resp_data = response.json()

            if self.debug:
                print(f"[DEBUG] Response: {json.dumps(resp_data, indent=2)}")

            # 检查状态
            if resp_data.get("STATUS") != "200":
                raise WoPanException(
                    f"Request failed: {resp_data.get('STATUS')} - {resp_data.get('MSG')}"
                )

            rsp = resp_data.get("RSP", {})
            rsp_code = rsp.get("RSP_CODE", "")
            allowed = allowed_codes or ["0000"]

            if rsp_code not in allowed:
                # 如果是认证相关错误（令牌过期、无效登录信息等）且允许重试，则刷新令牌后重试
                # 只针对明确的认证错误码进行刷新，避免不必要的刷新
                if (
                    retry
                    and channel != CHANNEL_API_USER
                    and rsp_code in ("9999", "1001")  # 9999=令牌过期, 1001=无效登录信息
                ):
                    self._refresh_token()
                    return self._request(channel, key, param, other, resp_class, False, allowed_codes)

                raise WoPanException(
                    f"Request failed: {rsp_code} - {rsp.get('RSP_DESC')}"
                )

            # 解析响应数据
            data_str = rsp.get("DATA", "")
            if data_str and resp_class:
                # 对于 wohome/wocloud 渠道，DATA 总是加密的
                # 对于 api-user 渠道，检查是否有引号包裹
                if channel in (CHANNEL_WO_HOME, CHANNEL_WO_CLOUD):
                    # wohome/wocloud 渠道：直接解密
                    try:
                        data_str = self.crypto.decrypt(data_str, channel)
                    except Exception:
                        # 解密失败，尝试直接解析 JSON（兼容某些 API）
                        pass
                else:
                    # api-user 渠道：检查引号包裹（JSON 解析后引号已被去掉）
                    # 但原始格式是 "encrypted_data"，所以需要检查是否像加密数据
                    if data_str.startswith('"') and data_str.endswith('"'):
                        data_str = self.crypto.decrypt(data_str[1:-1], channel)

                # 解密后检查是否为空
                if data_str:
                    parsed_data = json.loads(data_str)
                    # 如果提供了响应类，将数据转换为数据类对象
                    if resp_class:
                        return resp_class(**parsed_data)
                    return parsed_data
                else:
                    return {} if not resp_class else None

            return None

        except requests.RequestException as e:
            raise WoPanException(f"HTTP request failed: {str(e)}")

    def _refresh_token(self) -> None:
        """
        刷新访问令牌

        如果客户端是通过 OpenList 初始化的，会自动从 OpenList 重新获取 access_token。
        否则，如果有设置回调函数，则调用回调函数由用户处理刷新逻辑。
        """
        # 使用锁防止并发刷新
        if not self._refreshing_lock.acquire(blocking=False):
            # 已有其他线程在刷新，直接返回
            return

        try:
            # 优先使用 OpenList 配置自动刷新
            if self._openlist_config:
                self._refresh_from_openlist()
            # 其次使用用户自定义的回调函数
            elif self.on_refresh_token:
                self.on_refresh_token(self.access_token, self.refresh_token)
        finally:
            self._refreshing_lock.release()

    def _refresh_from_openlist(self) -> None:
        """
        从 OpenList 管理后台重新获取 access_token

        Raises:
            OpenListAuthException: 获取令牌失败时抛出
        """
        config = self._openlist_config
        if not config:
            return

        # 设置默认值
        base_url = config.base_url or DEFAULT_OPENLIST_BASE_URL

        # 设置请求头
        headers = {
            "Authorization": config.admin_token,
            "User-Agent": DEFAULT_UA,
            "Accept": "application/json",
        }

        try:
            # 发送请求
            response = requests.get(
                f"{base_url}/api/admin/storage/get_access_token",
                params={"id": config.storage_id},
                headers=headers,
                timeout=config.timeout,
                verify=config.verify_ssl,
            )
            response.raise_for_status()

            # 解析响应
            resp_data = response.json()

            # 检查响应状态
            if resp_data.get("code") != 200:
                error_msg = resp_data.get("message", "Unknown error")
                raise OpenListAuthException(
                    f"OpenList API returned error: code={resp_data.get('code')}, message={error_msg}"
                )

            # 提取 access_token
            token_info = resp_data.get("data", {}).get("token_info", {})
            new_access_token = token_info.get("access_token")

            if not new_access_token:
                raise OpenListAuthException("OpenList API returned empty access_token")

            # 更新客户端的 access_token
            self.set_access_token(new_access_token)

            if self.debug:
                print(f"[DEBUG] Access token refreshed successfully from OpenList")

        except requests.RequestException as e:
            raise OpenListAuthException(f"Failed to refresh token from OpenList API: {str(e)}")
        except ValueError as e:  # JSON 解析错误
            raise OpenListAuthException(f"Failed to parse OpenList API response: {str(e)}")

    def request_api_user(
        self,
        key: str,
        param: Dict[str, Any],
        other: Optional[Dict[str, Any]] = None,
        resp_class: Optional[type] = None,
        allowed_codes: Optional[list[str]] = None,
    ) -> Optional[Any]:
        """
        发送 api-user 请求

        Args:
            key: API 方法
            param: 参数
            other: 其他参数
            resp_class: 响应类
            allowed_codes: 允许的响应码列表

        Returns:
            响应数据
        """
        return self._request(CHANNEL_API_USER, key, param, other, resp_class, True, allowed_codes)

    def request_wo_home(
        self,
        key: str,
        param: Dict[str, Any],
        other: Optional[Dict[str, Any]] = None,
        resp_class: Optional[type] = None,
        allowed_codes: Optional[list[str]] = None,
    ) -> Optional[Any]:
        """
        发送 wohome 请求

        Args:
            key: API 方法
            param: 参数
            other: 其他参数
            resp_class: 响应类
            allowed_codes: 允许的响应码列表

        Returns:
            响应数据
        """
        return self._request(CHANNEL_WO_HOME, key, param, other, resp_class, True, allowed_codes)

    def family_user_current_encode(self) -> Optional[FamilyUserCurrentEncodeData]:
        """
        获取家庭用户当前编码信息（用于获取默认家庭空间 ID）

        Returns:
            家庭用户编码信息，如果失败返回 None

        Raises:
            WoPanException: 请求失败
        """
        try:
            param = {"clientId": DEFAULT_CLIENT_ID}
            result = self.request_wo_home(
                KEY_FAMILY_USER_CURRENT_ENCODE,
                param,
                JSON_SECRET,
                FamilyUserCurrentEncodeData,
            )
            return result
        except Exception as e:
            raise WoPanException(f"Failed to get family user encode: {str(e)}")

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
    def default_with_access_token(access_token: str) -> "WoClient":
        """
        使用访问令牌创建默认客户端

        Args:
            access_token: 访问令牌

        Returns:
            WoClient 实例
        """
        return WoClient(access_token=access_token)

    @staticmethod
    def default_with_refresh_token(refresh_token: str) -> "WoClient":
        """
        使用刷新令牌创建默认客户端

        Args:
            refresh_token: 刷新令牌

        Returns:
            WoClient 实例
        """
        return WoClient(refresh_token=refresh_token)

    @staticmethod
    def default() -> "WoClient":
        """
        创建默认客户端

        Returns:
            WoClient 实例
        """
        return WoClient(user_agent=DEFAULT_UA)

    @staticmethod
    def default_with_openlist(config: "OpenlistConfig") -> "WoClient":
        """
        通过 OpenList 管理后台 API 获取 access_token 并初始化客户端

        Args:
            config: OpenlistConfig 配置对象

        Returns:
            初始化好的 WoClient 实例

        Raises:
            OpenListAuthException: 获取令牌失败时抛出

        Example:
            >>> config = OpenlistConfig(
            ...     admin_token="your-admin-token",
            ...     storage_id=1
            ... )
            >>> client = WoClient.default_with_openlist(config)
        """
        # 参数验证
        if not config.admin_token:
            raise OpenListAuthException("admin_token is required")
        if config.storage_id <= 0:
            raise OpenListAuthException("storage_id must be a positive integer")

        # 设置默认值
        base_url = config.base_url or DEFAULT_OPENLIST_BASE_URL
        timeout = config.timeout

        # 设置请求头
        headers = {
            "Authorization": config.admin_token,
            "User-Agent": DEFAULT_UA,
            "Accept": "application/json",
        }

        try:
            # 发送请求（使用 params 参数进行 URL 编码）
            response = requests.get(
                f"{base_url}/api/admin/storage/get_access_token",
                params={"id": config.storage_id},
                headers=headers,
                timeout=timeout,
                verify=config.verify_ssl,
            )
            response.raise_for_status()

            # 解析响应
            resp_data = response.json()

            # 检查响应状态
            if resp_data.get("code") != 200:
                error_msg = resp_data.get("message", "Unknown error")
                raise OpenListAuthException(
                    f"OpenList API returned error: code={resp_data.get('code')}, message={error_msg}"
                )

            # 提取 access_token
            token_info = resp_data.get("data", {}).get("token_info", {})
            access_token = token_info.get("access_token")

            if not access_token:
                raise OpenListAuthException("OpenList API returned empty access_token")

            # 创建并返回客户端
            client = WoClient(access_token=access_token)
            # 缓存 OpenList 配置，用于后续自动刷新
            client._openlist_config = config
            return client

        except requests.RequestException as e:
            raise OpenListAuthException(f"Failed to request OpenList API: {str(e)}")
        except ValueError as e:  # JSON 解析错误
            raise OpenListAuthException(f"Failed to parse OpenList API response: {str(e)}")

    @staticmethod
    def default_with_openlist_simple(admin_token: str, storage_id: int) -> "WoClient":
        """
        通过 OpenList 管理后台 API 获取 access_token 并初始化客户端（简化版本）

        Args:
            admin_token: OpenList 管理后台的认证令牌
            storage_id: 存储空间 ID

        Returns:
            初始化好的 WoClient 实例

        Raises:
            OpenListAuthException: 获取令牌失败时抛出

        Example:
            >>> client = WoClient.default_with_openlist_simple("admin-token", 1)
        """
        return WoClient.default_with_openlist(
            OpenlistConfig(admin_token=admin_token, storage_id=storage_id)
        )


@dataclass(frozen=True)
class OpenlistConfig:
    """OpenList 管理后台配置"""

    # AdminToken OpenList 管理后台的认证令牌（必填）
    admin_token: str

    # StorageID 存储空间 ID（必填）
    storage_id: int

    # BaseURL OpenList API 基础 URL（可选）
    # 默认使用 DEFAULT_OPENLIST_BASE_URL
    base_url: str = ""

    # Timeout HTTP 请求超时时间，单位秒（可选）
    # 默认使用 DEFAULT_OPENLIST_TIMEOUT
    timeout: int = DEFAULT_OPENLIST_TIMEOUT

    # VerifySSL 是否验证 SSL 证书（可选）
    # 默认为 False（与项目现有风格保持一致）
    # ⚠️ 仅用于测试环境，生产环境建议设置为 True
    verify_ssl: bool = False
