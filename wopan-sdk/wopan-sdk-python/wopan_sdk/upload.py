"""
WoPan SDK 上传功能模块
实现文件上传相关功能
"""

import os
import time
import random
from typing import Optional, Callable, BinaryIO
from dataclasses import dataclass
from .client import WoClient
from .consts import *
from .exceptions import WoPanUploadException


@dataclass
class Upload2CFile:
    """上传文件信息"""

    name: str  # 文件名
    size: int  # 文件大小
    content: BinaryIO  # 文件内容（文件对象）
    content_type: str = "application/octet-stream"  # Content-Type


@dataclass
class Upload2COption:
    """上传选项"""

    on_progress: Optional[Callable[[int, int], None]] = None  # 进度回调
    retry_times: int = 3  # 重试次数
    on_retry: Optional[Callable[[Exception, str, int, int], None]] = (
        None  # 重试回调 (err, fileName, partIndex, finishedSize)
    )


class UploadMixin:
    """上传功能混入类"""

    def _init_zone_url(self) -> None:
        """初始化区域 URL"""
        if not self._zone_url_initialized:
            self._zone_url = DEFAULT_ZONE_URL
            self._zone_url_initialized = True

    def _random_chars(self, length: int) -> str:
        """
        生成随机字符串

        Args:
            length: 字符串长度

        Returns:
            随机字符串
        """
        charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return "".join(random.choice(charset) for _ in range(length))

    def upload_2c(
        self: WoClient,
        space_type: str,
        file: Upload2CFile,
        target_dir_id: str,
        family_id: str = "",
        opt: Optional[Upload2COption] = None,
    ) -> str:
        """
        上传文件到网盘

        Args:
            space_type: 空间类型 (0=个人, 1=家庭, 4=私有)
            file: 上传文件信息
            target_dir_id: 目标目录 ID
            family_id: 家庭 ID（家庭空间必需）
            opt: 上传选项

        Returns:
            文件 ID (fid)

        Raises:
            WoPanUploadException: 上传失败
        """
        opt = opt or Upload2COption()
        self._init_zone_url()

        zone_url = self._zone_url or DEFAULT_ZONE_URL
        batch_no = time.strftime("%Y%m%d%H%M%S")

        # 构建文件信息
        file_info = {
            "spaceType": space_type,
            "directoryId": target_dir_id,
            "batchNo": batch_no,
            "fileName": file.name,
            "fileSize": file.size,
            "fileType": self.get_file_type(file.name),
        }

        if space_type == SPACE_TYPE_FAMILY:
            if not family_id:
                raise WoPanUploadException("family_id is required for family space")
            file_info["familyId"] = family_id

        if space_type == SPACE_TYPE_PRIVATE:
            if not self.ps_token:
                raise WoPanUploadException("ps_token is required for private space")
            file_info["psToken"] = self.ps_token

        # 加密文件信息
        file_info_str = self.crypto.wo_home_encrypt(json.dumps(file_info))

        # 上传 URL
        upload_url = f"{zone_url}/openapi/client/{KEY_UPLOAD_2C}"

        # 计算分片数
        total_part = file.size // DEFAULT_PART_SIZE
        if total_part == 0:
            total_part = 1

        # 构建 form data
        unique_id = f"{int(time.time() * 1000)}_{self._random_chars(6)}"

        form_data = {
            "uniqueId": unique_id,
            "accessToken": self.access_token,
            "fileName": file.name,
            "psToken": "undefined",
            "fileSize": str(file.size),
            "totalPart": str(total_part),
            "channel": CHANNEL_WO_CLOUD,
            "directoryId": target_dir_id,
            "fileInfo": file_info_str,
        }

        fid = ""
        finished_size = 0

        # 分片上传
        for part_index in range(1, total_part + 1):
            part_size = DEFAULT_PART_SIZE
            if part_index == total_part:
                part_size = file.size - finished_size

            form_data["partSize"] = str(part_size)
            form_data["partIndex"] = str(part_index)

            # 上传分片
            try:
                resp = self._upload_part(
                    upload_url, file, form_data, part_index, part_size
                )
                if resp.get("data", {}).get("fid"):
                    fid = resp["data"]["fid"]
            except Exception as e:
                # 重试
                for retry in range(opt.retry_times):
                    if opt.on_retry:
                        opt.on_retry(e, file.name, part_index, finished_size)

                    # 重置文件指针
                    file.content.seek(finished_size)
                    try:
                        resp = self._upload_part(
                            upload_url, file, form_data, part_index, part_size
                        )
                        if resp.get("data", {}).get("fid"):
                            fid = resp["data"]["fid"]
                        break
                    except Exception:
                        if retry == opt.retry_times - 1:
                            raise WoPanUploadException(
                                f"Failed to upload part {part_index} after {opt.retry_times} retries: {str(e)}"
                            )

            finished_size += part_size

            # 进度回调
            if opt.on_progress:
                opt.on_progress(finished_size, file.size)

        return fid

    def _upload_part(
        self: WoClient,
        upload_url: str,
        file: Upload2CFile,
        form_data: dict,
        part_index: int,
        part_size: int,
    ) -> dict:
        """
        上传单个分片

        Args:
            upload_url: 上传 URL
            file: 上传文件信息
            form_data: form data
            part_index: 分片索引
            part_size: 分片大小

        Returns:
            响应数据

        Raises:
            WoPanUploadException: 上传失败
        """
        headers = {
            "Origin": "https://pan.wo.cn",
            "Referer": "https://pan.wo.cn/",
            "User-Agent": self.ua,
        }

        # 读取分片数据
        part_data = file.content.read(part_size)

        # 构建 multipart form data
        files = {
            "file": (file.name, part_data, file.content_type),
        }

        if self.debug:
            print(f"[DEBUG] Uploading part {part_index}/{form_data['totalPart']}")

        try:
            response = self.session.post(
                upload_url, data=form_data, files=files, headers=headers
            )
            response.raise_for_status()

            resp_data = response.json()

            if self.debug:
                print(f"[DEBUG] Part {part_index} response: {resp_data}")

            if resp_data.get("code") != "0000":
                raise WoPanUploadException(
                    f"Part {part_index} upload failed: {resp_data.get('msg', 'Unknown error')}"
                )

            return resp_data

        except Exception as e:
            raise WoPanUploadException(f"Failed to upload part {part_index}: {str(e)}")

    def upload_2c_personal(
        self: WoClient,
        file: Upload2CFile,
        target_dir_id: str,
        opt: Optional[Upload2COption] = None,
    ) -> str:
        """
        上传文件到个人空间

        Args:
            file: 上传文件信息
            target_dir_id: 目标目录 ID
            opt: 上传选项

        Returns:
            文件 ID (fid)
        """
        return self.upload_2c(SPACE_TYPE_PERSONAL, file, target_dir_id, "", opt)

    def upload_2c_family(
        self: WoClient,
        file: Upload2CFile,
        target_dir_id: str,
        family_id: str,
        opt: Optional[Upload2COption] = None,
    ) -> str:
        """
        上传文件到家庭空间

        Args:
            file: 上传文件信息
            target_dir_id: 目标目录 ID
            family_id: 家庭 ID
            opt: 上传选项

        Returns:
            文件 ID (fid)
        """
        return self.upload_2c(SPACE_TYPE_FAMILY, file, target_dir_id, family_id, opt)


# 将上传方法注入到 WoClient 类
def _inject_upload_methods():
    """将上传方法注入到 WoClient 类"""
    WoClient._init_zone_url = lambda self: UploadMixin._init_zone_url(self)
    WoClient._random_chars = UploadMixin._random_chars
    WoClient.upload_2c = UploadMixin.upload_2c
    WoClient._upload_part = UploadMixin._upload_part
    WoClient.upload_2c_personal = UploadMixin.upload_2c_personal
    WoClient.upload_2c_family = UploadMixin.upload_2c_family


# 导入 json
import json
