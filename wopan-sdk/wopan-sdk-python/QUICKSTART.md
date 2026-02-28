# WoPan SDK Python 快速开始指南

## 安装

### 1. 安装依赖

```bash
# 进入项目目录
cd wopan-sdk-python

# 安装依赖
pip install -r requirements.txt
```

或使用 pip 直接安装：

```bash
pip install requests pycryptodome
```

### 2. 运行测试

```bash
# 运行基础测试
python -m unittest tests.test_basic -v
```

## 项目结构

```
wopan-sdk-python/
├── wopan_sdk/              # SDK 核心模块
│   ├── __init__.py        # 包初始化文件
│   ├── client.py          # 客户端核心类
│   ├── client_extended.py # 客户端扩展（注入上传和文件系统方法）
│   ├── consts.py          # 常量定义
│   ├── crypto.py          # AES 加密/解密
│   ├── upload.py          # 上传功能
│   ├── api_fs.py          # 文件系统 API
│   └── exceptions.py      # 异常类定义
├── examples/              # 示例代码
│   └── upload_example.py  # 上传示例
├── tests/                 # 测试代码
│   ├── __init__.py
│   └── test_basic.py      # 基础测试
├── requirements.txt       # 依赖列表
├── setup.py              # 安装配置
├── README.md             # 项目说明
└── .gitignore           # Git 忽略文件
```

## 快速使用

### 1. 导入 SDK

```python
from wopan_sdk import WoClient, Upload2CFile, Upload2COption
```

### 2. 创建客户端

```python
# 使用访问令牌创建客户端
client = WoClient.default_with_access_token("your_access_token")

# 启用调试模式
client.set_debug(True)
```

### 3. 上传文件

```python
# 准备文件
with open("video.mp4", "rb") as f:
    upload_file = Upload2CFile(
        name="video.mp4",
        size=os.path.getsize("video.mp4"),
        content=f
    )

    # 上传
    fid = client.upload_2c_personal(
        file=upload_file,
        target_dir_id="your_directory_id"
    )

    print(f"上传成功！文件 ID: {fid}")
```

### 4. 查询文件

```python
# 查询文件
result = client.query_all_files_personal(
    parent_directory_id="your_directory_id"
)

for file in result.files:
    print(f"{file.name} - {file.size} bytes")
```

## API 文档

详细的 API 文档请参考 [README.md](README.md)

## 功能列表

- ✅ AES 加密/解密
- ✅ 文件上传（支持分片上传）
- ✅ 文件查询
- ✅ 创建目录
- ✅ 重命名文件/目录
- ✅ 移动文件
- ✅ 复制文件
- ✅ 删除文件
- ✅ 获取下载链接
- ✅ 支持个人空间和家庭空间
- ✅ 进度回调
- ✅ 错误重试

## 注意事项

1. 使用前需要获取有效的 `access_token`
2. 上传大文件时建议配置 `Upload2COption` 以支持进度回调和重试
3. 默认分片大小为 8MB，可在 `consts.py` 中修改
4. 启用调试模式可以查看详细的请求和响应信息

## 下一步

- 查看 [examples/upload_example.py](examples/upload_example.py) 了解更多使用示例
- 阅读 [README.md](README.md) 查看完整的 API 文档

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
