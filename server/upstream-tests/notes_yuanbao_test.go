// Copy to pkg/scraper/wxchannels/notes_yuanbao_test.go in the pinned checkout.
package wxchannels

import (
	"io"
	"net/http"
	"strings"
	"testing"
)

type notesTransport func(*http.Request) (*http.Response, error)

func (transport notesTransport) RoundTrip(request *http.Request) (*http.Response, error) {
	return transport(request)
}

func TestNotesRejectsUnusableYuanbaoResponses(t *testing.T) {
	original := http.DefaultTransport
	defer func() { http.DefaultTransport = original }()
	for _, sample := range []struct {
		status int
		body   string
	}{
		{401, `{"code":0,"data":{"wx_export_id":"id","playable_url":"url"}}`},
		{200, `{"code":401,"msg":"login required"}`},
		{200, `{"code":0,"data":{}}`},
	} {
		http.DefaultTransport = notesTransport(func(_ *http.Request) (*http.Response, error) {
			return &http.Response{StatusCode: sample.status, Body: io.NopCloser(strings.NewReader(sample.body))}, nil
		})
		if _, err := ParseShareUrl("https://weixin.qq.com/sph/test", "placeholder"); err == nil {
			t.Fatalf("expected error for status %d and body %s", sample.status, sample.body)
		}
	}
}
