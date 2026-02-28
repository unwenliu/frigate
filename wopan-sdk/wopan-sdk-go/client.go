package wopan

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/http"
	"path"
	"strings"
	"sync"
	"time"

	"github.com/go-resty/resty/v2"
)

type WoClient struct {
	accessToken  string
	refreshToken string
	psToken      string

	client            *resty.Client
	crypto            *Crypto
	ua                string
	jsonMarshalFunc   func(v interface{}) ([]byte, error)
	jsonUnmarshalFunc func(data []byte, v interface{}) error

	Phone            string
	ZoneURL          string
	zoneURLOnce      sync.Once
	ClassifyRuleData *ClassifyRuleData

	onRefreshToken func(accessToken, refreshToken string)
}

func New(opts ...Option) *WoClient {
	w := &WoClient{
		client:            resty.New(),
		crypto:            NewCrypto(),
		jsonMarshalFunc:   json.Marshal,
		jsonUnmarshalFunc: json.Unmarshal,
	}
	for _, opt := range opts {
		opt(w)
	}
	return w
}

func DefaultWithAccessToken(accessToken string) *WoClient {
	w := Default()
	w.SetAccessToken(accessToken)
	return w
}

func DefaultWithRefreshToken(refreshToken string) *WoClient {
	w := Default()
	w.SetRefreshToken(refreshToken)
	return w
}

func DefaultWithAccessAndPsToken(refreshToken, psToken string) *WoClient {
	w := Default()
	w.SetAccessToken(refreshToken)
	w.SetPsToken(psToken)
	return w
}

func Default() *WoClient {
	return New(WithUA(DefaultUA))
}

func (w *WoClient) SetUA(ua string) {
	w.ua = ua
}

func (w *WoClient) SetJsonMarshalFunc(f func(v interface{}) ([]byte, error)) {
	w.jsonMarshalFunc = f
}

func (w *WoClient) SetJsonUnmarshalFunc(f func(data []byte, v interface{}) error) {
	w.jsonUnmarshalFunc = f
}

func (w *WoClient) SetAccessToken(token string) {
	w.accessToken = token
	_ = w.crypto.SetAccessToken(token)
}

func (w *WoClient) SetRefreshToken(token string) {
	w.refreshToken = token
}

func (w *WoClient) SetPsToken(psToken string) {
	w.psToken = psToken
}

func (w *WoClient) GetToken() (string, string) {
	return w.accessToken, w.refreshToken
}

func (w *WoClient) SetHttpClient(httpClient *http.Client) *WoClient {
	w.client = resty.NewWithClient(httpClient)
	return w
}

func (w *WoClient) SetUserAgent(userAgent string) *WoClient {
	w.client.SetHeader("User-Agent", userAgent)
	return w
}

func (w *WoClient) SetDebug(d bool) *WoClient {
	w.client.SetDebug(d)
	return w
}

func (w *WoClient) EnableTrace() *WoClient {
	w.client.EnableTrace()
	return w
}

func (w *WoClient) SetProxy(proxy string) *WoClient {
	w.client.SetProxy(proxy)
	return w
}

func (w *WoClient) NewRequest() *resty.Request {
	return w.client.R()
}

func (w *WoClient) GetFileType(filename string) string {
	ext := path.Ext(filename)
	if ext == "" {
		return "5"
	}
	ext = ext[1:]
	err := w.InitClassifyRule()
	if err != nil {
		return "5"
	}
	if _type, ok := w.ClassifyRuleData.FileTypes[ext]; ok {
		return _type.Type
	}
	return "5"
}

func (w *WoClient) OnRefreshToken(f func(accessToken, refreshToken string)) {
	w.onRefreshToken = f
}

// OpenlistConfig OpenList 管理后台配置
type OpenlistConfig struct {
	// AdminToken OpenList 管理后台的认证令牌
	AdminToken string

	// StorageID 存储空间 ID
	StorageID int64

	// BaseURL OpenList API 基础 URL，可选
	// 默认使用 DefaultOpenlistBaseURL
	BaseURL string

	// Timeout HTTP 请求超时时间，可选
	// 默认使用 OpenlistTimeout
	Timeout time.Duration

	// InsecureSkipVerify 是否跳过 TLS 证书验证，可选
	// 默认为 false
	// ⚠️ 仅用于测试环境，生产环境请勿使用
	InsecureSkipVerify bool

	// HTTPClient 自定义 HTTP 客户端，可选
	// 如果提供，将使用该客户端而不是创建新的
	HTTPClient *http.Client
}

// DefaultWithOpenlist 通过 OpenList 管理后台 API 获取 access_token 并初始化 WoClient
//
// 参数：
//   - config: OpenlistConfig 配置对象
//
// 返回：
//   - *WoClient: 初始化后的 WoClient 实例
//   - error: 可能的错误包括：
//   - 参数验证错误（AdminToken 或 StorageID 为空或格式不正确）
//   - 网络请求错误
//   - API 返回错误（code != 200）
//   - access_token 为空
//
// 使用示例：
//
//	client, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
//	    AdminToken: "your-admin-token",
//	    StorageID:  1,
//	})
//	if err != nil {
//	    log.Fatal(err)
//	}
//
// 高级用法：
//
//	client, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
//	    AdminToken:         "your-admin-token",
//	    StorageID:          1,
//	    BaseURL:            "https://custom.openlist.com",
//	    Timeout:            60 * time.Second,
//	    InsecureSkipVerify: false,
//	})
func DefaultWithOpenlist(config OpenlistConfig) (*WoClient, error) {
	// 参数验证
	if config.AdminToken == "" {
		return nil, fmt.Errorf("AdminToken is required")
	}
	// 去除首尾空格并验证
	config.AdminToken = strings.TrimSpace(config.AdminToken)
	if config.AdminToken == "" {
		return nil, fmt.Errorf("AdminToken cannot be empty or whitespace only")
	}

	// 验证 StorageID 为正整数
	if config.StorageID <= 0 {
		return nil, fmt.Errorf("StorageID must be a positive integer, got: %d", config.StorageID)
	}

	// 设置默认值
	baseURL := config.BaseURL
	if baseURL == "" {
		baseURL = DefaultOpenlistBaseURL
	}

	timeout := config.Timeout
	if timeout == 0 {
		timeout = OpenlistTimeout * time.Second
	}

	// 创建 HTTP 客户端
	var httpClient *http.Client
	if config.HTTPClient != nil {
		httpClient = config.HTTPClient
	} else {
		httpClient = &http.Client{
			Timeout: timeout,
			Transport: &http.Transport{
				TLSClientConfig: &tls.Config{
					InsecureSkipVerify: config.InsecureSkipVerify,
				},
			},
		}
	}

	// 创建 resty 客户端
	restyClient := resty.NewWithClient(httpClient)

	// 发送请求获取 access_token（StorageID 为 int64，无需 URL 编码）
	var tokenResp OpenListTokenResponse
	apiURL := fmt.Sprintf("%s%s/%s?id=%d", baseURL, OpenListAPIPath, KeyOpenListGetAccessToken, config.StorageID)
	resp, err := restyClient.R().
		SetHeader("Authorization", config.AdminToken).
		SetResult(&tokenResp).
		Get(apiURL)

	if err != nil {
		return nil, fmt.Errorf("failed to request OpenList API: %w", err)
	}

	// 验证 HTTP 响应
	if resp.RawResponse == nil {
		return nil, fmt.Errorf("OpenList API returned empty response")
	}

	if resp.IsError() {
		return nil, fmt.Errorf("OpenList API request failed with status: %s", resp.Status())
	}

	// 验证业务状态码
	if tokenResp.Code != 200 {
		return nil, fmt.Errorf("OpenList API returned error: code=%d, message=%s", tokenResp.Code, tokenResp.Message)
	}

	// 验证 access_token
	if tokenResp.Data.TokenInfo.AccessToken == "" {
		return nil, fmt.Errorf("OpenList API returned empty access_token")
	}

	// 使用获取到的 access_token 初始化 WoClient
	w := Default()
	w.SetAccessToken(tokenResp.Data.TokenInfo.AccessToken)
	return w, nil
}

// DefaultWithOpenlistSimple 通过 OpenList 管理后台 API 获取 access_token 并初始化 WoClient（简化版本）
//
// 参数：
//   - adminToken: OpenList 管理后台的认证令牌
//   - storageID: 存储空间 ID
//
// 返回：
//   - *WoClient: 初始化后的 WoClient 实例
//   - error: 获取令牌或初始化过程中的错误
//
// 使用示例：
//
//	client, err := wopan.DefaultWithOpenlistSimple("your-admin-token", 1)
//	if err != nil {
//	    log.Fatal(err)
//	}
func DefaultWithOpenlistSimple(adminToken string, storageID int64) (*WoClient, error) {
	return DefaultWithOpenlist(OpenlistConfig{
		AdminToken: adminToken,
		StorageID:  storageID,
	})
}
