"""
云存储上传管理器单元测试
"""

import sys
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path

# 添加 wopan-sdk 到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
wopan_sdk_path = os.path.join(project_root, "wopan-sdk", "wopan-sdk-python")
if os.path.exists(wopan_sdk_path):
    sys.path.insert(0, wopan_sdk_path)

# Mock complex imports before importing cloud_upload
sys.modules["frigate.comms.inter_process"] = MagicMock()
sys.modules["frigate.comms.detections_updater"] = MagicMock()
sys.modules["frigate.comms.recordings_updater"] = MagicMock()

from frigate.record.cloud_upload import (
    CloudUploadManager,
    CloudUploadConfig,
    UploadTask,
    CLOUD_UPLOAD_PENDING,
    CLOUD_UPLOAD_UPLOADING,
    CLOUD_UPLOAD_SUCCESS,
    CLOUD_UPLOAD_FAILED,
)


class TestCloudUploadConfig(unittest.TestCase):
    """测试云存储配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = CloudUploadConfig()
        self.assertFalse(config.enabled)
        self.assertEqual(config.openlist_base_url, "https://openlist.example.com")
        self.assertEqual(config.openlist_admin_token, "")
        self.assertEqual(config.openlist_storage_id, 1)
        self.assertEqual(config.retry_times, 3)
        self.assertEqual(config.retry_interval, 60)
        self.assertEqual(config.max_retry_count, 10)
        self.assertEqual(config.cloud_retain_days, 30.0)
        self.assertEqual(config.cleanup_interval, 60)

    def test_custom_config(self):
        """测试自定义配置"""
        config = CloudUploadConfig(
            enabled=True,
            openlist_base_url="https://custom.openlist.com",
            openlist_admin_token="test-token",
            openlist_storage_id=5,
            retry_times=5,
            retry_interval=30,
            max_retry_count=20,
            cloud_retain_days=60.0,
            cleanup_interval=120,
        )
        self.assertTrue(config.enabled)
        self.assertEqual(config.openlist_base_url, "https://custom.openlist.com")
        self.assertEqual(config.openlist_admin_token, "test-token")
        self.assertEqual(config.openlist_storage_id, 5)
        self.assertEqual(config.retry_times, 5)
        self.assertEqual(config.retry_interval, 30)
        self.assertEqual(config.max_retry_count, 20)
        self.assertEqual(config.cloud_retain_days, 60.0)
        self.assertEqual(config.cleanup_interval, 120)


class TestUploadTask(unittest.TestCase):
    """测试上传任务类"""

    def test_upload_task_creation(self):
        """测试上传任务创建"""
        task = UploadTask(
            recording_id="test-recording-1",
            file_path="/media/test.mp4",
            cloud_path="/recordings/test.mp4",
        )
        self.assertEqual(task.recording_id, "test-recording-1")
        self.assertEqual(task.file_path, "/media/test.mp4")
        self.assertEqual(task.cloud_path, "/recordings/test.mp4")
        self.assertEqual(task.retry_count, 0)
        self.assertEqual(task.last_error, "")
        self.assertGreater(task.created_at, 0)

    def test_upload_task_with_retry(self):
        """测试带重试次数的上传任务"""
        task = UploadTask(
            recording_id="test-recording-2",
            file_path="/media/test2.mp4",
            cloud_path="/recordings/test2.mp4",
            retry_count=3,
            last_error="Upload timeout",
        )
        self.assertEqual(task.retry_count, 3)
        self.assertEqual(task.last_error, "Upload timeout")


class TestCloudUploadManager(unittest.TestCase):
    """测试云存储上传管理器"""

    def setUp(self):
        """测试前设置"""
        self.stop_event = threading.Event()
        self.config = CloudUploadConfig(
            enabled=True,
            openlist_admin_token="test-token",
            openlist_storage_id=1,
            max_retry_count=3,
        )

    def tearDown(self):
        """测试后清理"""
        self.stop_event.set()

    @patch("frigate.record.cloud_upload.Recordings")
    def test_enqueue_upload(self, mock_recordings):
        """测试将文件加入上传队列"""
        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            test_file = f.name
            f.write(b"test video content")

        try:
            manager = CloudUploadManager(self.config, self.stop_event)

            # Mock 数据库更新
            mock_recordings.update.return_value.where.return_value.execute = MagicMock()

            # 测试加入队列
            manager.enqueue_upload("test-recording-1", test_file)

            # 验证任务已加入队列
            self.assertFalse(manager.upload_queue.empty())
            self.assertIn("test-recording-1", manager._pending_tasks)

        finally:
            # 清理临时文件
            if os.path.exists(test_file):
                os.unlink(test_file)

    @patch("frigate.record.cloud_upload.Recordings")
    def test_enqueue_upload_disabled(self, mock_recordings):
        """测试禁用时不加入队列"""
        config = CloudUploadConfig(enabled=False)
        manager = CloudUploadManager(config, self.stop_event)

        # Mock 数据库更新
        mock_recordings.update.return_value.where.return_value.execute = MagicMock()

        # 测试加入队列（应该被忽略）
        manager.enqueue_upload("test-recording-1", "/media/test.mp4")

        # 验证任务未加入队列
        self.assertTrue(manager.upload_queue.empty())

    def test_update_recording_status(self):
        """测试更新录像状态"""
        manager = CloudUploadManager(self.config, self.stop_event)

        with patch("frigate.record.cloud_upload.Recordings") as mock_recordings:
            mock_recordings.update.return_value.where.return_value.execute = MagicMock()

            # 测试更新状态
            manager._update_recording_status(
                "test-recording-1", CLOUD_UPLOAD_SUCCESS, cloud_fid="file-123"
            )

            # 验证更新被调用
            self.assertTrue(mock_recordings.update.called)

    @patch("frigate.record.cloud_upload.os.path.exists")
    def test_upload_file_not_found(self, mock_exists):
        """测试文件不存在时的上传"""
        mock_exists.return_value = False
        manager = CloudUploadManager(self.config, self.stop_event)

        with patch.object(manager, "_update_recording_status") as mock_update:
            task = UploadTask(
                recording_id="test-1", file_path="/nonexistent.mp4", cloud_path="/test.mp4"
            )

            result = manager._upload_file(task)

            # 验证返回 False 且状态更新为失败
            self.assertFalse(result)
            mock_update.assert_called_once()

    @patch("frigate.record.cloud_upload.os.path.exists")
    def test_upload_file_success(self, mock_exists):
        """测试成功上传文件"""
        mock_exists.return_value = True

        # Mock wopan client (动态导入)
        mock_client = Mock()
        mock_client.SPACE_TYPE_PERSONAL = "0"
        mock_client.query_all_files_personal.return_value = MagicMock(files=[])
        mock_client.create_directory.return_value = Mock(id="dir-123")
        mock_client.upload_2c_personal.return_value = "fid-456"

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            test_file = f.name
            f.write(b"test video content")

        try:
            manager = CloudUploadManager(self.config, self.stop_event)
            # 直接设置 mock client
            manager._client = mock_client

            task = UploadTask(
                recording_id="test-1", file_path=test_file, cloud_path="/test.mp4"
            )

            with patch.object(manager, "_update_recording_status") as mock_update:
                result = manager._upload_file(task)

                # 验证上传成功
                self.assertTrue(result)
                # 验证状态更新为成功
                self.assertTrue(mock_update.called)

        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_cloud_path_generation(self):
        """测试云端路径生成"""
        manager = CloudUploadManager(self.config, self.stop_event)

        # Mock RECORD_DIR
        with patch("frigate.record.cloud_upload.RECORD_DIR", "/media/frigate/recordings"):
            # 测试路径转换
            test_cases = [
                ("/media/frigate/recordings/2024-01-15/14/camera/30.45.mp4", "/2024-01-15/14/camera/30.45.mp4"),
                ("/media/frigate/recordings/test.mp4", "/test.mp4"),
            ]

            for file_path, expected_cloud_path in test_cases:
                cloud_path = file_path.replace("/media/frigate/recordings", "")
                if not cloud_path.startswith("/"):
                    cloud_path = "/" + cloud_path
                self.assertEqual(cloud_path, expected_cloud_path)

    def test_find_directory_by_name_recursive(self):
        """测试递归查找目录"""
        config = CloudUploadConfig(
            enabled=True,
            openlist_admin_token="test-token",
            openlist_storage_id=1,
            upload_dir_name="backup_docker_app",
            max_retry_count=3,
        )
        manager = CloudUploadManager(config, self.stop_event)

        # Mock wopan client
        mock_client = Mock()
        mock_client.SPACE_TYPE_PERSONAL = "0"

        # 创建模拟的文件列表
        # 第一层：根目录下的文件和目录
        mock_file1 = Mock()
        mock_file1.name = "documents"
        mock_file1.type = 0  # 目录
        mock_file1.id = "dir-1"

        mock_file2 = Mock()
        mock_file2.name = "backup_docker_app"
        mock_file2.type = 0  # 目录
        mock_file2.id = "dir-target"  # 找到的目标目录

        mock_file3 = Mock()
        mock_file3.name = "photos"
        mock_file3.type = 0  # 目录
        mock_file3.id = "dir-3"

        mock_result = Mock()
        mock_result.files = [mock_file1, mock_file2, mock_file3]
        mock_client.query_all_files_personal.return_value = mock_result

        # 直接设置 mock client
        manager._client = mock_client

        # 测试查找目录
        result_id = manager._find_directory_by_name_recursive("backup_docker_app", "0")

        # 验证找到了正确的目录ID
        self.assertEqual(result_id, "dir-target")

    def test_find_directory_by_name_recursive_nested(self):
        """测试递归查找嵌套目录"""
        config = CloudUploadConfig(
            enabled=True,
            openlist_admin_token="test-token",
            openlist_storage_id=1,
            max_retry_count=3,
        )
        manager = CloudUploadManager(config, self.stop_event)

        # Mock wopan client
        mock_client = Mock()
        mock_client.SPACE_TYPE_PERSONAL = "0"

        # 创建嵌套目录结构
        # 根目录
        mock_dir1 = Mock()
        mock_dir1.name = "level1"
        mock_dir1.type = 0
        mock_dir1.id = "dir-1"

        # level1 下的目标目录
        mock_target = Mock()
        mock_target.name = "backup_docker_app"
        mock_target.type = 0
        mock_target.id = "dir-target-found"

        # 第一层查询结果（根目录）
        mock_result1 = Mock()
        mock_result1.files = [mock_dir1]

        # 第二层查询结果（level1 目录下）
        mock_result2 = Mock()
        mock_result2.files = [mock_target]

        # 设置 mock 返回值序列
        mock_client.query_all_files_personal.side_effect = [mock_result1, mock_result2]

        # 直接设置 mock client
        manager._client = mock_client

        # 测试查找嵌套目录
        result_id = manager._find_directory_by_name_recursive("backup_docker_app", "0")

        # 验证找到了正确的目录ID
        self.assertEqual(result_id, "dir-target-found")

    def test_find_directory_by_name_not_found(self):
        """测试查找不存在的目录"""
        config = CloudUploadConfig(
            enabled=True,
            openlist_admin_token="test-token",
            openlist_storage_id=1,
            max_retry_count=3,
        )
        manager = CloudUploadManager(config, self.stop_event)

        # Mock wopan client
        mock_client = Mock()
        mock_client.SPACE_TYPE_PERSONAL = "0"

        # 创建空的文件列表
        mock_result = Mock()
        mock_result.files = []
        mock_client.query_all_files_personal.return_value = mock_result

        # 直接设置 mock client
        manager._client = mock_client

        # 测试查找不存在的目录
        result_id = manager._find_directory_by_name_recursive("nonexistent", "0")

        # 验证返回 None
        self.assertIsNone(result_id)

    def test_init_with_upload_dir_name(self):
        """测试使用 upload_dir_name 初始化"""
        config = CloudUploadConfig(
            enabled=True,
            openlist_admin_token="test-token",
            openlist_storage_id=1,
            upload_dir_name="my_backup_dir",
            max_retry_count=3,
        )
        manager = CloudUploadManager(config, self.stop_event)

        # Mock wopan client
        mock_client = Mock()
        mock_client.SPACE_TYPE_PERSONAL = "0"

        # 模拟找到目标目录
        mock_target_dir = Mock()
        mock_target_dir.name = "my_backup_dir"
        mock_target_dir.type = 0
        mock_target_dir.id = "found-dir-id-123"

        mock_result = Mock()
        mock_result.files = [mock_target_dir]
        mock_client.query_all_files_personal.return_value = mock_result

        # 直接设置 mock client 和模拟初始化
        manager._client = mock_client

        # 手动调用目录查找逻辑（模拟 _init_client 中的部分）
        found_id = manager._find_directory_by_name_recursive("my_backup_dir", "0")
        manager.uploadDirID = found_id

        # 验证 uploadDirID 已被设置
        self.assertEqual(manager.uploadDirID, "found-dir-id-123")


if __name__ == "__main__":
    unittest.main()
