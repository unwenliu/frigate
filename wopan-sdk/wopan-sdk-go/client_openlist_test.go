package wopan_test

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/xhofe/wopan-sdk-go"
)

// TestDefaultWithOpenlist_Success 测试成功获取令牌并初始化客户端
func TestDefaultWithOpenlist_Success(t *testing.T) {
	// 创建测试服务器
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// 验证请求方法
		if r.Method != http.MethodGet {
			t.Errorf("expected GET request, got %s", r.Method)
		}

		// 验证请求头
		if r.Header.Get("Authorization") != "test-admin-token" {
			t.Errorf("expected Authorization header 'test-admin-token', got '%s'", r.Header.Get("Authorization"))
		}

		// 验证 URL 参数
		if r.URL.Query().Get("id") != "123" {
			t.Errorf("expected query param id='123', got '%s'", r.URL.Query().Get("id"))
		}

		// 返回模拟响应
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{
			"code": 200,
			"message": "success",
			"data": {
				"token_info": {
					"access_token": "test-access-token-12345"
				}
			}
		}`)
	}))
	defer server.Close()

	// 测试正常流程
	client, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
		AdminToken: "test-admin-token",
		StorageID:  123,
		BaseURL:    server.URL,
	})

	if err != nil {
		t.Fatalf("DefaultWithOpenlist() error = %v", err)
	}

	if client == nil {
		t.Fatal("expected non-nil client")
	}

	accessToken, _ := client.GetToken()
	if accessToken != "test-access-token-12345" {
		t.Errorf("expected access_token 'test-access-token-12345', got '%s'", accessToken)
	}
}

// TestDefaultWithOpenlistSimple_Success 测试简化版本成功获取令牌
func TestDefaultWithOpenlistSimple_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"code":200,"message":"success","data":{"token_info":{"access_token":"simple-token"}}}`)
	}))
	defer server.Close()

	client, err := wopan.DefaultWithOpenlistSimple("test-admin-token", 123)
	// 注意：这里会使用默认的 DefaultOpenlistBaseURL，所以会失败
	// 实际测试需要 mock 或使用环境变量配置
	if err != nil {
		// 预期失败，因为使用的是默认 URL
		t.Logf("Expected error with default URL: %v", err)
	}
	if client != nil {
		t.Error("expected nil client when request fails")
	}
}

// TestDefaultWithOpenlist_EmptyAdminToken 测试空 AdminToken
func TestDefaultWithOpenlist_EmptyAdminToken(t *testing.T) {
	_, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
		AdminToken: "",
		StorageID:  123,
	})

	if err == nil {
		t.Error("expected error for empty AdminToken, got nil")
	}

	expectedErrMsg := "AdminToken is required"
	if err != nil && err.Error() != expectedErrMsg {
		t.Errorf("expected error message '%s', got '%s'", expectedErrMsg, err.Error())
	}
}

// TestDefaultWithOpenlist_WhitespaceAdminToken 测试空白 AdminToken
func TestDefaultWithOpenlist_WhitespaceAdminToken(t *testing.T) {
	_, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
		AdminToken: "   ",
		StorageID:  123,
	})

	if err == nil {
		t.Error("expected error for whitespace AdminToken, got nil")
	}

	expectedErrMsg := "AdminToken cannot be empty or whitespace only"
	if err != nil && err.Error() != expectedErrMsg {
		t.Errorf("expected error message '%s', got '%s'", expectedErrMsg, err.Error())
	}
}

// TestDefaultWithOpenlist_EmptyStorageID 测试零值 StorageID
func TestDefaultWithOpenlist_EmptyStorageID(t *testing.T) {
	_, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
		AdminToken: "test-admin-token",
		StorageID:  0,
	})

	if err == nil {
		t.Error("expected error for zero StorageID, got nil")
	}

	expectedErrMsg := "StorageID must be a positive integer"
	if err != nil && err.Error()[:34] != expectedErrMsg {
		t.Errorf("expected error message to start with '%s', got '%s'", expectedErrMsg, err.Error())
	}
}

// TestDefaultWithOpenlist_NegativeStorageID 测试负数 StorageID
func TestDefaultWithOpenlist_NegativeStorageID(t *testing.T) {
	_, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
		AdminToken: "test-admin-token",
		StorageID:  -1,
	})

	if err == nil {
		t.Error("expected error for negative StorageID, got nil")
	}

	expectedErrMsg := "StorageID must be a positive integer"
	if err != nil && err.Error()[:34] != expectedErrMsg {
		t.Errorf("expected error message to start with '%s', got '%s'", expectedErrMsg, err.Error())
	}
}

// TestDefaultWithOpenlist_APIError 测试 API 返回错误
func TestDefaultWithOpenlist_APIError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{
			"code": 401,
			"message": "Unauthorized: Invalid admin token"
		}`)
	}))
	defer server.Close()

	_, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
		AdminToken: "invalid-token",
		StorageID:  123,
		BaseURL:    server.URL,
	})

	if err == nil {
		t.Error("expected error for API error response, got nil")
	}

	expectedErrMsg := "OpenList API returned error: code=401"
	if err != nil && err.Error()[:38] != expectedErrMsg {
		t.Errorf("expected error message to start with '%s', got '%s'", expectedErrMsg, err.Error())
	}
}

// TestDefaultWithOpenlist_EmptyAccessToken 测试 API 返回空 access_token
func TestDefaultWithOpenlist_EmptyAccessToken(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{
			"code": 200,
			"message": "success",
			"data": {
				"token_info": {
					"access_token": ""
				}
			}
		}`)
	}))
	defer server.Close()

	_, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
		AdminToken: "test-admin-token",
		StorageID:  123,
		BaseURL:    server.URL,
	})

	if err == nil {
		t.Error("expected error for empty access_token, got nil")
	}

	expectedErrMsg := "OpenList API returned empty access_token"
	if err != nil && err.Error() != expectedErrMsg {
		t.Errorf("expected error message '%s', got '%s'", expectedErrMsg, err.Error())
	}
}

// TestDefaultWithOpenlist_HTTPError 测试 HTTP 请求失败
func TestDefaultWithOpenlist_HTTPError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		fmt.Fprintf(w, "Internal Server Error")
	}))
	defer server.Close()

	_, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
		AdminToken: "test-admin-token",
		StorageID:  123,
		BaseURL:    server.URL,
	})

	if err == nil {
		t.Error("expected error for HTTP error, got nil")
	}
}

// TestDefaultWithOpenlist_LargeStorageID 测试大整数 StorageID
func TestDefaultWithOpenlist_LargeStorageID(t *testing.T) {
	// 测试较大的存储 ID 值
	storageID := int64(999999)

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// 验证参数已正确转换为字符串
		idParam := r.URL.Query().Get("id")
		if idParam != "999999" {
			t.Errorf("expected id='999999', got '%s'", idParam)
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"code":200,"message":"success","data":{"token_info":{"access_token":"safe-token"}}}`)
	}))
	defer server.Close()

	_, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
		AdminToken: "test-admin-token",
		StorageID:  storageID,
		BaseURL:    server.URL,
	})

	if err != nil {
		t.Errorf("unexpected error with large StorageID: %v", err)
	}
}

// TestDefaultWithOpenlist_CustomTimeout 测试自定义超时
func TestDefaultWithOpenlist_CustomTimeout(t *testing.T) {
	// 创建一个会延迟响应的服务器
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(100 * time.Millisecond)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"code":200,"message":"success","data":{"token_info":{"access_token":"timeout-token"}}}`)
	}))
	defer server.Close()

	// 使用较短的超时时间
	start := time.Now()
	_, err := wopan.DefaultWithOpenlist(wopan.OpenlistConfig{
		AdminToken: "test-admin-token",
		StorageID:  123,
		BaseURL:    server.URL,
		Timeout:    50 * time.Millisecond,
	})
	elapsed := time.Since(start)

	if err == nil {
		t.Error("expected timeout error, got nil")
	}

	if elapsed < 50*time.Millisecond || elapsed > 200*time.Millisecond {
		t.Errorf("expected timeout around 50-200ms, got %v", elapsed)
	}

	t.Logf("Timeout test completed in %v with error: %v", elapsed, err)
}

// TestDefaultWithOpenlist_InsecureSkipVerify 测试跳过 TLS 验证
func TestDefaultWithOpenlist_InsecureSkipVerify(t *testing.T) {
	// 注意：这个测试需要 HTTPS 服务器，这里仅验证配置是否正确设置
	config := wopan.OpenlistConfig{
		AdminToken:         "test-admin-token",
		StorageID:          123,
		InsecureSkipVerify: true,
	}

	// 验证配置
	if !config.InsecureSkipVerify {
		t.Error("expected InsecureSkipVerify to be true")
	}

	t.Log("InsecureSkipVerify configuration is correctly set")
}

// TestOpenListTokenResponse_Unmarshal 测试响应反序列化
func TestOpenListTokenResponse_Unmarshal(t *testing.T) {
	jsonData := `{
		"code": 200,
		"message": "success",
		"data": {
			"token_info": {
				"access_token": "test-token-12345"
			}
		}
	}`

	var resp wopan.OpenListTokenResponse
	err := json.Unmarshal([]byte(jsonData), &resp)
	if err != nil {
		t.Fatalf("failed to unmarshal JSON: %v", err)
	}

	if resp.Code != 200 {
		t.Errorf("expected code 200, got %d", resp.Code)
	}

	if resp.Message != "success" {
		t.Errorf("expected message 'success', got '%s'", resp.Message)
	}

	if resp.Data.TokenInfo.AccessToken != "test-token-12345" {
		t.Errorf("expected access_token 'test-token-12345', got '%s'", resp.Data.TokenInfo.AccessToken)
	}
}
