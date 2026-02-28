"""
WoPan SDK 常量定义
"""

# 默认配置
DEFAULT_CLIENT_ID = "1001000021"
DEFAULT_CLIENT_SECRET = "XFmi9GS2hzk98jGX"
DEFAULT_APP_ID = "10000001"
DEFAULT_BASE_URL = "https://panservice.mail.wo.cn"
DEFAULT_ZONE_URL = "https://tjupload.pan.wo.cn"
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.37"
DEFAULT_PART_SIZE = 8 * 1024 * 1024  # 8MB

# 渠道定义
CHANNEL_API_USER = "api-user"
CHANNEL_WO_HOME = "wohome"
CHANNEL_WO_CLOUD = "wocloud"

# 空间类型
SPACE_TYPE_PERSONAL = "0"  # 个人空间
SPACE_TYPE_FAMILY = "1"  # 家庭空间
SPACE_TYPE_PRIVATE = "4"  # 私有空间

# API 方法 - api-user
KEY_PC_WEB_LOGIN = "PcWebLogin"
KEY_PC_LOGIN_VERIFY_CODE = "PcLoginVerifyCode"
KEY_APP_QUERY_USER = "AppQueryUser"
KEY_APP_REFRESH_TOKEN = "AppRefreshToken"
KEY_APP_LOGOUT = "AppLogout"

# API 方法 - wohome
KEY_F_CLOUD_PRODUCT_ORD_LIST_QRY = "FCloudProductOrdListQry"
KEY_QUERY_CLOUD_USAGE_INFO = "QueryCloudUsageInfo"
KEY_F_CLOUD_PRODUCT_PACKAGE = "FCloudProductPackage"
KEY_CLASSIFY_RULE = "ClassifyRule"
KEY_GET_ZONE_INFO = "GetZoneInfo"
KEY_QUERY_SYS_CONFIG = "QuerySysConfig"
KEY_FAMILY_USER_CURRENT_ENCODE = "FamilyUserCurrentEncode"
KEY_QUERY_ALL_FILES = "QueryAllFiles"
KEY_GET_SEARCH_DIRECTORY = "GetSearchDirectory"
KEY_GET_DOWNLOAD_URL_V2 = "GetDownloadUrlV2"
KEY_GET_DOWNLOAD_URL = "GetDownloadUrl"
KEY_CREATE_DIRECTORY = "CreateDirectory"
KEY_RENAME_FILE_OR_DIRECTORY = "RenameFileOrDirectory"
KEY_MOVE_FILE = "MoveFile"
KEY_COPY_FILE = "CopyFile"
KEY_DELETE_FILE = "DeleteFile"
KEY_EMPTY_RECYCLE_DATA = "EmptyRecycleData"
KEY_UPLOAD_2C = "upload2C"
KEY_PRIVATE_SPACE_LOGIN = "PrivateSpaceLogin"

# 排序规则
SORT_NAME_ASC = 1
SORT_NAME_DESC = 2
SORT_SIZE_ASC = 3
SORT_SIZE_DESC = 4
SORT_TIME_ASC = 5
SORT_TIME_DESC = 6

# 加密相关
DEFAULT_IV = "wNSOYIB1k1DjY5lA"

# JSON Secret 参数（用于 Wohome API 请求）
JSON_SECRET = {"secret": True}
JSON_CLIENT_ID_SECRET = {
    "clientId": DEFAULT_CLIENT_ID,
    "secret": True,
}

# OpenList 相关常量
DEFAULT_OPENLIST_BASE_URL = "https://openlist.example.com"
DEFAULT_OPENLIST_TIMEOUT = 30  # 默认超时时间（秒）
