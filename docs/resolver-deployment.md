# 自部署视频号解析服务

只想生成笔记？按 [README](../README.md) 安装 Skill 即可，无需服务器。本页供需要**自己运行解析服务**的用户使用。服务器只解析分享链接；下载、OCR、ASR 和写笔记仍在客户端进行。

需要一台 Linux x64 服务器（Python 3、root 权限）和一台装有 Git、Go 的构建机。构建命令使用 POSIX shell，Windows 可在 WSL 中运行。当前脚本固定使用 `/root/projects/wx-video-account-notes/`，网关占用服务器的 80 端口。

> 已部署过？无需重装。服务器重启后看[启动与检查](#4-启动与检查)；登录态失效时看[更新元宝 Cookie](#3-更新元宝-cookie)。

## 1. 构建解析程序（构建机）

先检出本仓库，在**仓库外**选构建目录，并把 `repo` 改为仓库的绝对路径：

```sh
repo=/absolute/path/to/wx-video-account-notes
cd /path/to/build-directory
git clone https://github.com/ltaoo/wx_channels_download.git
cd wx_channels_download
git checkout 124f044235bc706fe796c043a14ff442a150ae5d
git apply "$repo/server/upstream-yuanbao.patch"
mkdir -p cmd/notes-resolver
cp "$repo/server/upstream_main.go" cmd/notes-resolver/main.go
cp "$repo/server/upstream-tests/notes_yuanbao_test.go" pkg/scraper/wxchannels/notes_yuanbao_test.go
go test -mod=mod ./pkg/scraper/wxchannels -run TestNotesRejectsUnusableYuanbaoResponses -count=1
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -mod=mod -trimpath -o resolver-linux-amd64 ./cmd/notes-resolver
```

生成的 `resolver-linux-amd64` 用于部署。构建可能改动上游仓库的 `go.mod`；不要把这些改动带回本仓库。

## 2. 上传并安装

仍在构建机执行，把 `your-server` 换成自己的 SSH 地址（下例假设可以 root 登录）：

```sh
ssh root@your-server 'install -d -m 0700 /root/projects/wx-video-account-notes'
scp resolver-linux-amd64 "$repo/server/gateway.py" "$repo/server/update_cookie.py" "$repo/server/install.sh" root@your-server:/root/projects/wx-video-account-notes/
ssh root@your-server
```

以下命令在服务器执行。新部署时生成自己的随机访问凭证：

```sh
cd /root/projects/wx-video-account-notes
umask 077
python3 -c 'import json,secrets; print(json.dumps({"access_key":secrets.token_urlsafe(32)}))' > client.json
sh install.sh
```

在可信终端查看 `client.json`，把 `access_key` 安全地保存到客户端；不要使用公开 Skill 自带的默认凭证，也不要把凭证放入仓库或日志。`install.sh` 只准备文件和权限，不创建 Cookie，也不启动服务。已有部署不要重新生成 `client.json`。

## 3. 更新元宝 Cookie

1. 在浏览器打开 [元宝](https://yuanbao.tencent.com/) 并登录。
2. 按 `F12` 打开开发者工具的“网络”，刷新页面；若没有请求，先在页面中操作一次。
3. 找到发往 `yuanbao.tencent.com/api/` 的请求，复制“请求标头”中 `Cookie` **后面的完整值**。
4. 在服务器运行以下命令，按提示粘贴；输入不会回显：

```sh
python3 /root/projects/wx-video-account-notes/update_cookie.py
```

脚本用内置分享链接验证新 Cookie，成功后才写入，失败则保留旧文件。若内置链接已不可用，可先设置 `WX_NOTES_VERIFY_LINK` 为另一条可用分享链接。不要使用可能漏掉 HttpOnly 内容的 `document.cookie`，也不要把 Cookie 放进命令参数、仓库或 issue。

## 4. 启动与检查

先检查旧进程；服务器重启后 PID 文件可能仍在：

```sh
cd /root/projects/wx-video-account-notes
for f in resolver.pid gateway.pid; do if [ -f "$f" ]; then ps -fp "$(cat "$f")"; fi; done
```

确认两个进程均未运行后启动：

```sh
umask 077
nohup ./resolver > resolver.log 2>&1 < /dev/null & echo $! > resolver.pid
nohup python3 gateway.py > gateway.log 2>&1 < /dev/null & echo $! > gateway.pid
ps -fp "$(cat resolver.pid)" "$(cat gateway.pid)"
```

`ps` 应显示两个进程。在服务器检查网关：

```sh
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1/api/channels/parse_sph
```

**预期返回 `401`**：无凭证请求被拒绝，说明网关有响应。实际解析还需按下一节用真实链接测试。公网访问失败时，另查服务器防火墙和云安全组的 80 端口。进程不会随开机自动启动；服务器重启或进程退出后需重新执行本节。更换访问凭证后需重启网关，更新 Cookie 无需重启。

## 5. 配置客户端并验收

在**运行 agent 的电脑**设置两项环境变量，然后从同一环境启动 agent。已打开的桌面应用需要重启，才能继承新环境。

| 变量 | 填写内容 |
| --- | --- |
| `WX_VIDEO_ACCOUNT_RESOLVE_API` | `http://<服务器>/api/channels/parse_sph`，或自己的 HTTPS 入口完整地址 |
| `WX_VIDEO_ACCOUNT_RESOLVE_KEY` | 服务器 `client.json` 中的 `access_key` |

PowerShell：

```powershell
$env:WX_VIDEO_ACCOUNT_RESOLVE_API = 'http://<服务器>/api/channels/parse_sph'
$env:WX_VIDEO_ACCOUNT_RESOLVE_KEY = Read-Host -Prompt '访问凭证' -MaskInput
```

Bash：

```sh
export WX_VIDEO_ACCOUNT_RESOLVE_API='http://<服务器>/api/channels/parse_sph'
read -rsp 'Access key: ' WX_VIDEO_ACCOUNT_RESOLVE_KEY
echo
export WX_VIDEO_ACCOUNT_RESOLVE_KEY
```

把一条可用的视频号分享链接交给 agent。验收时检查媒体文件、`note_materials.json`、OCR/ASR 状态和最终 Markdown 笔记；接口有响应并不代表完整流程成功。两项变量必须同时设置；都取消后恢复默认服务。自部署失败时不会自动改用默认服务，也不要修改 Skill 内的 `resolver_config.json`。

## 常见问题

| 现象或错误码 | 先检查什么 |
| --- | --- |
| 连不上服务器 | 两个进程、80 端口、防火墙和云安全组。 |
| `UNAUTHORIZED` | 客户端凭证是否与 `client.json` 一致。 |
| `LOGIN_REQUIRED` | 服务器是否已通过脚本写入 Cookie。 |
| `LOGIN_EXPIRED_OR_UPSTREAM_CHANGED` | 元宝登录态或接口可能变化；重新运行 Cookie 更新脚本验证。 |
| `FEED_UNAVAILABLE_OR_UPSTREAM_CHANGED` | 换一条可用分享链接重试，再排查上游接口。 |
| `RESOLVER_UNAVAILABLE` | 回环解析进程及同目录的 `resolver.log`、`gateway.log`。 |
| `RATE_LIMITED` | 等待一分钟再试；网关对所有客户端合计每分钟最多处理 30 次请求。 |

公网 HTTP 会明文传输分享链接、访问凭证和解析结果。需要保密传输时，在网关前配置只转发解析路由的 HTTPS 入口。服务器目录仅允许 root 访问，Cookie 文件权限为 `0600`；不要公开 Cookie、访问凭证、完整媒体地址或原始响应。

实现细节：服务使用固定版本的 [`ltaoo/wx_channels_download`](https://github.com/ltaoo/wx_channels_download) Go 解析函数。Go 进程监听 `127.0.0.1:17879`；Python 网关监听公网 80 端口，只开放 `GET /api/channels/parse_sph?url=...`。如需停止服务，先用上面的 `ps` 核对 PID，再执行 `kill "$(cat gateway.pid)" "$(cat resolver.pid)"` 并删除两个 PID 文件。
