# WoPan SDK for Python

网盘（WoPan）Python SDK，提供文件上传、下载、管理等功能。

## 功能特性

- ✅ 文件上传（支持分片上传、断点续传）
- ✅ 文件下载
- ✅ 文件管理（创建、重命名、移动、复制、删除）
- ✅ 目录管理
- ✅ 支持多种空间类型（个人空间、家庭空间）
- ✅ AES 加密/解密
- ✅ 进度回调
- ✅ 错误重试机制

## 安装

```bash
pip install wopan-sdk
```

或从源码安装：

```bash
git clone https://github.com/yourusername/wopan-sdk-python.git
cd wopan-sdk-python
pip install -e .
```

## 快速开始

### 初始化客户端

```python
from wopan_sdk import WoClient

# 使用访问令牌初始化
client = WoClient.default_with_access_token("your_access_token")

# 或使用刷新令牌初始化
client = WoClient.default_with_refresh_token("your_refresh_token")

# 启用调试模式
client.set_debug(True)
```

### 文件上传

```python
from wopan_sdk import WoClient, Upload2CFile, Upload2COption

# 创建客户端
client = WoClient.default_with_access_token("your_access_token")

# 准备文件
with open("video.mp4", "rb") as f:
    upload_file = Upload2CFile(
        name="video.mp4",
        size=os.path.getsize("video.mp4"),
        content=f,
        content_type="video/mp4"
    )

    # 上传选项
    options = Upload2COption(
        retry_times=3,
        on_progress=lambda current, total: print(f"Progress: {current}/{total} ({current*100//total}%)")
    )

    # 上传到个人空间
    fid = client.upload_2c_personal(
        file=upload_file,
        target_dir_id="your_directory_id",
        opt=options
    )

    print(f"Upload successful! File ID: {fid}")
```

### 上传到家庭空间

```python
# 上传到家庭空间
fid = client.upload_2c_family(
    file=upload_file,
    target_dir_id="your_directory_id",
    family_id="your_family_id",
    opt=options
)
```

### 查询文件

```python
# 查询个人空间文件
result = client.query_all_files_personal(
    parent_directory_id="your_directory_id",
    page_num=1,
    page_size=100,
    sort_rule=client.SORT_TIME_DESC
)

for file in result.files:
    print(f"File: {file.name}, Size: {file.size}, Type: {file.file_type}")
```

### 获取下载链接

```python
# 获取文件下载链接
download_data = client.get_download_url_v2(["file_id_1", "file_id_2"])

for item in download_data.list:
    print(f"File ID: {item.fid}, Download URL: {item.download_url}")
```

### 创建目录

```python
# 创建目录
result = client.create_directory(
    space_type=client.SPACE_TYPE_PERSONAL,
    parent_directory_id="parent_directory_id",
    directory_name="新建文件夹"
)

print(f"Directory created! ID: {result.id}")
```

### 重命名文件

```python
# 重命名文件
client.rename_file_or_directory_personal(
    file_type=1,  # 0=目录, 1=文件
    file_id="file_id",
    new_name="new_name.mp4"
)
```

### 移动文件

```python
# 移动文件
client.move_file(
    dir_list=[],
    file_list=["file_id_1", "file_id_2"],
    target_dir_id="target_directory_id",
    source_type=client.SPACE_TYPE_PERSONAL,
    target_type=client.SPACE_TYPE_PERSONAL
)
```

### 删除文件

```python
# 删除文件
client.delete_file(
    space_type=client.SPACE_TYPE_PERSONAL,
    dir_list=[],
    file_list=["file_id_1", "file_id_2"]
)
```

### 清空回收站

```python
# 清空回收站
client.empty_recycle_data()
```

## 高级用法

### 自定义配置

```python
from wopan_sdk import WoClient

client = WoClient(
    access_token="your_access_token",
    refresh_token="your_refresh_token",
    user_agent="Custom User Agent",
    debug=True,
    proxy="http://proxy.example.com:8080"
)
```

### 令牌刷新回调

```python
def on_token_refresh(access_token, refresh_token):
    print("Token refreshed!")
    # 保存新的令牌

client.on_refresh_token_callback(on_token_refresh)
```

### 分片上传配置

```python
from wopan_sdk import Upload2COption

options = Upload2COption(
    retry_times=5,  # 重试次数
    on_progress=lambda current, total: print(f"{current*100//total}%"),
    on_retry=lambda err, name, index, size: print(f"Retrying {name} part {index}")
)
```

## API 参考

### 客户端方法

| 方法 | 说明 |
|------|------|
| `upload_2c_personal()` | 上传到个人空间 |
| `upload_2c_family()` | 上传到家庭空间 |
| `query_all_files_personal()` | 查询个人空间文件 |
| `query_all_files_family()` | 查询家庭空间文件 |
| `get_download_url_v2()` | 获取下载链接 |
| `create_directory()` | 创建目录 |
| `rename_file_or_directory_personal()` | 重命名文件/目录 |
| `move_file()` | 移动文件 |
| `copy_file()` | 复制文件 |
| `delete_file()` | 删除文件 |
| `empty_recycle_data()` | 清空回收站 |

### 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `SPACE_TYPE_PERSONAL` | "0" | 个人空间 |
| `SPACE_TYPE_FAMILY` | "1" | 家庭空间 |
| `SPACE_TYPE_PRIVATE` | "4" | 私有空间 |
| `SORT_NAME_ASC` | 1 | 按名称升序 |
| `SORT_NAME_DESC` | 2 | 按名称降序 |
| `SORT_SIZE_ASC` | 3 | 按大小升序 |
| `SORT_SIZE_DESC` | 4 | 按大小降序 |
| `SORT_TIME_ASC` | 5 | 按时间升序 |
| `SORT_TIME_DESC` | 6 | 按时间降序 |

## 依赖

- Python >= 3.7
- requests >= 2.31.0
- pycryptodome >= 3.19.0

## 开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/wopan-sdk-python.git
cd wopan-sdk-python

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black wopan_sdk/

# 代码检查
flake8 wopan_sdk/
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 相关链接

- [WoPan 官网](https://pan.wo.cn)
- [Go 版本 SDK](https://github.com/yourusername/wopan-sdk-go)

## 更新日志

### 0.1.0 (2024-01-08)

- 初始版本发布
- 支持文件上传（分片上传、断点续传）
- 支持文件管理功能
- 支持 AES 加密/解密
- 支持个人空间和家庭空间
