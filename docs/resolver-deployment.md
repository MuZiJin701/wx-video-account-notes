# 自部署指南

本页教你在自己的服务器上运行解析服务。服务器只解析分享链接，下载、OCR、ASR 和写笔记仍在你的电脑上完成。普通使用无需自部署，见 [README](../README.md)。

准备一台支持 systemd 的 Linux x64 服务器，装好 Git、Python 3（`/usr/bin/python3`）和 curl，用 root 登录。防火墙和云安全组需要开放 80 端口。

## 1. 下载并安装

在**服务器**上依次运行。项目目录固定为 `/root/projects/wx-video-account-notes`，不要改路径。

```sh
umask 077
mkdir -p /root/projects
git clone https://github.com/MuZiJin701/wx-video-account-notes.git /root/projects/wx-video-account-notes
cd /root/projects/wx-video-account-notes
```

创建访问凭证，再安装服务。已有 `client.json` 时会保留原文件。

```sh
if [ ! -e client.json ]; then
  python3 -c 'import json,secrets; print(json.dumps({"access_key":secrets.token_urlsafe(32)}))' > client.json
fi
sh server/install.sh
```

安装完成后服务还没有启动，需要先设置 Cookie。以后更新程序时，保留 `client.json` 和 `cookie`，只需在项目目录重新运行 `sh server/install.sh`，再重启服务。

## 2. 更新元宝 Cookie

1. 在电脑浏览器登录[元宝](https://yuanbao.tencent.com/)。
2. 按 F12，打开“网络”，刷新页面。没有请求时，在页面上操作一次。
3. 找到地址包含 `yuanbao.tencent.com/api/` 的请求，复制“请求标头”里 `Cookie` 后面的完整值。
4. 在服务器运行下面的命令，按提示粘贴 Cookie。输入不显示是正常的。

```sh
python3 /root/projects/wx-video-account-notes/update_cookie.py
```

看到“Cookie 已更新”即可继续。验证失败会保留旧文件；内置测试链接失效时，可设置 `WX_NOTES_VERIFY_LINK` 为另一条有效分享链接后重试。不要用 `document.cookie` 取值，它可能不完整。不要把 Cookie 写进命令参数、仓库或 issue。

## 3. 启动、停止与恢复

下面的命令都在**服务器**上运行。`wx-notes-resolver` 负责解析，`wx-notes-gateway` 提供对外接口。

### 启动并检查

依次启动服务、设置开机启动、查看运行状态：

```sh
systemctl start wx-notes-resolver wx-notes-gateway
systemctl enable wx-notes-resolver wx-notes-gateway
systemctl status wx-notes-resolver wx-notes-gateway
```

两个服务都显示 `active (running)`，说明进程已启动。若进入翻页界面，按 `q` 退出。再检查接口：

```sh
curl -i http://127.0.0.1/api/channels/parse_sph
```

看到 **401** 或 `UNAUTHORIZED` 是正常的，因为这次检查没有提供访问凭证。它只说明接口有响应，实际解析还要按第 4 步测试。

### 停止

```sh
systemctl stop wx-notes-gateway wx-notes-resolver
```

手动停止后会保持停止；如果保留开机启动，服务器重启时仍会启动。要取消开机启动，再运行：

```sh
systemctl disable wx-notes-gateway wx-notes-resolver
```

### 停止后恢复

```sh
systemctl start wx-notes-resolver wx-notes-gateway
```

需要恢复开机启动时，再运行前面的 `systemctl enable` 命令。已设置开机启动的服务，会在服务器重启后自动运行。

### 故障后恢复

先按下方“常见问题”排查。修好问题后，或更新程序、访问凭证后，重启并检查：

```sh
systemctl restart wx-notes-resolver wx-notes-gateway
systemctl status wx-notes-resolver wx-notes-gateway
```

进程异常退出后会等待 5 秒自动重启。但 Cookie 失效、上游接口变化或进程卡住，需要人工处理。更新 Cookie 不用重启；手动修改 `.service` 文件后，先运行 `systemctl daemon-reload` 再重启。

## 4. 在电脑上连接服务

先在服务器查看访问凭证：

```sh
cat /root/projects/wx-video-account-notes/client.json
```

复制 `access_key` 的值，供下面输入。使用自己生成的凭证，不要使用公开 Skill 的共用凭证，也不要把这个文件发给别人。

回到**运行 agent 的电脑**，用文本编辑器打开实际使用的 Skill 目录下的 `runtime/resolver_config.json`。本仓库中的位置是：

```text
plugins/wx-video-account-notes/skills/wx-video-account-notes/runtime/resolver_config.json
```

如果是通过插件或 `skills` 安装的，请修改已安装的那份 Skill，修改源码仓库不会影响另一个安装副本。

先备份原文件，再把两个字段改成自己的地址和凭证：

```json
{
  "api_url": "http://<服务器>/api/channels/parse_sph",
  "access_key": "服务器 client.json 中的 access_key 值"
}
```

把 `<服务器>` 换成公网 IP 或域名；已配置 HTTPS 时填写完整 HTTPS 接口地址。只替换引号内的值，保留 JSON 格式。这样即可完成本机配置，无需终端命令或修改机器的环境变量。

保存后给 agent 发一条真实分享链接，确认生成媒体、`note_materials.json` 和 Markdown 笔记，并查看 OCR/ASR 状态。自部署失败不会自动切换到默认服务；恢复默认服务时，还原备份的配置文件。

配置中含有自己的访问凭证，不要提交或公开。更新或重装 Skill 可能覆盖配置，更新前请备份。如果之前设置过 `WX_VIDEO_ACCOUNT_RESOLVE_API` 和 `WX_VIDEO_ACCOUNT_RESOLVE_KEY`，它们仍会优先覆盖文件配置。

## 常见问题

查看最近 50 条日志（按 `q` 退出）：

```sh
journalctl -u wx-notes-resolver -u wx-notes-gateway -n 50
```

如果提示启动过于频繁，修好问题后先清除失败记录，再按上文重启：

```sh
systemctl reset-failed wx-notes-resolver wx-notes-gateway
```

| 现象或错误码 | 先检查什么 |
| --- | --- |
| 连不上服务器 | 查看两个服务状态，确认防火墙和云安全组已开放 80 端口。 |
| 端口已被占用 | 检查是否有其他程序使用 80 或本机 17879 端口。 |
| `UNAUTHORIZED` | 客户端凭证是否与 `client.json` 一致。 |
| `LOGIN_REQUIRED` | 服务器是否已通过脚本写入 Cookie。 |
| `LOGIN_EXPIRED_OR_UPSTREAM_CHANGED` | 元宝登录态或接口可能变化；重新运行 Cookie 更新脚本验证。 |
| `FEED_UNAVAILABLE_OR_UPSTREAM_CHANGED` | 换一条可用分享链接重试，再排查上游接口。 |
| `RESOLVER_UNAVAILABLE` | 检查解析服务是否运行，查看上面的日志。 |
| `RATE_LIMITED` | 等待一分钟再试；网关对所有客户端合计每分钟最多处理 30 次请求。 |

HTTP 会明文传输链接、凭证和结果。需要加密传输时，请为网关配置 HTTPS，并只转发解析接口。安装脚本会限制目录和凭证文件的访问权限；不要公开 Cookie、访问凭证、带令牌的媒体地址或原始响应。

更多：[解析原理](research/wx-channels-upstream.md) · [完整验收](../plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md) · [systemctl 官方说明](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)。
