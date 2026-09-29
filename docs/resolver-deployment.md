# 解析服务部署与维护

所有用户安装 Skill 后默认使用项目维护者的解析服务，无需部署服务器。本页也说明如何在自己的 Linux x64 服务器部署同一解析服务；选择自部署后，客户端只请求自己的服务。无论选择哪种方式，服务器只解析分享链接，媒体下载、OCR、ASR 和笔记生成仍在用户本机完成。

本部署复用上游 [`ltaoo/wx_channels_download`](https://github.com/ltaoo/wx_channels_download) 的 Go 解析函数，固定提交为 `124f044235bc706fe796c043a14ff442a150ae5d`。回环解析进程监听 `127.0.0.1:17879`；Python 网关在公网 HTTP 80 端口只开放 `GET /api/channels/parse_sph?url=...`，校验访问凭证并限制为每分钟 30 次请求。其他上游管理路由不对外开放。两个进程由服务器维护者手动启动；服务器重启或进程退出后须手动再次启动。

公网 HTTP 明文传输分享链接、访问凭证和解析响应。默认服务的共用凭证随公开 Skill 分发，只能限制误调用，不能充当秘密。自部署者应使用自己的访问凭证和元宝 Cookie，不复用默认服务的凭证。部署文件、运行程序、网关配置、Cookie、PID 文件和日志集中在 `/root/projects/wx-video-account-notes/`；当前脚本固定此目录，并以 root 运行。目录仅允许 root 访问，Cookie 权限为 `0600`；日志不记录请求行或上游解析日志。需要传输保密时，请自行在网关前配置只转发解析路由的 HTTPS 入口。

## 构建与安装

构建机需要 Git 和 Go，目标服务器需要 Linux x64 和 Python 3。先检出本仓库，把 `repo` 设为其绝对路径，再从固定上游提交构建：

```sh
repo=/absolute/path/to/wx-video-account-notes
git clone https://github.com/ltaoo/wx_channels_download.git
cd wx_channels_download
git checkout 124f044235bc706fe796c043a14ff442a150ae5d
git apply "$repo/server/upstream-yuanbao.patch"
mkdir -p cmd/notes-resolver
cp "$repo/server/upstream_main.go" cmd/notes-resolver/main.go
cp "$repo/server/upstream-tests/notes_yuanbao_test.go" pkg/scraper/wxchannels/notes_yuanbao_test.go
```

补丁令上游元宝响应在 HTTP/业务码异常或缺少必要字段时停止，避免误报成媒体不可用。然后在上游目录运行：

```sh
go test -mod=mod ./pkg/scraper/wxchannels -run TestNotesRejectsUnusableYuanbaoResponses -count=1
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -mod=mod -trimpath -o resolver-linux-amd64 ./cmd/notes-resolver
```

构建时上游 `go.mod` 可能被 Go 更新；只把生成的二进制用于部署，不把这些更新带回本仓库。以 root 在自己的服务器执行 `install -d -m 0700 /root/projects/wx-video-account-notes`，再把二进制与本仓库 `server/` 下的 `gateway.py`、`update_cookie.py` 和 `install.sh` 放入该目录。先运行 `umask 077`，再创建自己的 `client.json`，内容为 `{"access_key":"<自己生成的随机凭证>"}`；不要复制公开 Skill 的默认凭证。妥善保存此凭证，后续在客户端配置相同值。以 root 在该目录运行 `sh install.sh`，准备程序及文件权限；它不会创建或覆盖 Cookie，也不会启动进程。维护者现有服务器继续使用原有配置，无需重装。

以 root 手动启动，并把 PID 与日志保留在项目目录：

```sh
cd /root/projects/wx-video-account-notes
umask 077
nohup ./resolver > resolver.log 2>&1 < /dev/null & echo $! > resolver.pid
nohup python3 gateway.py > gateway.log 2>&1 < /dev/null & echo $! > gateway.pid
ps -fp "$(cat resolver.pid)" "$(cat gateway.pid)"
```

停止前先用上述 `ps` 命令核对 PID 对应的程序，再运行 `kill "$(cat gateway.pid)" "$(cat resolver.pid)"` 并删除两个 `.pid` 文件。没有 Cookie 时应返回 `LOGIN_REQUIRED`，错误凭证应返回 `UNAUTHORIZED`；先确认这两个状态，再更新 Cookie。公网端口的云安全组开放情况须单独检查。更换 `client.json` 中的访问凭证后，需要重启网关进程。

## 自部署客户端配置

在启动 agent 前，同时设置以下环境变量；桌面应用须继承新环境，已打开的应用需要重启：

| 变量 | 值 |
| --- | --- |
| `WX_VIDEO_ACCOUNT_RESOLVE_API` | `http://<自己的服务器>/api/channels/parse_sph`，或自己的 HTTPS 入口完整地址 |
| `WX_VIDEO_ACCOUNT_RESOLVE_KEY` | 与自有服务器 `client.json` 中 `access_key` 相同的凭证 |

在 PowerShell 中：

```powershell
$env:WX_VIDEO_ACCOUNT_RESOLVE_API = 'http://<自己的服务器>/api/channels/parse_sph'
$env:WX_VIDEO_ACCOUNT_RESOLVE_KEY = Read-Host -Prompt '访问凭证' -MaskInput
```

在 Bash 中：

```sh
export WX_VIDEO_ACCOUNT_RESOLVE_API='http://<自己的服务器>/api/channels/parse_sph'
read -rsp 'Access key: ' WX_VIDEO_ACCOUNT_RESOLVE_KEY
echo
export WX_VIDEO_ACCOUNT_RESOLVE_KEY
```

从设置变量的环境启动 agent，避免把凭证写入命令历史。两项必须同时设置；只设置其中一项会在发送请求前报错。取消两项设置后恢复默认服务，不要编辑或提交 Skill 自带的 `resolver_config.json`。自部署服务失败时不会自动请求维护者的服务。

## 更新元宝 Cookie

服务器维护者在 Chrome/Edge 打开 `https://yuanbao.tencent.com/` 并登录，按 `F12` 打开“网络”，刷新页面，在发往 `yuanbao.tencent.com/api/` 的请求的“请求标头”中复制 `Cookie` 后的完整值。若未出现 API 请求，先在页面中进行一次操作。不要使用可能遗漏 HttpOnly Cookie 的 `document.cookie`，也不要复制或运行含凭证的 cURL 命令。然后 SSH 登录自己的服务器。推荐运行：

```sh
python3 /root/projects/wx-video-account-notes/update_cookie.py
```

脚本在终端无回显读取 Cookie，使用内置分享链接验证，无需再输入链接。候选 Cookie 先在独立进程中完成真实解析验证；验证失败时退出非零并保留旧文件，成功时以原子替换写入 `0600` 文件。不要把 Cookie 作为命令参数、粘贴到 issue、日志或仓库中。若默认验证链接已不可用，可在运行脚本前设置 `WX_NOTES_VERIFY_LINK` 为另一条可用链接。

也可以以 root 直接编辑文件：

```sh
nano /root/projects/wx-video-account-notes/cookie
chmod 0600 /root/projects/wx-video-account-notes/cookie
```

文件内容只写请求标头中 `Cookie` 后面的值，不带 `Cookie:` 前缀；保存后用一条可用分享链接验证解析。解析程序每次请求都会重新读取该文件，无需重启。直接编辑不会预先验证新值，也不保证写入期间读到的是完整旧值或新值；需要保留旧值并在验证成功后切换时，使用上面的脚本。不要把 Cookie 放进 shell 命令或命令历史。

## 验收与故障定位

从客户端经所选解析接口运行 Skill。确认媒体、`note_materials.json`、OCR/ASR 处理状态及最终 Markdown 笔记；服务器单独解析成功不算完成。记录只写日期、平台、HTTP/业务状态、产物存在性和错误类别，不写 Cookie、访问凭证、完整媒体地址或原始响应。

- `UNAUTHORIZED`：客户端凭证与所选服务器配置不一致。
- `LOGIN_REQUIRED`：服务器缺少 Cookie 文件。
- `LOGIN_EXPIRED_OR_UPSTREAM_CHANGED`：元宝登录态可能失效或上游接口变化；所选服务的维护者先用交互脚本验证并更新。
- `FEED_UNAVAILABLE_OR_UPSTREAM_CHANGED`：媒体动态不可用或上游详情接口变化；先换一条可用链接排查。
- `RESOLVER_UNAVAILABLE`：回环解析进程不可用；检查两个 PID 对应的进程及同目录日志。
