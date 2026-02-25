from enum import Enum
from typing import Optional

from pydantic import Field

from frigate.const import MAX_PRE_CAPTURE
from frigate.review.types import SeverityEnum

from ..base import FrigateBaseModel

__all__ = [
    "RecordConfig",
    "RecordExportConfig",
    "RecordPreviewConfig",
    "RecordQualityEnum",
    "EventsConfig",
    "ReviewRetainConfig",
    "RecordRetainConfig",
    "RetainModeEnum",
    "CloudUploadConfig",
]

DEFAULT_TIME_LAPSE_FFMPEG_ARGS = "-vf setpts=0.04*PTS -r 30"


class RecordRetainConfig(FrigateBaseModel):
    days: float = Field(default=0, ge=0, title="Default retention period.")


class RetainModeEnum(str, Enum):
    all = "all"
    motion = "motion"
    active_objects = "active_objects"


class ReviewRetainConfig(FrigateBaseModel):
    days: float = Field(default=10, ge=0, title="Default retention period.")
    mode: RetainModeEnum = Field(default=RetainModeEnum.motion, title="Retain mode.")


class EventsConfig(FrigateBaseModel):
    pre_capture: int = Field(
        default=5,
        title="Seconds to retain before event starts.",
        le=MAX_PRE_CAPTURE,
        ge=0,
    )
    post_capture: int = Field(
        default=5, ge=0, title="Seconds to retain after event ends."
    )
    retain: ReviewRetainConfig = Field(
        default_factory=ReviewRetainConfig, title="Event retention settings."
    )


class RecordQualityEnum(str, Enum):
    very_low = "very_low"
    low = "low"
    medium = "medium"
    high = "high"
    very_high = "very_high"


class RecordPreviewConfig(FrigateBaseModel):
    quality: RecordQualityEnum = Field(
        default=RecordQualityEnum.medium, title="Quality of recording preview."
    )


class RecordExportConfig(FrigateBaseModel):
    timelapse_args: str = Field(
        default=DEFAULT_TIME_LAPSE_FFMPEG_ARGS, title="Timelapse Args"
    )


class RecordConfig(FrigateBaseModel):
    enabled: bool = Field(default=False, title="Enable record on all cameras.")
    sync_recordings: bool = Field(
        default=False, title="Sync recordings with disk on startup and once a day."
    )
    expire_interval: int = Field(
        default=60,
        title="Number of minutes to wait between cleanup runs.",
    )
    continuous: RecordRetainConfig = Field(
        default_factory=RecordRetainConfig,
        title="Continuous recording retention settings.",
    )
    motion: RecordRetainConfig = Field(
        default_factory=RecordRetainConfig, title="Motion recording retention settings."
    )
    detections: EventsConfig = Field(
        default_factory=EventsConfig, title="Detection specific retention settings."
    )
    alerts: EventsConfig = Field(
        default_factory=EventsConfig, title="Alert specific retention settings."
    )
    export: RecordExportConfig = Field(
        default_factory=RecordExportConfig, title="Recording Export Config"
    )
    preview: RecordPreviewConfig = Field(
        default_factory=RecordPreviewConfig, title="Recording Preview Config"
    )
    enabled_in_config: Optional[bool] = Field(
        default=None, title="Keep track of original state of recording."
    )
    cloud_upload: "CloudUploadConfig" = Field(
        default_factory=lambda: CloudUploadConfig(),
        title="Cloud storage upload configuration.",
    )

    @property
    def event_pre_capture(self) -> int:
        return max(
            self.alerts.pre_capture,
            self.detections.pre_capture,
        )

    def get_review_pre_capture(self, severity: SeverityEnum) -> int:
        if severity == SeverityEnum.alert:
            return self.alerts.pre_capture
        else:
            return self.detections.pre_capture

    def get_review_post_capture(self, severity: SeverityEnum) -> int:
        if severity == SeverityEnum.alert:
            return self.alerts.post_capture
        else:
            return self.detections.post_capture


class CloudUploadConfig(FrigateBaseModel):
    """云存储上传配置"""

    enabled: bool = Field(default=False, title="启用云存储上传")
    openlist_base_url: str = Field(
        default="https://openlist.example.com",
        title="OpenList API 地址"
    )
    openlist_admin_token: str = Field(
        default="",
        title="OpenList 管理员令牌"
    )
    openlist_storage_id: int = Field(
        default=1,
        title="存储空间 ID"
    )
    upload_dir_name: str = Field(
        default="",
        title="云盘目标目录名称 (可选，如 'backup_docker_app')"
    )
    retry_times: int = Field(
        default=3,
        title="单次上传重试次数"
    )
    retry_interval: int = Field(
        default=60,
        title="失败重试间隔(秒)"
    )
    max_retry_count: int = Field(
        default=10,
        title="最大重试次数"
    )
    cloud_retain_days: int = Field(
        default=30,
        title="云端保留天数"
    )
    cleanup_interval: int = Field(
        default=60,
        title="清理检查间隔(分钟)"
    )
