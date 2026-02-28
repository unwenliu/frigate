"""
WoPan SDK 使用示例
演示如何使用 SDK 进行文件上传和管理
"""

import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wopan_sdk import WoClient, Upload2CFile, Upload2COption
from wopan_sdk.consts import SPACE_TYPE_PERSONAL, SORT_TIME_DESC


def example_upload_file():
    """示例：上传文件到个人空间"""
    print("=== 示例：上传文件 ===")

    # 初始化客户端（替换为你的 access_token）
    client = WoClient.default_with_access_token("your_access_token_here")

    # 启用调试模式
    client.set_debug(True)

    # 假设要上传的文件
    file_path = "test_video.mp4"

    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        print("提示：请准备一个测试文件或修改 file_path")
        return

    file_size = os.path.getsize(file_path)

    # 准备上传文件
    with open(file_path, "rb") as f:
        upload_file = Upload2CFile(
            name=os.path.basename(file_path),
            size=file_size,
            content=f,
            content_type="video/mp4",
        )

        # 配置上传选项
        options = Upload2COption(
            retry_times=3,
            on_progress=lambda current, total: print(
                f"上传进度: {current}/{total} ({current * 100 // total}%)"
            ),
            on_retry=lambda err, name, index, size: print(
                f"重试上传 {name} 第 {index} 部分"
            ),
        )

        try:
            # 上传到个人空间（替换为你的目录 ID）
            target_dir_id = "your_directory_id_here"
            fid = client.upload_2c_personal(
                file=upload_file,
                target_dir_id=target_dir_id,
                opt=options,
            )

            print(f"上传成功！文件 ID: {fid}")

        except Exception as e:
            print(f"上传失败: {str(e)}")


def example_query_files():
    """示例：查询文件列表"""
    print("\n=== 示例：查询文件 ===")

    # 初始化客户端
    client = WoClient.default_with_access_token("your_access_token_here")

    try:
        # 查询个人空间的文件
        result = client.query_all_files_personal(
            parent_directory_id="your_directory_id_here",
            page_num=1,
            page_size=100,
            sort_rule=SORT_TIME_DESC,
        )

        print(f"找到 {len(result.files)} 个文件：")
        for file in result.files:
            print(
                f"  - {file.name} ({file.size} bytes, Type: {file.file_type}, ID: {file.fid})"
            )

    except Exception as e:
        print(f"查询失败: {str(e)}")


def example_create_directory():
    """示例：创建目录"""
    print("\n=== 示例：创建目录 ===")

    # 初始化客户端
    client = WoClient.default_with_access_token("your_access_token_here")

    try:
        # 创建目录
        result = client.create_directory(
            space_type=SPACE_TYPE_PERSONAL,
            parent_directory_id="your_parent_directory_id",
            directory_name="测试文件夹",
        )

        print(f"目录创建成功！目录 ID: {result.id}")

    except Exception as e:
        print(f"创建目录失败: {str(e)}")


def example_get_download_url():
    """示例：获取下载链接"""
    print("\n=== 示例：获取下载链接 ===")

    # 初始化客户端
    client = WoClient.default_with_access_token("your_access_token_here")

    try:
        # 获取文件下载链接
        download_data = client.get_download_url_v2(["file_id_1", "file_id_2"])

        for item in download_data.list:
            print(f"文件 ID: {item.fid}")
            print(f"下载链接: {item.download_url}")
            print()

    except Exception as e:
        print(f"获取下载链接失败: {str(e)}")


def example_rename_file():
    """示例：重命名文件"""
    print("\n=== 示例：重命名文件 ===")

    # 初始化客户端
    client = WoClient.default_with_access_token("your_access_token_here")

    try:
        # 重命名文件
        client.rename_file_or_directory_personal(
            file_type=1,  # 0=目录, 1=文件
            file_id="your_file_id",
            new_name="new_file_name.mp4",
        )

        print("文件重命名成功！")

    except Exception as e:
        print(f"重命名失败: {str(e)}")


def example_delete_files():
    """示例：删除文件"""
    print("\n=== 示例：删除文件 ===")

    # 初始化客户端
    client = WoClient.default_with_access_token("your_access_token_here")

    try:
        # 删除文件
        client.delete_file(
            space_type=SPACE_TYPE_PERSONAL,
            dir_list=[],
            file_list=["file_id_1", "file_id_2"],
        )

        print("文件删除成功！")

    except Exception as e:
        print(f"删除失败: {str(e)}")


def example_with_custom_config():
    """示例：自定义配置"""
    print("\n=== 示例：自定义配置 ===")

    # 使用自定义配置创建客户端
    client = WoClient(
        access_token="your_access_token_here",
        refresh_token="your_refresh_token_here",
        user_agent="My Custom App/1.0",
        debug=True,
        proxy="http://proxy.example.com:8080",  # 可选代理
    )

    # 设置令牌刷新回调
    def on_token_refresh(access_token, refresh_token):
        print("令牌已刷新！")
        # 这里可以保存新的令牌

    client.on_refresh_token_callback(on_token_refresh)

    print("客户端配置完成")


def main():
    """主函数"""
    print("WoPan SDK Python 使用示例\n")

    print("请确保在运行示例前配置正确的 access_token 和目录 ID\n")

    # 运行示例
    # example_upload_file()
    # example_query_files()
    # example_create_directory()
    # example_get_download_url()
    # example_rename_file()
    # example_delete_files()
    # example_with_custom_config()

    print("\n提示：取消注释 main() 函数中的示例代码来运行")


if __name__ == "__main__":
    main()
