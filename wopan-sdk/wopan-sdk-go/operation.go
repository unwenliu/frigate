package wopan

func (w *WoClient) InitPhone() error {
	if w.Phone == "" {
		_resp, err := w.AppQueryUser()
		if err != nil {
			return err
		}
		w.Phone = _resp.UserId
	}
	return nil
}

func (w *WoClient) InitClassifyRule() error {
	if w.ClassifyRuleData != nil {
		return nil
	}
	data, err := w.ClassifyRule()
	if err != nil {
		return err
	}
	w.ClassifyRuleData = data
	return nil
}

func (w *WoClient) InitZoneURL() error {
	if w.ZoneURL != "" {
		return nil
	}
	data, err := w.GetZoneInfo()
	if err != nil {
		return err
	}
	w.ZoneURL = data.Url
	return nil
}

// RefreshToken 刷新访问令牌
//
// 如果客户端是通过 OpenList 初始化的，会自动从 OpenList 重新获取 access_token。
// 否则，如果有设置回调函数，则调用回调函数由用户处理刷新逻辑。
func (w *WoClient) RefreshToken() error {
	// 使用锁防止并发刷新
	w.refreshingLock.Lock()
	defer w.refreshingLock.Unlock()

	// 优先使用 OpenList 配置自动刷新
	if w.openlistConfig != nil {
		return w.refreshFromOpenlist()
	}

	// 其次使用标准的 refresh_token 刷新
	resp, err := w.AppRefreshToken()
	if err != nil {
		return err
	}
	w.onRefreshToken(resp.AccessToken, resp.RefreshToken)
	w.SetAccessToken(resp.AccessToken)
	w.SetRefreshToken(resp.RefreshToken)
	return nil
}

// refreshFromOpenlist 从 OpenList 管理后台重新获取 access_token
func (w *WoClient) refreshFromOpenlist() error {
	if w.openlistConfig == nil {
		return fmt.Errorf("openlist config is nil")
	}

	config := *w.openlistConfig

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

	// 发送请求获取 access_token
	var tokenResp OpenListTokenResponse
	apiURL := fmt.Sprintf("%s%s/%s?id=%d", baseURL, OpenListAPIPath, KeyOpenListGetAccessToken, config.StorageID)
	resp, err := restyClient.R().
		SetHeader("Authorization", config.AdminToken).
		SetResult(&tokenResp).
		Get(apiURL)

	if err != nil {
		return fmt.Errorf("failed to refresh token from OpenList API: %w", err)
	}

	// 验证 HTTP 响应
	if resp.RawResponse == nil {
		return fmt.Errorf("OpenList API returned empty response")
	}

	if resp.IsError() {
		return fmt.Errorf("OpenList API request failed with status: %s", resp.Status())
	}

	// 验证业务状态码
	if tokenResp.Code != 200 {
		return fmt.Errorf("OpenList API returned error: code=%d, message=%s", tokenResp.Code, tokenResp.Message)
	}

	// 验证 access_token
	if tokenResp.Data.TokenInfo.AccessToken == "" {
		return fmt.Errorf("OpenList API returned empty access_token")
	}

	// 更新客户端的 access_token
	w.SetAccessToken(tokenResp.Data.TokenInfo.AccessToken)

	return nil
}

func (w *WoClient) InitData() error {
	if w.accessToken == "" && w.refreshToken != "" {
		if err := w.RefreshToken(); err != nil {
			return err
		}
	}
	if err := w.InitPhone(); err != nil {
		return err
	}
	if err := w.InitClassifyRule(); err != nil {
		return err
	}
	if err := w.InitZoneURL(); err != nil {
		return err
	}
	return nil
}
