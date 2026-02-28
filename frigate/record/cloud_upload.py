"""
录像云存储上传管理器

实现异步上传、自动重试、断点续传和云端清理
"""

import datetime
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from queue import Queue, Empty
from pathlib import Path
from typing import Optional, Dict, Any, List

from frigate.const import RECORD_DIR
from frigate.models import Recordings

logger = logging.getLogger(__name__)

# 云上传状态常量
CLOUD_UPLOAD_PENDING = "pending"      # 等待上传
CLOUD_UPLOAD_UPLOADING = "uploading"  # 上传中
CLOUD_UPLOAD_SUCCESS = "success"      # 上传成功
CLOUD_UPLOAD_FAILED = "failed"        # 上传失败

# 云存储空间类型常量 (与 wopan_sdk 保持一致)
SPACE_TYPE_PERSONAL = "0"  # 个人空间


@dataclass
class CloudUploadConfig:
    """云存储配置"""
    enabled: bool = False
    openlist_base_url: str = "https://openlist.example.com"
    openlist_admin_token: str = ""
    openlist_storage_id: int = 1
    upload_dir_name: str = ""          # 云盘目标目录名称 (如 "backup_docker_app")
    retry_times: int = 3
    retry_interval: int = 60           # 重试间隔(秒)
    max_retry_count: int = 10          # 最大重试次数
    upload_timeout: int = 300          # 上传超时(秒)
    cloud_retain_days: int = 30        # 云端保留天数
    cleanup_interval: int = 60         # 清理检查间隔(分钟)


@dataclass
class UploadTask:
    """上传任务"""
    recording_id: str
    file_path: str
    cloud_path: str                    # 云端路径: /frigate/recordings/2024-01-15/14/front_door/30.45.mp4
    retry_count: int = 0
    last_error: str = ""
    created_at: float = field(default_factory=time.time)


class CloudUploadManager(threading.Thread):
    """
    云存储上传管理器

    职责:
    - 从队列中获取上传任务
    - 调用 wopan-sdk 执行上传
    - 管理上传状态和重试逻辑
    - 确保云盘目录结构与本地一致
    - 定期清理过期云端文件
    """

    def __init__(self, config: CloudUploadConfig, stop_event: threading.Event, camera_configs: dict = None):
        super().__init__(name="cloud_upload_manager", daemon=True)
        self.config = config
        self.stop_event = stop_event
        self.camera_configs = camera_configs or {}  # 摄像头配置，用于获取 friendly_name
        self.upload_queue: Queue[UploadTask] = Queue()
        self._client = None             # WoClient 实例 (延迟初始化)
        self._dir_cache: Dict[str, str] = {}  # 目录路径 -> 目录ID 缓存
        self._pending_tasks: Dict[str, UploadTask] = {}  # recording_id -> task
        self._last_cleanup_time: float = 0  # 上次清理时间
        self.uploadDirID: str = ""      # 根据upload_dir_name查找得到的目录ID

    def _init_client(self):
        """延迟初始化 wopan 客户端"""
        if self._client is not None:
            return True

        try:
            import sys
            # 添加 wopan-sdk 到路径 (子模块位于项目根目录下的 wopan-sdk/wopan-sdk-python)
            # 从 frigate/record/cloud_upload.py 向上两级到达项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            wopan_sdk_path = os.path.join(project_root, 'wopan-sdk', 'wopan-sdk-python')
            if os.path.exists(wopan_sdk_path):
                sys.path.insert(0, wopan_sdk_path)

            from wopan_sdk import WoClient, OpenlistConfig

            openlist_config = OpenlistConfig(
                admin_token=self.config.openlist_admin_token,
                storage_id=self.config.openlist_storage_id,
                base_url=self.config.openlist_base_url,
            )
            self._client = WoClient.default_with_openlist(openlist_config)

            # 根据 upload_dir_name 查找目录ID，如果不存在则创建
            if self.config.upload_dir_name:
                self.uploadDirID = self._find_directory_by_name_recursive(
                    self.config.upload_dir_name, "0"
                )
                if self.uploadDirID:
                    logger.info(f"Found upload directory by name: {self.config.upload_dir_name} -> {self.uploadDirID}")
                else:
                    # 目录不存在，创建目录
                    logger.info(f"Creating upload directory: {self.config.upload_dir_name}")
                    create_result = self._client.create_directory(
                        space_type=SPACE_TYPE_PERSONAL,
                        parent_directory_id="0",
                        directory_name=self.config.upload_dir_name,
                    )
                    if create_result and hasattr(create_result, 'id'):
                        self.uploadDirID = create_result.id
                        logger.info(f"Created upload directory: {self.config.upload_dir_name} -> {self.uploadDirID}")
                    else:
                        logger.warning(f"Failed to create directory: {self.config.upload_dir_name}")

            logger.info("Wopan client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize wopan client: {e}")
            return False

    def _find_directory_by_name_recursive(self, target_name: str, parent_dir_id: str) -> Optional[str]:
        """
        递归查找指定名称的目录

        Args:
            target_name: 目标目录名称 (如 "backup_docker_app")
            parent_dir_id: 起始父目录ID (通常为 "0" 表示根目录)

        Returns:
            找到的目录ID，未找到返回 None
        """
        if not self._client:
            return None

        try:
            # 查询当前目录下的所有文件和文件夹
            result = self._client.query_all_files_personal(
                parent_directory_id=parent_dir_id,
                page_num=1,
                page_size=100,
            )

            if not result or not hasattr(result, 'files'):
                return None

            # 先查找当前层级是否有匹配的目录
            for f in result.files:
                if f.name == target_name and f.type == 0:  # type=0 表示目录
                    return f.id

            # 如果当前层级没有找到，递归搜索子目录
            for f in result.files:
                if f.type == 0:  # 是目录
                    # 递归搜索子目录
                    found_id = self._find_directory_by_name_recursive(target_name, f.id)
                    if found_id:
                        return found_id

            return None

        except Exception as e:
            logger.error(f"Failed to find directory by name '{target_name}': {e}")
            return None

    def enqueue_upload(self, recording_id: str, file_path: str) -> None:
        """
        将录像加入上传队列

        Args:
            recording_id: 录像记录ID
            file_path: 本地文件路径 (如 /media/frigate/recordings/2024-01-15/14/front_door/30.45.mp4)
        """
        if not self.config.enabled:
            return

        # 计算云端路径 (移除本地前缀,保留相对路径)
        if file_path.startswith(RECORD_DIR):
            cloud_path = file_path[len(RECORD_DIR):]
        else:
            cloud_path = file_path

        # 确保以 / 开头
        if not cloud_path.startswith("/"):
            cloud_path = "/" + cloud_path

        # 将 UTC 时间路径转换为本地时区路径
        cloud_path = self._convert_utc_path_to_local(cloud_path)

        # 将摄像头内部名称替换为 friendly_name
        cloud_path = self._replace_camera_with_friendly_name(cloud_path)

        task = UploadTask(
            recording_id=recording_id,
            file_path=file_path,
            cloud_path=cloud_path,
        )

        self.upload_queue.put(task)
        self._pending_tasks[recording_id] = task

        # 更新数据库状态为 pending
        self._update_recording_status(recording_id, CLOUD_UPLOAD_PENDING)

        logger.debug(f"Enqueued cloud upload: {recording_id} -> {cloud_path}")

    def _convert_utc_path_to_local(self, cloud_path: str) -> str:
        """
        将 UTC 时间路径转换为本地时区路径
        例如: /2024-01-15/14/cam/30.45.mp4 -> /2024-01-15/22/cam/30.45.mp4 (UTC+8)
        """
        import re

        # 匹配日期/小时模式: /YYYY-MM-DD/HH/
        match = re.match(r'^/(\d{4}-\d{2}-\d{2})/(\d{2})(/.*)$', cloud_path)
        if match:
            date_str = match.group(1)
            hour_str = match.group(2)
            rest_path = match.group(3)

            try:
                # 解析 UTC 时间
                utc_time = datetime.datetime.strptime(f"{date_str} {hour_str}:00:00", "%Y-%m-%d %H:%M:%S")
                # 添加 UTC 时区
                utc_time = utc_time.replace(tzinfo=datetime.timezone.utc)
                # 转换为本地时区
                local_time = utc_time.astimezone()
                # 格式化回路径
                local_path = f"/{local_time.strftime('%Y-%m-%d/%H')}{rest_path}"
                logger.debug(f"Converted UTC path: {cloud_path} -> {local_path}")
                return local_path
            except Exception as e:
                logger.warning(f"Failed to convert UTC path to local: {e}")

        return cloud_path

    def _replace_camera_with_friendly_name(self, cloud_path: str) -> str:
        """
        将路径中的摄像头内部名称替换为 friendly_name
        例如: /2024-01-15/14/cam_a32cfd59/30.45.mp4 -> /2024-01-15/14/户外1/30.45.mp4

        Args:
            cloud_path: 云端路径

        Returns:
            替换后的路径，如果未找到 friendly_name 则返回原路径
        """
        import re

        # 匹配路径模式: /YYYY-MM-DD/HH/camera_name/filename.mp4
        match = re.match(r'^/(\d{4}-\d{2}-\d{2})/(\d{2})/([^/]+)(/.*)$', cloud_path)
        if match:
            date_str = match.group(1)
            hour_str = match.group(2)
            camera_name = match.group(3)
            rest_path = match.group(4)

            # 在 camera_configs 中查找对应的 friendly_name
            if camera_name in self.camera_configs:
                camera_config = self.camera_configs[camera_name]
                friendly_name = getattr(camera_config, "friendly_name", None)
                if friendly_name:
                    # 替换为 friendly_name
                    new_path = f"/{date_str}/{hour_str}/{friendly_name}{rest_path}"
                    logger.debug(f"Replaced camera name: {cloud_path} -> {new_path}")
                    return new_path

        return cloud_path

    def _update_recording_status(self, recording_id: str, status: str,
                                  cloud_fid: str = "", error: str = "") -> None:
        """更新录像的云上传状态"""
        try:
            update_data = {"cloud_upload_status": status}
            if cloud_fid:
                update_data["cloud_fid"] = cloud_fid
            if error:
                update_data["cloud_upload_error"] = error

            Recordings.update(**update_data).where(
                Recordings.id == recording_id
            ).execute()
        except Exception as e:
            logger.error(f"Failed to update recording status: {e}")

    def _get_or_create_root_dir(self) -> Optional[str]:
        """获取或创建云盘根目录 /frigate"""
        # 如果已经通过 upload_dir_name 找到了目录ID，直接使用
        if self.uploadDirID:
            return self.uploadDirID

        if not self._init_client():
            return None

        try:
            # 尝试查找 frigate 目录
            result = self._client.query_all_files_personal(
                parent_directory_id="0",  # 根目录
                page_num=1,
                page_size=100,
            )

            if result and hasattr(result, 'files'):
                for f in result.files:
                    if f.name == "frigate" and f.type == 0:  # type=0 表示目录
                        return f.id

            # 如果不存在则创建
            create_result = self._client.create_directory(
                space_type=SPACE_TYPE_PERSONAL,
                parent_directory_id="0",
                directory_name="frigate",
            )
            if create_result and hasattr(create_result, 'id'):
                logger.info("Created cloud root directory: /frigate")
                return create_result.id

            return None
        except Exception as e:
            logger.error(f"Failed to get/create root directory: {e}")
            return None

    def _ensure_cloud_directory(self, cloud_dir: str) -> Optional[str]:
        """
        确保云盘目录存在,返回目录ID

        Args:
            cloud_dir: 云端目录路径 (如 /recordings/2024-01-15/14/front_door)

        Returns:
            目录ID,失败返回None
        """
        root_dir_id = self._get_or_create_root_dir()
        if not root_dir_id:
            return None

        # 检查缓存
        if cloud_dir in self._dir_cache:
            return self._dir_cache[cloud_dir]

        if not self._init_client():
            return None

        try:
            # 解析路径,逐级创建目录
            parts = [p for p in cloud_dir.split("/") if p]
            current_dir_id = root_dir_id

            for part in parts:
                cache_key = "/".join(parts[:parts.index(part)+1])

                if cache_key in self._dir_cache:
                    current_dir_id = self._dir_cache[cache_key]
                    continue

                # 查找或创建子目录
                result = self._client.query_all_files_personal(
                    parent_directory_id=current_dir_id,
                    page_num=1,
                    page_size=100,
                )

                # 查找已存在的目录
                found = False
                if result and hasattr(result, 'files'):
                    for f in result.files:
                        if f.name == part and f.type == 0:  # type=0 表示目录
                            current_dir_id = f.id
                            found = True
                            break

                # 目录不存在,创建
                if not found:
                    create_result = self._client.create_directory(
                        space_type=SPACE_TYPE_PERSONAL,
                        parent_directory_id=current_dir_id,
                        directory_name=part,
                    )
                    if create_result and hasattr(create_result, 'id'):
                        current_dir_id = create_result.id
                        logger.debug(f"Created cloud directory: {part} -> {current_dir_id}")
                    else:
                        logger.error(f"Failed to create directory: {part}")
                        return None

                # 缓存结果
                self._dir_cache[cache_key] = current_dir_id

            return current_dir_id

        except Exception as e:
            logger.error(f"Failed to ensure cloud directory {cloud_dir}: {e}")
            return None

    def _upload_file(self, task: UploadTask) -> bool:
        """
        执行文件上传

        Returns:
            True 表示成功, False 表示失败
        """
        if not os.path.exists(task.file_path):
            logger.warning(f"File not found: {task.file_path}")
            self._update_recording_status(
                task.recording_id, CLOUD_UPLOAD_FAILED,
                error="File not found"
            )
            return False

        if not self._init_client():
            self._update_recording_status(
                task.recording_id, CLOUD_UPLOAD_FAILED,
                error="Failed to initialize wopan client"
            )
            return False

        # 确保目录存在
        cloud_dir = str(Path(task.cloud_path).parent)
        dir_id = self._ensure_cloud_directory(cloud_dir)

        if not dir_id:
            logger.error(f"Failed to get/create cloud directory: {cloud_dir}")
            self._update_recording_status(
                task.recording_id, CLOUD_UPLOAD_FAILED,
                error=f"Failed to create directory: {cloud_dir}"
            )
            return False

        try:
            from wopan_sdk import Upload2CFile, Upload2COption

            file_name = os.path.basename(task.file_path)
            file_size = os.path.getsize(task.file_path)

            with open(task.file_path, "rb") as f:
                upload_file = Upload2CFile(
                    name=file_name,
                    size=file_size,
                    content=f,
                    content_type="video/mp4",
                )

                options = Upload2COption(
                    retry_times=self.config.retry_times,
                    on_progress=lambda current, total: logger.debug(
                        f"Upload progress {task.recording_id}: {current}/{total}"
                    ),
                )

                self._update_recording_status(task.recording_id, CLOUD_UPLOAD_UPLOADING)

                fid = self._client.upload_2c_personal(
                    file=upload_file,
                    target_dir_id=dir_id,
                    opt=options,
                )

                self._update_recording_status(
                    task.recording_id, CLOUD_UPLOAD_SUCCESS, cloud_fid=fid
                )
                logger.info(f"Successfully uploaded: {task.file_path} -> fid={fid}")
                return True

        except Exception as e:
            logger.error(f"Upload failed for {task.file_path}: {e}")
            self._update_recording_status(
                task.recording_id, CLOUD_UPLOAD_FAILED, error=str(e)
            )
            return False

    def _cleanup_expired_cloud_files(self) -> None:
        """
        清理过期的云端文件

        根据 cloud_retain_days 配置删除超过保留期的云端文件
        """
        if self.config.cloud_retain_days <= 0:
            return

        if not self._init_client():
            return

        try:
            # 计算过期时间点
            expire_before = (
                datetime.datetime.now() - datetime.timedelta(days=self.config.cloud_retain_days)
            ).timestamp()

            # 查询需要清理的录像记录
            expired_recordings = Recordings.select().where(
                (Recordings.end_time < expire_before) &
                (Recordings.cloud_upload_status == CLOUD_UPLOAD_SUCCESS) &
                (Recordings.cloud_fid.is_null(False))
            )

            deleted_count = 0
            for rec in expired_recordings:
                try:
                    # 删除云端文件
                    if rec.cloud_fid:
                        self._client.delete_file(
                            space_type=SPACE_TYPE_PERSONAL,
                            dir_list=[],
                            file_list=[rec.cloud_fid],
                        )
                        deleted_count += 1

                        # 更新数据库状态
                        Recordings.update(
                            cloud_upload_status="deleted",
                            cloud_fid=None,
                        ).where(Recordings.id == rec.id).execute()

                        logger.debug(f"Deleted expired cloud file: {rec.cloud_fid}")

                except Exception as e:
                    logger.warning(f"Failed to delete cloud file {rec.cloud_fid}: {e}")

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired cloud files")

        except Exception as e:
            logger.error(f"Failed to cleanup expired cloud files: {e}")

    def run(self) -> None:
        """主循环: 处理上传队列和定期清理"""
        logger.info("Cloud upload manager started")

        while not self.stop_event.is_set():
            try:
                # 从队列获取任务 (超时5秒)
                task = self.upload_queue.get(timeout=5)
            except Empty:
                # 队列为空，检查是否需要清理
                self._check_cleanup()
                continue

            if task is None:
                continue

            # 检查重试次数
            if task.retry_count >= self.config.max_retry_count:
                logger.warning(f"Max retry reached for {task.recording_id}, giving up")
                self._pending_tasks.pop(task.recording_id, None)
                continue

            # 执行上传
            success = self._upload_file(task)

            if success:
                self._pending_tasks.pop(task.recording_id, None)
                # 上传成功后暂停 1 秒，避免频繁请求触发网盘限流
                time.sleep(1)
            else:
                # 上传失败,加入重试队列
                task.retry_count += 1
                task.last_error = "Upload failed"

                if task.retry_count < self.config.max_retry_count:
                    # 延迟重试
                    time.sleep(self.config.retry_interval)
                    self.upload_queue.put(task)
                else:
                    self._pending_tasks.pop(task.recording_id, None)

            # 检查是否需要清理
            self._check_cleanup()

        logger.info("Cloud upload manager stopped")

    def _check_cleanup(self) -> None:
        """检查是否需要执行清理"""
        now = time.time()
        cleanup_interval_seconds = self.config.cleanup_interval * 60

        if now - self._last_cleanup_time >= cleanup_interval_seconds:
            self._cleanup_expired_cloud_files()
            self._last_cleanup_time = now

    def load_pending_uploads(self) -> None:
        """
        启动时加载待上传的录像
        处理程序重启后的断点续传
        """
        if not self.config.enabled:
            return

        try:
            # 查询所有 pending 或 uploading 状态的录像
            pending_recordings = Recordings.select().where(
                (Recordings.cloud_upload_status == CLOUD_UPLOAD_PENDING) |
                (Recordings.cloud_upload_status == CLOUD_UPLOAD_UPLOADING)
            )

            for rec in pending_recordings:
                if os.path.exists(rec.path):
                    self.enqueue_upload(rec.id, rec.path)
                    logger.info(f"Resumed pending upload: {rec.id}")
        except Exception as e:
            logger.error(f"Failed to load pending uploads: {e}")
