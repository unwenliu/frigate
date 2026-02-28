

# 管理后台 API 文档

本文档描述 OpenList 管理后台的内部 API 接口。

## 存储管理接口

### GET /api/admin/storage/get_access_token

获取指定存储的访问令牌信息。

#### 认证方式

此接口需要管理员权限，必须提供有效的认证 token。

**认证方式（二选一）：**

1. **全局管理 Token**：在请求头中添加 `Authorization` 字段，值为设置中配置的 Token
2. **JWT Token**：登录后获取的 JWT Token（需要登录用户具有管理员权限）

#### 请求头

| 参数名       | 类型   | 必填 | 说明                                     |
| ------------ | ------ | ---- | ---------------------------------------- |
| Authorization | string | 是   | 认证 Token（全局管理 Token 或 JWT Token） |

#### 请求参数

| 参数名 | 类型   | 必填 | 说明   |
| ------ | ------ | ---- | ------ |
| id     | number | 是   | 存储 ID |

#### 请求示例

**使用全局管理 Token：**
```bash
curl -H "Authorization: your_global_admin_token" \
  "http://localhost:5244/api/admin/storage/get_access_token?id=1"
```

**使用 JWT Token（登录后获取）：**
```bash
curl -H "Authorization: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  "http://localhost:5244/api/admin/storage/get_access_token?id=1"
```

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "storage_id": 1,
    "driver": "AliyundriveOpen",
    "mount_path": "/阿里云盘",
    "token_info": {
      "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
      "device_id": "xxx",
      "drive_id": "xxx"
    },
    "has_token": true
  }
}
```

#### token_info 字段说明

根据不同的存储驱动类型，`token_info` 返回的字段会有所不同：

##### 通用字段

所有驱动都可能包含：
- `access_token`: 访问令牌

##### 阿里云盘系列 (Aliyundrive, AliyundriveShare, AliyundriveOpen)

- `access_token`: 访问令牌
- `device_id`: 设备 ID
- `drive_id`: 驱动 ID

##### OneDrive 系列 (Onedrive, OnedriveAPP)

- `access_token`: 访问令牌
- `tenant_id`: 租户 ID
- `client_id`: 客户端 ID

##### 123 云盘系列 (123Open, 123Share)

- `access_token`: 访问令牌
- `client_id`: 客户端 ID
- `uid`: 用户 ID

#### 错误响应

**参数错误：**
```json
{
  "code": 400,
  "message": "invalid id",
  "data": null
}
```

**认证失败（Token 无效或未提供）：**
```json
{
  "code": 401,
  "message": "token not valid",
  "data": null
}
```

**权限不足（非管理员用户）：**
```json
{
  "code": 403,
  "message": "You are not an admin",
  "data": null
}
```

**存储不存在：**
```json
{
  "code": 500,
  "message": "storage not found",
  "data": null
}
```

#### 使用场景

该接口主要用于：
1. 查看存储的令牌状态，验证令牌是否存在
2. 获取存储的认证信息，用于调试和问题排查
3. 在管理界面展示存储的认证详情

#### 注意事项

- 此接口属于管理后台 API，需要管理员权限
- 返回的 `access_token` 为敏感信息，请妥善保管
- 不同驱动类型返回的额外字段不同，具体取决于驱动的配置
