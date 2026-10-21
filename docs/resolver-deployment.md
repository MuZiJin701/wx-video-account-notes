# 自部署指南

按下面 4 步部署：安装程序 → 微信扫码 → 启动服务 → 连接客户端。

服务器只负责解析视频号分享链接。下载媒体、OCR、ASR 和生成笔记仍在运行 agent 的电脑上完成。

## 部署前准备

- 一台 Linux x64 服务器，使用 systemd 管理服务，能联网下载依赖。
- 用 root 账号通过 SSH 登录，确认已有 Git、Python 3（`/usr/bin/python3`）、curl 和 tar。
- 确认 80 端口没有被其他程序占用，并在云服务器安全组和防火墙中允许客户端访问。内部解析端口 17879 不需要对外开放。

下面第 1～3 步的命令都在服务器上执行。安装目录固定为 `/root/projects/wx-video-account-notes`。

## 1. 安装程序

首次安装时运行；已有部署请看文末的“更新程序”。

```sh
mkdir -p /root/projects
git clone --branch main https://github.com/MuZiJin701/wx-video-account-notes.git /root/projects/wx-video-account-notes
cd /root/projects/wx-video-account-notes
sh server/install.sh
```

安装脚本会下载项目使用的 Python、Playwright 和 Chromium，并安装所需的系统库，首次运行可能较慢。安装完成后会生成 `config.json` 和服务配置，但还不会启动服务或登录元宝。

`config.json` 中的 `access_key` 会自动生成，稍后填写到客户端；`verify_link` 是用来检查 Cookie 的视频号分享链接，通常先保留默认值。

## 2. 微信扫码获取 Cookie

在同一个 SSH 终端运行：

```sh
.runtime/server/.venv/bin/python maintain_cookie.py
```

阅读协议提示后输入 `yes`，用微信扫描终端二维码，并在手机上确认。若提示确认注册，请按提示决定是否继续；扫码可能创建新的元宝账号。

看到以下任一结果即可继续：

- `COOKIE_UPDATED`：扫码成功，新 Cookie 已通过解析检查并保存。
- `COOKIE_REUSED`：原 Cookie 仍然有效，无需扫码。

二维码最多等待 3 分钟。终端显示不完整时先拉宽窗口；也可在命令结束前查看提示中的临时图片。超时、取消、额外验证或检查失败会退出，保留原 Cookie；处理后重新运行即可。

扫码无法完成时，可以使用下面的“手动更新 Cookie”。

## 3. 启动服务并检查

```sh
systemctl enable --now wx-notes-resolver wx-notes-gateway
systemctl status wx-notes-resolver wx-notes-gateway --no-pager
```

两个服务都显示 `active (running)`，说明已启动，也会在开机时自动启动。接着完成第 4 步，用一条真实分享链接确认解析可用，无需先运行开发测试。

启动失败时查看最近日志：

```sh
journalctl -u wx-notes-resolver -u wx-notes-gateway -n 50 --no-pager
```

## 4. 连接客户端

在服务器查看配置，找到 `access_key`：

```sh
cat config.json
```

在**运行 agent 的电脑**上，备份并编辑实际安装的 Skill 中的 `runtime/resolver_config.json`：

```json
{
  "api_url": "http://你的服务器IP/api/channels/parse_sph",
  "access_key": "填写服务器config.json中的access_key"
}
```

修改安装副本中的文件；只改源码仓库不会影响已经安装的 Skill。若设置过 `WX_VIDEO_ACCOUNT_RESOLVE_API` 和 `WX_VIDEO_ACCOUNT_RESOLVE_KEY`，它们会覆盖文件配置，须同时更新或同时取消。更新、重装 Skill 前也请备份这份配置。

给 agent 一条真实的视频号分享链接，确认能下载内容并生成笔记，部署就完成了。自部署失败时不会自动切换到默认服务。

HTTP 会明文传输访问凭证、分享链接和结果；需要加密时，请通过 HTTPS 反向代理访问网关。元宝 Cookie 和服务器配置不要提交到 Git 或贴到公开日志。

## 日常维护

### Cookie 失效后重新扫码

本方案没有定时登录或邮件通知。解析提示登录失效时，在服务器运行：

```sh
cd /root/projects/wx-video-account-notes
.runtime/server/.venv/bin/python maintain_cookie.py
```

更新 Cookie 后不用重启服务。网络故障或登录状态不明时，程序不会直接重登；请先检查网络和 `config.json` 中的 `verify_link` 是否仍然有效。

### 手动更新 Cookie

在正常浏览器中登录元宝，打开开发者工具的“网络”，从发往元宝 API 的请求头中复制完整 `Cookie` 值。不要使用 `document.cookie`，它可能缺少必要凭证。

回到服务器运行，按提示粘贴（输入不回显）：

```sh
cd /root/projects/wx-video-account-notes
python3 update_cookie.py
```

看到“Cookie 已更新；解析验证通过”即成功。此方式同样先检查再替换，失败保留原文件。

### 更新程序

先备份 `config.json`、`cookie` 和 `.runtime/`，保留自己的源码修改，再运行：

```sh
cd /root/projects/wx-video-account-notes
git pull --ff-only
sh server/install.sh
systemctl restart wx-notes-resolver wx-notes-gateway
```

若 Git 提示有本地修改或分支分歧，先处理提示，不要强制覆盖。安装脚本保留访问凭证和 Cookie；从旧版升级时，会停用旧 Cookie 定时任务，移除活动配置中的 QQ 密码和维护周期，不再使用旧浏览器资料。

### 停止服务

```sh
systemctl stop wx-notes-gateway wx-notes-resolver
```

如需同时取消开机启动，运行 `systemctl disable wx-notes-gateway wx-notes-resolver`。恢复时重新执行第 3 步的启动命令。

## 遇到问题

| 情况 | 先这样处理 |
| --- | --- |
| 终端太窄、字符乱码 | 拉宽窗口、使用支持 UTF-8 的 SSH 终端后重试。 |
| 扫码超时或取消 | 重新运行维护命令，再次扫码。 |
| 要求额外验证，或网页流程发生变化 | 在正常网页处理，或改用手动更新 Cookie。程序不会自动解验证码。 |
| 提示 `LOGIN_TERMS_CHANGED` | 网页协议已变化，需要先核对并更新程序中的协议链接。 |
| 提示已有维护命令运行 | 等前一条命令退出，不要同时运行多个维护命令。 |
| Cookie 检查失败、网络或上游不可用 | 检查服务器网络，并将 `verify_link` 换成有效分享链接；不要只凭解析失败判断 Cookie 过期。 |
| 本机能访问，客户端连不上 | 检查服务器 IP、安全组、防火墙、80 端口及客户端访问凭证。 |

需要开发测试时，再看[独立扫码检查与完整验收清单](../plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md#standalone-wechat-login-check)。方案依据和已知限制见 [ADR 0005](adr/0005-manual-wechat-cookie-maintenance.md) 与[扫码验收记录](research/yuanbao-manual-qr-login.md)。
