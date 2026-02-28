"""
WoPan SDK 异步文件系统 API 模块
提供文件和目录操作功能
"""

import json
from typing import Optional, List
from .client_async import (
    WoClientAsync,
    File,
    QueryAllFilesData,
    CreateDirectoryData,
    GetDownloadUrlData,
    GetDownloadUrlV2Data,
)
from .consts import *
from .exceptions import WoPanFileException


class FileSystemAsyncMixin:
    """异步文件系统操作混入类"""

    async def query_all_files(
        self: WoClientAsync,
        space_type: str,
        parent_directory_id: str,
        page_num: int = 1,
        page_size: int = 100,
        sort_rule: int = SORT_TIME_DESC,
        family_id: str = "",
    ) -> QueryAllFilesData:
        """
        查询所有文件

        Args:
            space_type: 空间类型
            parent_directory_id: 父目录 ID
            page_num: 页码
            page_size: 每页大小
            sort_rule: 排序规则
            family_id: 家庭 ID（家庭空间必需）

        Returns:
            查询结果

        Raises:
            WoPanFileException: 查询失败
        """
        param = {
            "spaceType": space_type,
            "parentDirectoryId": parent_directory_id,
            "pageNum": page_num,
            "pageSize": page_size,
            "sortRule": sort_rule,
            "clientId": DEFAULT_CLIENT_ID,
        }

        if space_type == SPACE_TYPE_FAMILY:
            if not family_id:
                raise WoPanFileException("family_id is required for family space")
            param["familyId"] = family_id

        if space_type == SPACE_TYPE_PRIVATE:
            if not self.ps_token:
                raise WoPanFileException("ps_token is required for private space")
            param["psToken"] = self.ps_token

        try:
            result = await self.request_wo_home(KEY_QUERY_ALL_FILES, param)
            if not result:
                return QueryAllFilesData(files=[])

            files = []
            for f in result.get("files", []):
                files.append(
                    File(
                        family_id=f.get("familyId"),
                        fid=f.get("fid"),
                        creator=f.get("creator"),
                        size=f.get("size", 0),
                        create_time=f.get("createTime"),
                        name=f.get("name"),
                        shooting_time=f.get("shootingTime"),
                        id=f.get("id"),
                        type=f.get("type"),
                        thumb_url=f.get("thumbUrl"),
                        file_type=f.get("fileType"),
                    )
                )

            return QueryAllFilesData(files=files)

        except Exception as e:
            raise WoPanFileException(f"Failed to query files: {str(e)}")

    async def query_all_files_personal(
        self: WoClientAsync,
        parent_directory_id: str,
        page_num: int = 1,
        page_size: int = 100,
        sort_rule: int = SORT_TIME_DESC,
    ) -> QueryAllFilesData:
        """
        查询个人空间的文件

        Args:
            parent_directory_id: 父目录 ID
            page_num: 页码
            page_size: 每页大小
            sort_rule: 排序规则

        Returns:
            查询结果
        """
        return await self.query_all_files(
            SPACE_TYPE_PERSONAL, parent_directory_id, page_num, page_size, sort_rule
        )

    async def query_all_files_family(
        self: WoClientAsync,
        parent_directory_id: str,
        family_id: str,
        page_num: int = 1,
        page_size: int = 100,
        sort_rule: int = SORT_TIME_DESC,
    ) -> QueryAllFilesData:
        """
        查询家庭空间的文件

        Args:
            parent_directory_id: 父目录 ID
            family_id: 家庭 ID
            page_num: 页码
            page_size: 每页大小
            sort_rule: 排序规则

        Returns:
            查询结果
        """
        return await self.query_all_files(
            SPACE_TYPE_FAMILY,
            parent_directory_id,
            page_num,
            page_size,
            sort_rule,
            family_id,
        )

    async def get_download_url_v2(
        self: WoClientAsync, fid_list: List[str]
    ) -> GetDownloadUrlV2Data:
        """
        获取文件下载链接 V2

        Args:
            fid_list: 文件 ID 列表

        Returns:
            下载链接数据

        Raises:
            WoPanFileException: 获取失败
        """
        param = {
            "type": "1",
            "fidList": fid_list,
            "clientId": DEFAULT_CLIENT_ID,
        }

        try:
            result = await self.request_wo_home(KEY_GET_DOWNLOAD_URL_V2, param)
            if not result:
                return GetDownloadUrlV2Data(type=1, list=[])

            download_list = []
            for item in result.get("list", []):
                download_list.append(
                    GetDownloadUrlData(
                        fid=item.get("fid"), download_url=item.get("downloadUrl")
                    )
                )

            return GetDownloadUrlV2Data(type=result.get("type", 1), list=download_list)

        except Exception as e:
            raise WoPanFileException(f"Failed to get download URL: {str(e)}")

    async def get_download_url(
        self: WoClientAsync, space_type: str, fid_list: List[str]
    ) -> List[GetDownloadUrlData]:
        """
        获取文件下载链接

        Args:
            space_type: 空间类型
            fid_list: 文件 ID 列表

        Returns:
            下载链接列表

        Raises:
            WoPanFileException: 获取失败
        """
        param = {
            "fidList": fid_list,
            "clientId": DEFAULT_CLIENT_ID,
            "spaceType": space_type,
        }

        try:
            result = await self.request_wo_home(KEY_GET_DOWNLOAD_URL, param)
            if not result:
                return []

            download_list = []
            for item in result:
                download_list.append(
                    GetDownloadUrlData(fid=item.get("fid"), download_url=item.get("downloadUrl"))
                )

            return download_list

        except Exception as e:
            raise WoPanFileException(f"Failed to get download URL: {str(e)}")

    async def create_directory(
        self: WoClientAsync,
        space_type: str,
        parent_directory_id: str,
        directory_name: str,
        family_id: str = "",
    ) -> CreateDirectoryData:
        """
        创建目录

        Args:
            space_type: 空间类型
            parent_directory_id: 父目录 ID
            directory_name: 目录名称
            family_id: 家庭 ID（家庭空间必需）

        Returns:
            创建的目录信息

        Raises:
            WoPanFileException: 创建失败
        """
        param = {
            "spaceType": space_type,
            "familyId": family_id,
            "parentDirectoryId": parent_directory_id,
            "directoryName": directory_name,
            "clientId": DEFAULT_CLIENT_ID,
        }

        if space_type == SPACE_TYPE_PRIVATE:
            if not self.ps_token:
                raise WoPanFileException("ps_token is required for private space")
            param["psToken"] = self.ps_token

        try:
            result = await self.request_wo_home(KEY_CREATE_DIRECTORY, param)
            if not result:
                raise WoPanFileException("Failed to create directory: No response")

            return CreateDirectoryData(id=result.get("id", ""))

        except Exception as e:
            raise WoPanFileException(f"Failed to create directory: {str(e)}")

    async def rename_file_or_directory(
        self: WoClientAsync,
        space_type: str,
        file_type: int,
        file_id: str,
        new_name: str,
        family_id: str = "",
    ) -> None:
        """
        重命名文件或目录

        Args:
            space_type: 空间类型
            file_type: 文件类型 (0=目录, 1=文件)
            file_id: 文件/目录 ID
            new_name: 新名称
            family_id: 家庭 ID（家庭空间必需）

        Raises:
            WoPanFileException: 重命名失败
        """
        # 如果是文件，获取文件类型
        file_type_str = "0"
        if file_type != 0:
            file_type_str = self.get_file_type(new_name)

        param = {
            "spaceType": space_type,
            "type": file_type,
            "fileType": file_type_str,
            "id": file_id,
            "name": new_name,
            "clientId": DEFAULT_CLIENT_ID,
        }

        if space_type == SPACE_TYPE_FAMILY:
            param["familyId"] = family_id

        if space_type == SPACE_TYPE_PRIVATE:
            if not self.ps_token:
                raise WoPanFileException("ps_token is required for private space")
            param["psToken"] = self.ps_token

        try:
            await self.request_wo_home(KEY_RENAME_FILE_OR_DIRECTORY, param, resp_class=None)

        except Exception as e:
            raise WoPanFileException(f"Failed to rename: {str(e)}")

    async def rename_file_or_directory_personal(
        self: WoClientAsync, file_type: int, file_id: str, new_name: str
    ) -> None:
        """
        重命名个人空间的文件或目录

        Args:
            file_type: 文件类型 (0=目录, 1=文件)
            file_id: 文件/目录 ID
            new_name: 新名称
        """
        await self.rename_file_or_directory(SPACE_TYPE_PERSONAL, file_type, file_id, new_name)

    async def rename_file_or_directory_family(
        self: WoClientAsync, file_type: int, file_id: str, new_name: str, family_id: str
    ) -> None:
        """
        重命名家庭空间的文件或目录

        Args:
            file_type: 文件类型 (0=目录, 1=文件)
            file_id: 文件/目录 ID
            new_name: 新名称
            family_id: 家庭 ID
        """
        await self.rename_file_or_directory(
            SPACE_TYPE_FAMILY, file_type, file_id, new_name, family_id
        )

    async def move_file(
        self: WoClientAsync,
        dir_list: List[str],
        file_list: List[str],
        target_dir_id: str,
        source_type: str,
        target_type: str,
        from_family_id: str = "",
        target_family_id: str = "",
    ) -> None:
        """
        移动文件或目录

        Args:
            dir_list: 目录 ID 列表
            file_list: 文件 ID 列表
            target_dir_id: 目标目录 ID
            source_type: 源空间类型
            target_type: 目标空间类型
            from_family_id: 源家庭 ID
            target_family_id: 目标家庭 ID

        Raises:
            WoPanFileException: 移动失败
        """
        param = {
            "targetDirId": target_dir_id,
            "sourceType": source_type,
            "targetType": target_type,
            "dirList": dir_list,
            "fileList": file_list,
            "secret": False,
            "clientId": DEFAULT_CLIENT_ID,
        }

        if source_type == SPACE_TYPE_FAMILY:
            param["fromFamilyId"] = from_family_id

        if target_type == SPACE_TYPE_FAMILY:
            param["familyId"] = target_family_id

        try:
            await self.request_wo_home(KEY_MOVE_FILE, param, resp_class=None)

        except Exception as e:
            raise WoPanFileException(f"Failed to move files: {str(e)}")

    async def copy_file(
        self: WoClientAsync,
        dir_list: List[str],
        file_list: List[str],
        target_dir_id: str,
        source_type: str,
        target_type: str,
        from_family_id: str = "",
        target_family_id: str = "",
    ) -> None:
        """
        复制文件或目录

        Args:
            dir_list: 目录 ID 列表
            file_list: 文件 ID 列表
            target_dir_id: 目标目录 ID
            source_type: 源空间类型
            target_type: 目标空间类型
            from_family_id: 源家庭 ID
            target_family_id: 目标家庭 ID

        Raises:
            WoPanFileException: 复制失败
        """
        param = {
            "targetDirId": target_dir_id,
            "sourceType": source_type,
            "targetType": target_type,
            "dirList": dir_list,
            "fileList": file_list,
            "secret": False,
            "clientId": DEFAULT_CLIENT_ID,
        }

        if source_type == SPACE_TYPE_FAMILY:
            param["fromFamilyId"] = from_family_id

        if target_type == SPACE_TYPE_FAMILY:
            param["familyId"] = target_family_id

        try:
            await self.request_wo_home(KEY_COPY_FILE, param, resp_class=None)

        except Exception as e:
            raise WoPanFileException(f"Failed to copy files: {str(e)}")

    async def delete_file(
        self: WoClientAsync, space_type: str, dir_list: List[str], file_list: List[str]
    ) -> None:
        """
        删除文件或目录

        Args:
            space_type: 空间类型
            dir_list: 目录 ID 列表
            file_list: 文件 ID 列表

        Raises:
            WoPanFileException: 删除失败
        """
        param = {
            "spaceType": space_type,
            "vipLevel": "0",
            "dirList": dir_list,
            "fileList": file_list,
            "clientId": DEFAULT_CLIENT_ID,
        }

        try:
            await self.request_wo_home(KEY_DELETE_FILE, param, resp_class=None)

        except Exception as e:
            raise WoPanFileException(f"Failed to delete files: {str(e)}")

    async def empty_recycle_data(self: WoClientAsync) -> None:
        """
        清空回收站

        Raises:
            WoPanFileException: 清空失败
        """
        param = {
            "clientId": DEFAULT_CLIENT_ID,
        }

        try:
            await self.request_wo_home(KEY_EMPTY_RECYCLE_DATA, param, resp_class=None)

        except Exception as e:
            raise WoPanFileException(f"Failed to empty recycle: {str(e)}")


# 将异步文件系统方法注入到 WoClientAsync 类
def _inject_filesystem_async_methods():
    """将异步文件系统方法注入到 WoClientAsync 类"""
    WoClientAsync.query_all_files = FileSystemAsyncMixin.query_all_files
    WoClientAsync.query_all_files_personal = FileSystemAsyncMixin.query_all_files_personal
    WoClientAsync.query_all_files_family = FileSystemAsyncMixin.query_all_files_family
    WoClientAsync.get_download_url_v2 = FileSystemAsyncMixin.get_download_url_v2
    WoClientAsync.get_download_url = FileSystemAsyncMixin.get_download_url
    WoClientAsync.create_directory = FileSystemAsyncMixin.create_directory
    WoClientAsync.rename_file_or_directory = FileSystemAsyncMixin.rename_file_or_directory
    WoClientAsync.rename_file_or_directory_personal = (
        FileSystemAsyncMixin.rename_file_or_directory_personal
    )
    WoClientAsync.rename_file_or_directory_family = (
        FileSystemAsyncMixin.rename_file_or_directory_family
    )
    WoClientAsync.move_file = FileSystemAsyncMixin.move_file
    WoClientAsync.copy_file = FileSystemAsyncMixin.copy_file
    WoClientAsync.delete_file = FileSystemAsyncMixin.delete_file
    WoClientAsync.empty_recycle_data = FileSystemAsyncMixin.empty_recycle_data
