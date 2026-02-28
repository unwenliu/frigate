"""
WoPan SDK 异步使用示例
"""

import asyncio
from wopan_sdk import WoClientAsync, Upload2CFile, Upload2COption


async def main():
    """异步主函数示例"""

    # 使用上下文管理器自动管理会话
    async with WoClientAsync(access_token="your_access_token") as client:
        # 1. 查询个人空间文件
        print("查询个人空间文件...")
        result = await client.query_all_files_personal(
            parent_directory_id="0",  # 根目录ID
            page_num=1,
            page_size=10
        )
        print(f"找到 {len(result.files)} 个文件")
        for file in result.files:
            print(f"  - {file.name} ({file.size} bytes)")

        # 2. 创建目录
        print("\n创建目录...")
        dir_result = await client.create_directory(
            space_type="0",  # 个人空间
            parent_directory_id="0",
            directory_name="测试目录"
        )
        print(f"创建目录成功，ID: {dir_result.id}")

        # 3. 上传文件
        print("\n上传文件...")
        with open("test_file.txt", "rb") as f:
            upload_file = Upload2CFile(
                name="test_file.txt",
                size=1024,  # 文件大小
                content=f
            )

            # 设置上传选项
            upload_option = Upload2COption(
                on_progress=lambda current, total: print(f"上传进度: {current}/{total}"),
                retry_times=3
            )

            fid = await client.upload_2c_personal(
                file=upload_file,
                target_dir_id=dir_result.id,
                opt=upload_option
            )
            print(f"上传成功，文件ID: {fid}")

        # 4. 获取下载链接
        print("\n获取下载链接...")
        download_data = await client.get_download_url_v2([fid])
        for item in download_data.list:
            print(f"  下载链接: {item.download_url}")

        # 5. 批量操作示例
        print("\n批量操作示例...")
        # 可以使用 asyncio.gather 并发执行多个操作
        results = await asyncio.gather(
            client.query_all_files_personal("0", 1, 10),
            client.query_all_files_personal("0", 2, 10),
            client.query_all_files_personal("0", 3, 10),
        )
        print(f"并发查询完成，共获取 {sum(len(r.files) for r in results)} 个文件")


async def upload_with_progress():
    """带进度显示的上传示例"""
    async with WoClientAsync(access_token="your_access_token") as client:

        def progress_callback(current, total):
            percent = (current / total) * 100
            print(f"\r上传进度: {percent:.2f}%", end="")

        with open("large_file.zip", "rb") as f:
            upload_file = Upload2CFile(
                name="large_file.zip",
                size=1024 * 1024 * 100,  # 100MB
                content=f
            )

            upload_option = Upload2COption(
                on_progress=progress_callback,
                retry_times=5
            )

            fid = await client.upload_2c_personal(
                file=upload_file,
                target_dir_id="0",
                opt=upload_option
            )
            print(f"\n上传完成，文件ID: {fid}")


async def manual_session_management():
    """手动管理会话的示例"""
    client = WoClientAsync(access_token="your_access_token")

    try:
        # 手动初始化会话（如果需要）
        # session 会在首次请求时自动创建

        # 执行操作
        result = await client.query_all_files_personal("0", 1, 10)
        print(f"找到 {len(result.files)} 个文件")

    finally:
        # 记得关闭会话
        await client.close()


if __name__ == "__main__":
    # 运行主示例
    asyncio.run(main())

    # 运行其他示例
    # asyncio.run(upload_with_progress())
    # asyncio.run(manual_session_management())
