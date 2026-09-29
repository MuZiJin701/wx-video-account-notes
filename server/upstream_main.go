// Copy this file to cmd/notes-resolver/main.go in the pinned upstream checkout.
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"

	"wx_channel/pkg/scraper/wxchannels"
)

var shareLink = regexp.MustCompile(`^https://weixin\.qq\.com/sph/[A-Za-z0-9_-]+/?$`)

func parse(link, cookie string) (json.RawMessage, string) {
	if !shareLink.MatchString(link) {
		return nil, "INVALID_LINK"
	}
	if cookie == "" {
		return nil, "LOGIN_REQUIRED"
	}
	// ponytail: upstream has no HTTP deadline; isolate each parse in a subprocess if hangs become frequent.
	feed, err := wxchannels.FetchVideoProfileWithShareUrl(link, cookie)
	if err != nil {
		if strings.Contains(err.Error(), "parse share url") {
			return nil, "LOGIN_EXPIRED_OR_UPSTREAM_CHANGED"
		}
		return nil, "FEED_UNAVAILABLE_OR_UPSTREAM_CHANGED"
	}
	return feed, ""
}

func reply(w http.ResponseWriter, status int, code string, data json.RawMessage) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(struct {
		Code string          `json:"code"`
		Msg  string          `json:"msg"`
		Data json.RawMessage `json:"data,omitempty"`
	}{Code: code, Msg: code, Data: data})
}

func main() {
	// The pinned upstream logs share links and feed tokens; keep them out of service logs.
	log.SetOutput(io.Discard)
	if len(os.Args) == 3 && os.Args[1] == "--check-cookie" {
		cookie, err := io.ReadAll(io.LimitReader(os.Stdin, 16<<10))
		if err != nil {
			os.Exit(1)
		}
		_, code := parse(os.Args[2], strings.TrimSpace(string(cookie)))
		if code != "" {
			fmt.Fprintln(os.Stderr, code)
			os.Exit(1)
		}
		fmt.Println("PARSE_OK")
		return
	}
	if len(os.Args) != 1 {
		os.Exit(2)
	}
	http.HandleFunc("/internal/parse", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet || r.URL.Path != "/internal/parse" {
			reply(w, http.StatusNotFound, "NOT_FOUND", nil)
			return
		}
		cookie, err := os.ReadFile("/root/projects/wx-video-account-notes/cookie")
		if err != nil {
			reply(w, http.StatusServiceUnavailable, "LOGIN_REQUIRED", nil)
			return
		}
		feed, code := parse(r.URL.Query().Get("url"), strings.TrimSpace(string(cookie)))
		if code != "" {
			status := http.StatusBadGateway
			if code == "INVALID_LINK" {
				status = http.StatusBadRequest
			} else if code == "LOGIN_REQUIRED" || code == "LOGIN_EXPIRED_OR_UPSTREAM_CHANGED" {
				status = http.StatusServiceUnavailable
			}
			reply(w, status, code, nil)
			return
		}
		reply(w, http.StatusOK, "OK", feed)
	})
	server := &http.Server{Addr: "127.0.0.1:17879", ReadHeaderTimeout: 5 * time.Second}
	if err := server.ListenAndServe(); err != nil {
		fmt.Fprintln(os.Stderr, "resolver listen failed")
		os.Exit(1)
	}
}
