# wopan-sdk-python 模块文档

[根目录](../CLAUDE.md) > **wopan-sdk-python**

---

> 最后更新：2026-03-01 14:00:41
> 状态：已实现 OpenList 自动刷新功能

---

## 变更记录 (Changelog)

| 时间 | 变更内容 |
|------|----------|
| 2026-03-01 14:00:41 | 新增 OpenList 自动刷新 access_token 功能及完整测试覆盖（12 个测试用例） |
| 2026-02-26 14:11:25 | 更新文档：记录新增的调试脚本和测试文件 |
| 2026-02-25 21:31:54 | 新增 OpenList 管理后台认证支持文档，补充完整测试列表 |
| 2026-02-21 16:30:19 | 初始化模块文档，记录入口、接口、测试配置 |

---

## 模块职责

联通沃盘 Python SDK，提供完整的文件管理、上传下载和用户认证功能，支持同步和异步两种调用模式。

**核心功能：**
- 用户认证与令牌管理
- 文件查询、创建、重命名、移动、复制、删除
- 分片上传与断点续传
- AES 加密/解密
- 多空间类型支持（个人/家庭/私有）
- 同步/异步 API 双模式
- Mixin 模式注入扩展功能
- **OpenList 管理后台认证支持**（新增）
- **OpenList 自动刷新 access_token**（新增）

---

## 入口与启动

### 主入口文件
- **`wopan_sdk/__init__.py`** - 模块导出
- **`wopan_sdk/client.py`** - `WoClient` 核心客户端类
- **`wopan_sdk/client_async.py`** - `WoClientAsync` 异步客户端类

### 快速初始化

```python
from wopan_sdk import WoClient

# 使用访问令牌初始化
client = WoClient.default_with_access_token("your-access-token")

# 或使用刷新令牌初始化
client = WoClient.default_with_refresh_token("your-refresh-token")

# 启用调试模式
client.set_debug(True)

# 查询用户信息
user = client.request_api_user(
    key="AppQueryUser",
    param={"accessToken": client.access_token}
)
```

### 使用 OpenList 管理后台认证（推荐）

```python
from wopan_sdk import WoClient, OpenlistConfig

# 完整配置
client = WoClient.default_with_openlist(OpenlistConfig(
    admin_token="your-admin-token",
    storage_id=1,
    base_url="https://custom.openlist.com",
    timeout=30,
    verify_ssl=False
))

# SDK 会在令牌过期时自动调用 _refresh_token() 从 OpenList 获取新令牌
# 无需手动处理令牌刷新逻辑

# 简化版本
client = WoClient.default_with_openlist_simple("your-admin-token", 1)
```

### 异步客户端初始化

```python
import asyncio
from wopan_sdk import WoClientAsync

async def main():
    client = WoClientAsync(access_token="your-access-token")
    result = await client.query_all_files_personal(parent_directory_id="root")
    print(result)

asyncio.run(main())
```

---

## 对外接口

### 核心客户端方法 (client.py)

| 方法 | 说明 | 返回类型 |
|------|------|----------|
| `set_access_token(token)` | 设置访问令牌 | `WoClient` |
| `set_refresh_token(token)` | 设置刷新令牌 | `WoClient` |
| `set_ps_token(token)` | 设置私有空间令牌 | `WoClient` |
| `set_debug(debug)` | 启用/禁用调试模式 | `WoClient` |
| `set_proxy(proxy)` | 设置代理 | `WoClient` |
| `on_refresh_token_callback(callback)` | 设置令牌刷新回调 | `None` |
| `get_file_type(filename)` | 获取文件类型 | `str` |
| `get_token()` | 获取令牌元组 | `tuple[str, str]` |
| `set_user_agent(ua)` | 设置用户代理 | `WoClient` |
| `default_with_openlist(config)` | 使用 OpenList 认证初始化 | `WoClient` |
| `default_with_openlist_simple(admin_token, storage_id)` | OpenList 简化初始化 | `WoClient` |

### 文件系统 API (api_fs.py)

| 方法 | 说明 | 空间类型 |
|------|------|----------|
| `query_all_files_personal(parent_dir_id, page_num, page_size, sort_rule)` | 查询个人空间文件 | 个人 |
| `query_all_files_family(parent_dir_id, family_id, page_num, page_size, sort_rule)` | 查询家庭空间文件 | 家庭 |
| `get_download_url_v2(fid_list)` | 获取下载链接 V2 | 通用 |
| `get_download_url(space_type, fid_list)` | 获取下载链接 | 通用 |
| `create_directory(space_type, parent_dir_id, dir_name, family_id)` | 创建目录 | 全部 |
| `rename_file_or_directory_personal(file_type, file_id, new_name)` | 重命名（个人） | 个人 |
| `rename_file_or_directory_family(file_type, file_id, new_name, family_id)` | 重命名（家庭） | 家庭 |
| `move_file(dir_list, file_list, target_dir_id, source_type, target_type, ...)` | 移动文件 | 通用 |
| `copy_file(dir_list, file_list, target_dir_id, source_type, target_type, ...)` | 复制文件 | 通用 |
| `delete_file(space_type, dir_list, file_list)` | 删除文件 | 全部 |
| `empty_recycle_data()` | 清空回收站 | 通用 |

### 上传 API (upload.py)

| 方法 | 说明 |
|------|------|
| `upload_2c_personal(file, target_dir_id, opt)` | 上传到个人空间 |
| `upload_2c_family(file, target_dir_id, family_id, opt)` | 上传到家庭空间 |

### 异步 API (api_fs_async.py)

提供与同步 API 相同的方法，但返回 `Coroutine` 对象，需要使用 `await` 调用。

---

## 关键依赖与配置

### 依赖 (requirements.txt)

```
requests>=2.31.0
pycryptodome>=3.19.0
```

### 开发依赖 (setup.py)

```python
extras_require={
    "dev": [
        "pytest>=7.0.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
    ],
    "async": [
        "aiohttp>=3.9.0",
    ],
}
```

### 核心常量 (consts.py)

```python
# 默认配置
DEFAULT_CLIENT_ID = "1001000021"
DEFAULT_CLIENT_SECRET = "XFmi9GS2hzk98jGX"
DEFAULT_APP_ID = "10000001"
DEFAULT_BASE_URL = "https://panservice.mail.wo.cn"
DEFAULT_ZONE_URL = "https://tjupload.pan.wo.cn"
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
DEFAULT_PART_SIZE = 8 * 1024 * 1024  # 8MB 分片大小
DEFAULT_IV = "wNSOYIB1k1DjY5lA"      # AES 初始化向量
DEFAULT_OPENLIST_BASE_URL = "https://openlist.example.com"
DEFAULT_OPENLIST_TIMEOUT = 30       # OpenList 默认超时时间（秒）

# 空间类型
SPACE_TYPE_PERSONAL = "0"  # 个人空间
SPACE_TYPE_FAMILY = "1"    # 家庭空间
SPACE_TYPE_PRIVATE = "4"   # 私有空间

# 排序规则
SORT_NAME_ASC = 1   # 按名称升序
SORT_NAME_DESC = 2  # 按名称降序
SORT_SIZE_ASC = 3   # 按大小升序
SORT_SIZE_DESC = 4  # 按大小降序
SORT_TIME_ASC = 5   # 按时间升序
SORT_TIME_DESC = 6  # 按时间降序
```

### API 渠道 (channel)

| 渠道 | 用途 |
|------|------|
| `CHANNEL_API_USER` | 用户认证相关 |
| `CHANNEL_WO_HOME` | 文件系统操作 |
| `CHANNEL_WO_CLOUD` | 云存储上传 |

---

## 数据模型

### 客户端数据类 (client.py)

```python
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
```

### 上传数据类 (upload.py)

```python
@dataclass
class Upload2CFile:
    """上传文件信息"""
    name: str                        # 文件名
    size: int                        # 文件大小
    content: BinaryIO                # 文件内容（文件对象）
    content_type: str = "application/octet-stream"

@dataclass
class Upload2COption:
    """上传选项"""
    on_progress: Optional[Callable[[int, int], None]] = None  # 进度回调
    retry_times: int = 3                                     # 重试次数
    on_retry: Optional[Callable[[Exception, str, int, int], None]] = None  # 重试回调
```

### OpenList 配置 (client.py)

```python
@dataclass(frozen=True)
class OpenlistConfig:
    """OpenList 管理后台配置"""
    admin_token: str          # OpenList 管理后台的认证令牌（必填）
    storage_id: int           # 存储空间 ID（必填）
    base_url: str = ""        # OpenList API 基础 URL（可选）
    timeout: int = DEFAULT_OPENLIST_TIMEOUT  # HTTP 请求超时时间，单位秒（可选）
    verify_ssl: bool = False  # 是否验证 SSL 证书（可选）
```

---

## 测试与质量

### 测试文件

| 测试文件 | 覆盖内容 |
|----------|----------|
| `tests/test_basic.py` | 加密、客户端初始化、文件类型检测、上传对象创建 |
| `tests/test_openlist.py` | OpenList 管理后台认证测试 |
| `tests/test_auto_refresh.py` | **OpenList 自动刷新功能测试**（新增） |

### OpenList 自动刷新测试用例

`tests/test_auto_refresh.py` 包含两个测试类，共 12 个测试用例：

**TestOpenListAutoRefresh 类（基础功能测试）：**

1. **test_config_is_cached** - 验证 OpenList 配置被正确缓存
2. **test_refresh_from_openlist_success** - 测试从 OpenList 成功刷新令牌
3. **test_refresh_from_openlist_api_error** - 测试刷新令牌时 API 返回错误
4. **test_refresh_from_openlist_empty_token** - 测试刷新令牌时返回空令牌
5. **test_refresh_from_openlist_network_error** - 测试刷新令牌时网络请求失败
6. **test_refresh_token_uses_openlist** - 测试 RefreshToken 优先使用 OpenList
7. **test_refresh_token_fallback_to_callback** - 测试 RefreshToken 回退到回调函数
8. **test_concurrent_refresh_safety** - 测试并发刷新的线程安全性（10 个线程）
9. **test_multiple_refreshes** - 测试多次刷新令牌
10. **test_refresh_with_custom_base_url** - 测试使用自定义 BaseURL 刷新令牌
11. **test_refresh_with_custom_timeout** - 测试使用自定义超时刷新令牌
12. **test_refresh_with_debug_mode** - 测试调试模式下的刷新

**TestRefreshTokenIntegration 类（集成测试）：**

1. **test_full_refresh_cycle** - 测试完整的刷新周期

### 调试脚本（开发中）

| 脚本文件 | 用途 |
|----------|------|
| `debug_create_dir.py` | 调试目录创建功能 |
| `debug_http.py` | 调试 HTTP 请求 |
| `debug_query.py` | 调试文件查询功能 |
| `test_upload_to_existing_dir.py` | 测试上传到现有目录 |

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_auto_refresh.py::TestOpenListAutoRefresh -v

# 查看覆盖率
pytest --cov=wopan_sdk tests/

# 运行特定测试用例
pytest tests/test_auto_refresh.py::TestOpenListAutoRefresh::test_concurrent_refresh_safety -v
```

### 代码质量工具

```bash
# 代码格式化
black wopan_sdk/

# 代码检查
flake8 wopan_sdk/
```

---

## 加密机制

### 加密模块 (crypto.py)

```python
class Crypto:
    """加密工具类"""

    def __init__(self, client_secret=None, iv=None):
        self.key = (client_secret or DEFAULT_CLIENT_SECRET).encode("utf-8")
        self.iv = (iv or DEFAULT_IV).encode("utf-8")
        self.access_key = None  # 从 accessToken 前16位生成

    def encrypt(self, content: str, channel: str) -> str:
        """AES-CBC 加密后 Base64 编码"""

    def decrypt(self, content: str, channel: str) -> str:
        """Base64 解码后 AES-CBC 解密"""

    def set_access_token(self, token: str) -> None:
        """设置访问令牌（用于生成密钥）"""
```

### 加密流程

```python
# api-user 渠道：使用 clientSecret 作为密钥
# wohome/wocloud 渠道：使用 accessToken 前16位作为密钥

1. 根据渠道选择密钥
2. 使用 IV "wNSOYIB1k1DjY5lA"
3. AES-CBC 加密（PKCS7 填充）
4. Base64 编码输出
```

---

## OpenList 自动刷新机制

### 触发条件

当 API 返回错误码 `9999`（令牌过期）且 `retry=True` 时，SDK 会自动触发令牌刷新。

### 刷新策略

```python
def _refresh_token(self) -> None:
    """
    刷新访问令牌

    优先级：
    1. OpenList 配置自动刷新
    2. 用户自定义回调函数
    """
    # 1. 使用锁防止并发刷新
    if not self._refreshing_lock.acquire(blocking=False):
        return  # 已有其他线程在刷新

    try:
        # 2. 优先使用 OpenList 配置自动刷新
        if self._openlist_config:
            self._refresh_from_openlist()
        # 3. 其次使用用户自定义的回调函数
        elif self.on_refresh_token:
            self.on_refresh_token(self.access_token, self.refresh_token)
    finally:
        self._refreshing_lock.release()
```

### 线程安全

- 使用 `threading.Lock` 保护刷新逻辑
- 防止多个线程同时刷新令牌
- 使用非阻塞模式获取锁（`acquire(blocking=False)`）

### 配置缓存

- `OpenlistConfig` 在初始化时被保存到 `WoClient._openlist_config` 字段
- 后续刷新时直接使用缓存的配置，无需用户重新传入

### 自动重试

- 刷新成功后，原始请求会自动重试（`retry=False` 防止无限循环）
- 用户无感知，体验流畅

---

## 异常处理

### 异常类层次 (exceptions.py)

```python
WoPanException                    # 基础异常
├── WoPanAuthException           # 认证异常
├── OpenListAuthException        # OpenList 认证异常
├── WoPanUploadException         # 上传异常
├── WoPanFileException           # 文件操作异常
└── WoPanCryptoException         # 加密异常
```

### 异常示例

```python
from wopan_sdk import WoClient
from wopan_sdk.exceptions import WoPanException, WoPanFileException, OpenListAuthException

client = WoClient.default_with_access_token("token")

try:
    result = client.query_all_files_personal("parent-id")
except WoPanFileException as e:
    print(f"File operation failed: {e}")
except WoPanException as e:
    print(f"SDK error: {e}")

# OpenList 认证异常处理
try:
    client = WoClient.default_with_openlist(config)
except OpenListAuthException as e:
    print(f"OpenList authentication failed: {e}")
```

---

## 常见问题 (FAQ)

### Q1: 如何处理私有空间？

```python
client = WoClient()
client.set_ps_token("your-ps-token")
# 然后调用私有空间相关 API
result = client.query_all_files(
    space_type=SPACE_TYPE_PRIVATE,
    parent_directory_id="root"
)
```

### Q2: 如何实现上传进度回调？

```python
def progress_callback(current, total):
    percent = current * 100 // total
    print(f"Upload progress: {percent}%")

options = Upload2COption(
    on_progress=progress_callback,
    retry_times=5
)

with open("video.mp4", "rb") as f:
    upload_file = Upload2CFile(
        name="video.mp4",
        size=os.path.getsize("video.mp4"),
        content=f
    )
    fid = client.upload_2c_personal(upload_file, "target-dir-id", options)
```

### Q3: 如何使用异步 API？

```python
import asyncio
from wopan_sdk import WoClientAsync

async def upload_file_async():
    client = WoClientAsync(access_token="token")
    result = await client.query_all_files_personal("parent-id")
    return result

# 运行异步代码
result = asyncio.run(upload_file_async())
```

### Q4: 如何启用调试日志？

```python
client = WoClient.default_with_access_token("token")
client.set_debug(True)
# 请求和响应将打印到控制台
```

### Q5: 如何处理令牌自动刷新？

**使用 OpenList 自动刷新（推荐）：**

```python
from wopan_sdk import WoClient, OpenlistConfig

client = WoClient.default_with_openlist(OpenlistConfig(
    admin_token="your-admin-token",
    storage_id=1
))
# SDK 会自动处理刷新，无需手动干预
```

**使用自定义回调：**

```python
def on_token_refresh(access_token, refresh_token):
    print("Token refreshed!")
    # 保存新令牌到配置或数据库
    save_tokens(access_token, refresh_token)

client.on_refresh_token_callback(on_token_refresh)
```

### Q6: OpenList 自动刷新的优缺点是什么？

**优点：**
- 无需手动管理令牌生命周期
- 自动处理令牌过期场景
- 线程安全，支持并发请求
- 可配置超时和 SSL 验证
- 自动重试原始请求

**缺点：**
- 依赖 OpenList API 可用性
- 需要维护 admin_token 安全性
- 网络延迟可能导致请求重试

### Q7: 如何自定义 OpenList 请求超时？

```python
config = OpenlistConfig(
    admin_token="your-admin-token",
    storage_id=1,
    timeout=60,  # 60 秒超时
    base_url="https://custom.openlist.com"
)
client = WoClient.default_with_openlist(config)
```

### Q8: 如何禁用 SSL 验证？

```python
config = OpenlistConfig(
    admin_token="your-admin-token",
    storage_id=1,
    verify_ssl=False  # 禁用 SSL 验证（仅用于测试）
)
client = WoClient.default_with_openlist(config)
```

### Q7: 如何获取访问令牌？

```python
client = WoClient.default_with_access_token("token")
access_token, refresh_token = client.get_token()
print(f"Access Token: {access_token}")
print(f"Refresh Token: {refresh_token}")
```

---

## Mixin 模式说明

Python SDK 使用 Mixin 模式扩展功能：

```python
# api_fs.py 定义 FileSystemMixin
class FileSystemMixin:
    def query_all_files(self, ...): ...

# client_extended.py 在导入时注入方法
def _inject_filesystem_methods():
    WoClient.query_all_files = FileSystemMixin.query_all_files
    # ... 其他方法

# __init__.py 导入扩展模块
from . import client_extended
from . import client_extended_async
```

这种设计使得核心 `client.py` 保持简洁，同时支持模块化扩展。

---

## 相关文件清单

```
wopan-sdk-python/
├── wopan_sdk/
│   ├── __init__.py                    # 模块导出
│   ├── client.py                      # 核心同步客户端（含 OpenList 支持和自动刷新）
│   ├── client_async.py                # 核心异步客户端
│   ├── client_extended.py             # 同步客户端扩展注入
│   ├── client_extended_async.py       # 异步客户端扩展注入
│   ├── api_fs.py                      # 文件系统 API（同步）
│   ├── api_fs_async.py                # 文件系统 API（异步）
│   ├── upload.py                      # 上传功能（同步）
│   ├── upload_async.py                # 上传功能（异步）
│   ├── crypto.py                      # AES 加密工具
│   ├── consts.py                      # 常量定义
│   ├── exceptions.py                  # 异常类定义
│   └── __pycache__/                   # Python 缓存
├── tests/
│   ├── __init__.py
│   ├── test_basic.py                  # 基础功能测试
│   ├── test_openlist.py               # OpenList 认证测试
│   └── test_auto_refresh.py           # OpenList 自动刷新测试（新增）
├── examples/
│   ├── upload_example.py              # 上传示例
│   └── upload_async_example.py        # 异步上传示例
├── debug_create_dir.py                # 调试脚本：目录创建
├── debug_http.py                      # 调试脚本：HTTP 请求
├── debug_query.py                     # 调试脚本：文件查询
├── test_upload_to_existing_dir.py     # 测试脚本：上传到现有目录
├── setup.py                           # 包安装配置
├── requirements.txt                   # 依赖列表
├── README.md                          # 项目说明
├── QUICKSTART.md                      # 快速开始指南
├── LICENSE                            # MIT 许可证
├── CLAUDE.md                          # 模块 AI 文档
└── .gitignore                         # Git 忽略规则
```

---

*本文档由 AI 自动生成和维护。*
