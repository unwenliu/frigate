# wopan-sdk-go 模块文档

[根目录](../CLAUDE.md) > **wopan-sdk-go**

---

> 最后更新：2026-03-01 14:00:41
> 状态：已实现 OpenList 自动刷新功能

---

## 变更记录 (Changelog)

| 时间 | 变更内容 |
|------|----------|
| 2026-03-01 14:00:41 | 新增 OpenList 自动刷新 access_token 功能及完整测试覆盖（10 个测试用例） |
| 2026-02-26 14:11:25 | 更新文档：补充依赖信息和 API 方法列表 |
| 2026-02-25 21:31:54 | 新增 OpenList 管理后台认证支持文档，补充完整测试列表 |
| 2026-02-21 16:30:19 | 初始化模块文档，记录入口、接口、测试配置 |

---

## 模块职责

联通沃盘 Go 语言 SDK，提供完整的文件管理、上传下载和用户认证功能。

**核心功能：**
- 用户认证与令牌管理
- 文件查询、创建、重命名、移动、复制、删除
- 分片上传与断点续传
- AES 加密/解密
- 多空间类型支持（个人/家庭/私有）
- **OpenList 管理后台认证支持**（新增）
- **OpenList 自动刷新 access_token**（新增）

---

## 入口与启动

### 主入口文件
- **`client.go`** - `WoClient` 核心客户端类
- **`go.mod`** - Go 模块定义

### 快速初始化

```go
package main

import (
    "fmt"
    "github.com/xhofe/wopan-sdk-go"
)

func main() {
    // 使用刷新令牌初始化
    w := wopan.DefaultWithRefreshToken("your-refresh-token")

    // 查询用户信息
    user, err := w.AppQueryUser()
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    fmt.Printf("User: %+v\n", user)
}
```

### 使用 OpenList 管理后台认证（推荐）

```go
// 使用 OpenList 管理后台 API 获取令牌并初始化
client, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
    AdminToken: "your-admin-token",
    StorageID:  1,
})
if err != nil {
    log.Fatal(err)
}

// SDK 会在令牌过期时自动调用 RefreshToken() 从 OpenList 获取新令牌
// 无需手动处理令牌刷新逻辑

// 或使用简化版本
client, err := wopan.DefaultWithOpenlistSimple("your-admin-token", 1)
```

### 客户端配置选项

```go
import "github.com/go-resty/resty/v2"

// 使用 Option 模式配置客户端
client := wopan.New(
    wopan.WithUA("Custom User-Agent"),
    wopan.WithHttpClient(customHTTPClient),
)

// 或使用链式调用
wopan.Default().
    SetDebug(true).
    SetProxy("http://proxy:8080").
    EnableTrace()
```

---

## 对外接口

### 用户认证 API (api-user.go)

| 方法 | 说明 | 请求类型 |
|------|------|----------|
| `PcWebLogin(phone, password)` | PC Web 登录 | 无加密 |
| `PcLoginVerifyCode(phone, password, code)` | 验证码登录 | 无加密 |
| `AppQueryUser()` | 查询用户信息 | 已加密 |
| `AppRefreshToken()` | 刷新访问令牌 | 无加密 |
| `AppLogout()` | 登出 | 已加密 |

### 文件系统 API (api-fs.go)

| 方法 | 说明 | 空间类型 |
|------|------|----------|
| `QueryAllFilesPersonal(parentId, pageNum, pageSize, sortRule)` | 查询个人空间文件 | 个人 |
| `QueryAllFilesFamily(parentId, pageNum, pageSize, sortRule, familyId)` | 查询家庭空间文件 | 家庭 |
| `GetSearchDirectory(directoryId)` | 获取子目录列表 | 通用 |
| `GetDownloadUrlV2(fidList)` | 获取下载链接 V2 | 通用 |
| `GetDownloadUrl(spaceType, fidList)` | 获取下载链接 | 通用 |
| `CreateDirectory(spaceType, parentId, name, familyId)` | 创建目录 | 全部 |
| `RenameFileOrDirectoryPersonal(fileType, id, name)` | 重命名（个人） | 个人 |
| `RenameFileOrDirectoryFamily(fileType, id, name, familyId)` | 重命名（家庭） | 家庭 |
| `MoveFile(dirList, fileList, targetDirId, sourceType, targetType, ...)` | 移动文件 | 通用 |
| `CopyFile(dirList, fileList, targetDirId, sourceType, targetType, ...)` | 复制文件 | 通用 |
| `DeleteFile(spaceType, dirList, fileList)` | 删除文件 | 全部 |
| `EmptyRecycleData()` | 清空回收站 | 通用 |

### 上传 API (upload.go)

| 方法 | 说明 |
|------|------|
| `Upload2CPersonal(file, targetDirId, opt)` | 上传到个人空间 |
| `Upload2CFamily(file, targetDirId, familyId, opt)` | 上传到家庭空间 |

### WoHome API (api-wohome.go)

| 方法 | 说明 |
|------|------|
| `FCloudProductOrdListQry()` | 查询产品订单列表 |
| `QueryCloudUsageInfo()` | 查询云空间使用情况 |
| `FCloudProductPackage()` | 查询产品套餐 |
| `ClassifyRule()` | 获取文件分类规则 |
| `GetZoneInfo()` | 获取区域信息 |
| `QuerySysConfig()` | 查询系统配置 |
| `FamilyUserCurrentEncode()` | 家庭用户编码 |
| `PrivateSpaceLogin()` | 私有空间登录 |

---

## 关键依赖与配置

### 依赖 (go.mod)

```go
module github.com/xhofe/wopan-sdk-go

go 1.20

require github.com/go-resty/resty/v2 v2.7.0
require golang.org/x/net v0.11.0 // indirect
```

### 核心常量 (consts.go)

```go
const (
    DefaultClientID     = "1001000021"
    DefaultClientSecret = "XFmi9GS2hzk98jGX"
    DefaultBaseURL      = "https://panservice.mail.wo.cn"
    DefaultZoneURL      = "https://tjupload.pan.wo.cn"
    DefaultPartSize     = 8 * 1024 * 1024  // 8MB 分片大小
    DefaultOpenlistBaseURL = "https://openlist.example.com"
    OpenlistTimeout     = 30  // 秒
)

// 空间类型
const (
    SpaceTypePersonal = "0"  // 个人空间
    SpaceTypeFamily   = "1"  // 家庭空间
    SpaceTypePrivate  = "4"  // 私有空间
)

// 排序规则
const (
    SortNameAsc  = iota + 1  // 按名称升序
    SortNameDesc              // 按名称降序
    SortSizeAsc               // 按大小升序
    SortSizeDesc              // 按大小降序
    SortTimeAsc               // 按时间升序
    SortTimeDesc              // 按时间降序
)
```

### API 渠道 (channel)

| 渠道 | 用途 |
|------|------|
| `api-user` | 用户认证相关 |
| `wohome` | 文件系统操作 |
| `wocloud` | 云存储上传 |

---

## 数据模型

### 请求/响应类型 (types.go)

```go
// 通用 JSON 类型
type Json map[string]interface{}

// 请求头
type Header struct {
    Key     string `json:"key"`
    ResTime int64  `json:"resTime"`
    ReqSeq  int    `json:"reqSeq"`
    Channel string `json:"channel"`
    Sign    string `json:"sign"`
    Version string `json:"version"`
}

// 通用请求体
type Req[T any] struct {
    Header `json:"header"`
    Body   T `json:"body"`
}

// 通用响应
type Resp struct {
    Status string `json:"STATUS"`
    Msg    string `json:"MSG"`
    LogID  string `json:"LOGID"`
    Rsp    struct {
        RspCode string          `json:"RSP_CODE"`
        RSPDesc string          `json:"RSP_DESC"`
        Data    json.RawMessage `json:"DATA"`
    } `json:"RSP"`
}

// OpenList API 响应
type OpenListTokenResponse struct {
    Code    int `json:"code"`
    Message string `json:"message"`
    Data    struct {
        TokenInfo struct {
            AccessToken string `json:"access_token"`
        } `json:"token_info"`
    } `json:"data"`
}
```

### 文件信息 (api-fs.go)

```go
type File struct {
    FamilyId     int    `json:"familyId"`
    Fid          string `json:"fid"`
    Creator      string `json:"creator"`
    Size         int64  `json:"size"`
    CreateTime   string `json:"createTime"`
    Name         string `json:"name"`
    ShootingTime string `json:"shootingTime"`
    Id           string `json:"id"`
    Type         int    `json:"type"`
    ThumbUrl     string `json:"thumbUrl"`
    FileType     string `json:"fileType"`
}
```

### 上传相关 (upload.go)

```go
type Upload2COption struct {
    OnProgress func(current, total int64)  // 进度回调
    Ctx        context.Context              // 上下文（用于取消）
    RetryTimes int                          // 重试次数
    OnRetry    func(err error, fileName string, partIndex int64, finishedSize int64)
}

type Upload2CFile struct {
    Name        string      // 文件名
    Size        int64       // 文件大小
    Content     *os.File    // 文件内容
    ContentType string      // Content-Type
}
```

### OpenList 配置 (client.go)

```go
type OpenlistConfig struct {
    AdminToken string        // OpenList 管理后台的认证令牌
    StorageID  int64         // 存储空间 ID
    BaseURL    string        // OpenList API 基础 URL（可选）
    Timeout    time.Duration // HTTP 请求超时时间（可选）
    InsecureSkipVerify bool  // 是否跳过 TLS 证书验证（可选）
    HTTPClient *http.Client // 自定义 HTTP 客户端（可选）
}
```

---

## 测试与质量

### 测试文件

| 测试文件 | 覆盖内容 |
|----------|----------|
| `api-user_test.go` | 用户认证 API 测试 |
| `crypto_test.go` | AES 加密/解密测试 |
| `upload_test.go` | 文件上传测试 |
| `client_openlist_test.go` | OpenList 管理后台认证测试 |
| `refresh_token_test.go` | **OpenList 自动刷新功能测试**（新增） |

### OpenList 自动刷新测试用例

`refresh_token_test.go` 包含 10 个完整的测试用例：

1. **TestOpenListAutoRefresh_ConfigCached** - 验证 OpenList 配置被正确缓存
2. **TestOpenListAutoRefresh_RefreshTokenSuccess** - 测试通过 RefreshToken 从 OpenList 刷新令牌
3. **TestOpenListAutoRefresh_RefreshTokenAPIError** - 测试刷新令牌时 API 返回错误
4. **TestOpenListAutoRefresh_ConcurrentRefresh** - 测试并发刷新的安全性（10 个 goroutine）
5. **TestOpenListAutoRefresh_RefreshTokenEmptyToken** - 测试刷新令牌时返回空令牌
6. **TestOpenListAutoRefresh_RefreshTokenHTTPError** - 测试刷新令牌时 HTTP 请求失败
7. **TestOpenListAutoRefresh_NilOpenListConfig** - 测试没有 OpenList 配置时的行为
8. **TestOpenListAutoRefresh_MultipleRefresh** - 测试多次刷新令牌
9. **TestOpenListAutoRefresh_CustomTimeout** - 测试自定义超时配置
10. **TestOpenListAutoRefresh_RefreshLockPreventsRace** - 测试刷新锁防止竞态条件

### 运行测试

```bash
# 运行所有测试
go test -v ./...

# 运行特定测试
go test -v -run TestOpenListAutoRefresh

# 查看覆盖率
go test -cover ./...

# 运行基准测试
go test -bench=. -benchmem
```

---

## 加密机制

### 加密模块 (crypto.go, aes.go)

SDK 使用 AES-CBC 模式进行加密/解密：

```go
// 加密流程
1. 根据渠道选择密钥（api-user 使用 clientSecret，其他使用 accessToken 前16位）
2. 使用 IV "wNSOYIB1k1DjY5lA"
3. AES-CBC 加密
4. Base64 编码输出

// 解密流程
1. Base64 解码
2. 使用相同密钥和 IV 进行 AES-CBC 解密
3. 返回明文字符串
```

### 加密工具类

```go
// Crypto 提供加密/解密功能
type Crypto struct {
    key []byte
    iv  []byte
}

// Encrypt 加密内容并返回 Base64 编码字符串
func (c *Crypto) Encrypt(content string) (string, error)

// Decrypt 解密 Base64 编码字符串
func (c *Crypto) Decrypt(content string) (string, error)
```

---

## OpenList 自动刷新机制

### 触发条件

当 API 返回错误码 `9999`（令牌过期）时，SDK 会自动触发令牌刷新。

### 刷新策略

```go
func (w *WoClient) refreshToken() error {
    // 1. 使用锁防止并发刷新
    w.refreshingLock.Lock()
    defer w.refreshingLock.Unlock()

    // 2. 优先使用 OpenList 配置自动刷新
    if w.openlistConfig != nil {
        return w.refreshFromOpenlist()
    }

    // 3. 其次使用用户自定义的回调函数
    if w.onRefreshToken != nil {
        // 调用回调函数由用户处理刷新逻辑
    }

    return fmt.Errorf("no refresh mechanism available")
}
```

### 线程安全

- 使用 `sync.Mutex` 保护刷新逻辑
- 防止多个 goroutine 同时刷新令牌
- 确保在并发环境下只有一个刷新操作执行

### 配置缓存

- `OpenlistConfig` 在初始化时被保存到 `WoClient.openlistConfig` 字段
- 后续刷新时直接使用缓存的配置，无需用户重新传入

---

## 常见问题 (FAQ)

### Q1: 如何处理私有空间？

需要先设置 `psToken`：

```go
client.SetPsToken("your-ps-token")
// 然后调用私有空间相关 API
```

### Q2: 如何实现断点续传？

上传时使用 `Upload2COption.Ctx` 控制取消，记录已上传的分片索引：

```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

opt := wopan.Upload2COption{
    Ctx:        ctx,
    OnProgress: func(current, total int64) {
        fmt.Printf("Progress: %d/%d\n", current, total)
    },
}

client.Upload2CPersonal(file, dirId, opt)
```

### Q3: 如何启用调试日志？

```go
client.SetDebug(true)
// 或者
client.EnableTrace()
```

### Q4: 如何处理令牌刷新？

**使用 OpenList 自动刷新（推荐）：**

```go
client, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
    AdminToken: "your-admin-token",
    StorageID:  1,
})
// SDK 会自动处理刷新，无需手动干预
```

**使用自定义回调：**

```go
client.OnRefreshToken(func(accessToken, refreshToken string) {
    // 保存新令牌到配置文件或数据库
    saveTokens(accessToken, refreshToken)
})
```

### Q5: OpenList 自动刷新的优缺点是什么？

**优点：**
- 无需手动管理令牌生命周期
- 自动处理令牌过期场景
- 线程安全，支持并发请求
- 可配置超时和重试策略

**缺点：**
- 依赖 OpenList API 可用性
- 需要维护 admin_token 安全性
- 网络延迟可能导致请求重试

### Q6: 如何自定义 OpenList 请求超时？

```go
client, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
    AdminToken: "your-admin-token",
    StorageID:  1,
    Timeout:    60 * time.Second,  // 60 秒超时
})
```

### Q6: 如何设置代理？

```go
client.SetProxy("http://proxy:8080")
```

---

## 相关文件清单

```
wopan-sdk-go/
├── client.go                # 核心客户端类（含 OpenList 支持和自动刷新）
├── types.go                 # 通用数据类型
├── consts.go                # 常量定义
├── option.go                # Option 配置模式
├── vars.go                  # 全局变量
├── header.go                # 请求头处理
├── req_body.go              # 请求体处理
├── request.go               # 请求方法
├── operation.go             # 操作方法
├── aes.go                   # AES 加密实现
├── crypto.go                # 加密工具类
├── api-user.go              # 用户认证 API
├── api-fs.go                # 文件系统 API
├── api-wohome.go            # WoHome API
├── upload.go                # 上传功能
├── api-user_test.go         # 用户认证测试
├── crypto_test.go           # 加密测试
├── upload_test.go           # 上传测试
├── client_openlist_test.go  # OpenList 认证测试
├── refresh_token_test.go    # OpenList 自动刷新测试（新增）
├── go.mod                   # Go 模块定义
├── go.sum                   # 依赖校验和
├── LICENSE                  # MIT 许可证
├── README.md                # 项目说明
├── CLAUDE.md                # 模块 AI 文档
├── .gitignore               # Git 忽略规则
├── .gitattributes           # Git 属性配置
└── docs/                    # 文档目录
    ├── api-user.md
    ├── personal-fs.md
    ├── family-fs.md
    └── wohome.md
```

---

*本文档由 AI 自动生成和维护。*
