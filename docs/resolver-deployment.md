# 自部署解析服务

普通使用无需服务器，见 [README](../README.md)。自部署只解析分享链接，下载、OCR、ASR 和笔记仍在客户端完成。

要求：使用 systemd 的 Linux x64 服务器、Git、`/usr/bin/python3`、curl 和 root shell。固定目录为 `/root/projects/wx-video-account-notes/`；Go 解析进程监听 `127.0.0.1:17879`，Python 网关占用公网 80 端口。仓库已包含解析二进制，无需自行构建。

## 1. 克隆并安装（服务器）

以下命令在**服务器的 root shell** 中执行：

```sh
umask 077
mkdir -p /root/projects
git clone https://github.com/MuZiJin701/wx-video-account-notes.git /root/projects/wx-video-account-notes
cd /root/projects/wx-video-account-notes
```

仅在没有凭证文件时生成随机凭证，然后安装：

```sh
if [ ! -e client.json ]; then
  python3 -c 'import json,secrets; print(json.dumps({"access_key":secrets.token_urlsafe(32)}))' > client.json
fi
sh server/install.sh
```

将 `client.json` 中的 `access_key` 安全保存到客户端，不使用公开 Skill 的共用凭证。安装脚本复制程序、安装两个 systemd 服务并执行 `daemon-reload`，不创建 Cookie，也不自动启动或启用服务。**已有部署保留 `client.json` 和 `cookie`**；更新仓库后只重新运行安装脚本，再按下文重启，不要重新生成凭证。

## 2. 更新元宝 Cookie

1. 在浏览器打开 [元宝](https://yuanbao.tencent.com/) 并登录。
2. 按 `F12` 打开开发者工具的“网络”，刷新页面；若没有请求，先在页面中操作一次。
3. 找到发往 `yuanbao.tencent.com/api/` 的请求，复制“请求标头”中 `Cookie` **后面的完整值**。
4. 在服务器运行以下命令，按提示粘贴；输入不会回显：

```sh
python3 /root/projects/wx-video-account-notes/update_cookie.py
```

脚本用内置分享链接验证新 Cookie，成功后才写入，失败则保留旧文件。若内置链接已不可用，可先设置 `WX_NOTES_VERIFY_LINK` 为另一条可用分享链接。不要使用可能漏掉 HttpOnly 内容的 `document.cookie`，也不要把 Cookie 放进命令参数、仓库或 issue。

## 3. 启动、停止与恢复

以下命令在服务器执行。完成 Cookie 配置后，**启动并启用开机启动**：

```sh
systemctl enable --now wx-notes-resolver.service wx-notes-gateway.service
systemctl status wx-notes-resolver.service wx-notes-gateway.service --no-pager
```

**停止**（保留开机启动设置）：

```sh
systemctl stop wx-notes-gateway.service wx-notes-resolver.service
```

手动停止不会触发自动重启。若重启服务器后也要保持停用，执行 `systemctl disable --now wx-notes-gateway.service wx-notes-resolver.service`。

**停止后恢复运行**：

```sh
systemctl start wx-notes-resolver.service wx-notes-gateway.service
```

若曾禁用开机启动，改用 `enable --now`。两个进程异常退出后会间隔 5 秒自动重启；这不修复 Cookie 失效、上游接口变化或仍存活但卡住的进程。

**故障恢复或更新程序/凭证后重启**：

```sh
systemctl status wx-notes-resolver.service wx-notes-gateway.service --no-pager
journalctl -u wx-notes-resolver.service -u wx-notes-gateway.service -n 50 --no-pager
# 修复问题后，清除失败/启动限流状态并重启
systemctl reset-failed wx-notes-resolver.service wx-notes-gateway.service
systemctl restart wx-notes-resolver.service wx-notes-gateway.service
systemctl status wx-notes-resolver.service wx-notes-gateway.service --no-pager
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1/api/channels/parse_sph
```

两项状态应为 `active (running)`；无凭证探测预期返回 **401**，只证明网关有响应，完整验收见下一节。修改服务文件后先执行 `systemctl daemon-reload`；更换 `client.json` 凭证需重启网关，更新 Cookie 无需重启。公网访问失败时检查防火墙和云安全组的 80 端口。

## 4. 配置客户端并验收

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
| 连不上服务器 | 两个服务状态、端口占用、防火墙和云安全组。 |
| `UNAUTHORIZED` | 客户端凭证是否与 `client.json` 一致。 |
| `LOGIN_REQUIRED` | 服务器是否已通过脚本写入 Cookie。 |
| `LOGIN_EXPIRED_OR_UPSTREAM_CHANGED` | 元宝登录态或接口可能变化；重新运行 Cookie 更新脚本验证。 |
| `FEED_UNAVAILABLE_OR_UPSTREAM_CHANGED` | 换一条可用分享链接重试，再排查上游接口。 |
| `RESOLVER_UNAVAILABLE` | 回环解析服务和 journal 日志。 |
| `RATE_LIMITED` | 等待一分钟再试；网关对所有客户端合计每分钟最多处理 30 次请求。 |

公网 HTTP 明文传输链接、凭证和结果；保密传输需在网关前配置仅转发解析路由的 HTTPS 入口。项目目录仅 root 可访问，凭证和 Cookie 权限为 `0600`。不要公开 Cookie、访问凭证、带令牌的媒体地址或原始响应。

解析原理见[技术调查](research/wx-channels-upstream.md)，完整验收见[检查清单](../plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md)；管理命令语义见 [systemctl 手册](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)和[服务重启策略](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#Restart=)。
