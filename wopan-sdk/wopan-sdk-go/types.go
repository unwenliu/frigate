package wopan

import "encoding/json"

type Json map[string]interface{}

func copyJson(src Json) Json {
	dst := make(Json, len(src))
	for k, v := range src {
		dst[k] = v
	}
	return dst
}

type Header struct {
	Key     string `json:"key"`
	ResTime int64  `json:"resTime"`
	ReqSeq  int    `json:"reqSeq"`
	Channel string `json:"channel"`
	Sign    string `json:"sign"`
	Version string `json:"version"`
}

type Req[T any] struct {
	Header `json:"header"`
	Body   T `json:"body"`
}

type Resp struct {
	Status string `json:"STATUS"`
	Msg    string `json:"MSG"`
	LogID  string `json:"LOGID"`
	Rsp    struct {
		RspCode string          `json:"RSP_CODE"`
		RspDesc string          `json:"RSP_DESC"`
		Data    json.RawMessage `json:"DATA"`
	} `json:"RSP"`
}

// OpenListTokenResponse OpenList API 获取令牌的响应
type OpenListTokenResponse struct {
	Code    int `json:"code"`
	Message string `json:"message"`
	Data    struct {
		TokenInfo struct {
			AccessToken string `json:"access_token"`
		} `json:"token_info"`
	} `json:"data"`
}
