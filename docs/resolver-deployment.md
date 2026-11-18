# 自部署指南

按下面 4 步搭建你自己的解析服务器：**安装程序 → 微信扫码登录 → 启动服务 → 连接客户端**。

服务器只负责把视频号分享链接解析成媒体下载地址；下载视频/图片、OCR 识字、语音转写和整理笔记仍在你运行 Agent 的电脑上完成。

## 部署前准备

- 一台 **Linux x64** 服务器（支持 `systemd`），可以访问公网下载依赖。
- 以 `root` 用户通过 SSH 登录，服务器上已安装 `git`、`python3`（`/usr/bin/python3`）、`curl` 和 `tar`。
- 确认 **80 端口**未被占用，并在云服务器安全组与防火墙中放行 80 端口（内部解析端口 `17879` 仅限本机访问，不要对外开放）。

以下第 1～3 步均在服务器上执行，安装目录固定为 `/root/projects/wx-video-account-notes`。

## 1. 安装程序

首次部署运行以下命令：

```sh
mkdir -p /root/projects
git clone --branch main https://github.com/MuZiJin701/wx-video-account-notes.git /root/projects/wx-video-account-notes
cd /root/projects/wx-video-account-notes
sh server/install.sh
```

脚本会自动准备服务端所需的 Python、Playwright 和 Chromium 环境，并生成配置文件 `config.json` 与两个 systemd 服务单元（首次安装可能需要几分钟，此时暂不启动服务也不登录）。

`config.json` 会自动生成一个随机 `access_key`（客户端连接凭证），第 4 步会用到；`verify_link` 用于检测登录态是否有效，初次使用保持默认即可。

## 2. 微信扫码获取 Cookie

在同一个 SSH 终端中运行：

```sh
.runtime/server/.venv/bin/python maintain_cookie.py
```

1. 终端会先显示服务与隐私协议提示，确认后输入 `yes`。
2. 终端会打印二维码，用手机微信扫码并在手机上确认。如果页面提示首次注册元宝账号，按提示确认是否继续。
3. 等待大约几秒，看到下面任一提示即可进入下一步：
   - `COOKIE_UPDATED`：扫码成功，且已用一条测试链接验证通过并保存。
   - `COOKIE_REUSED`：原有 Cookie 仍然有效，无需重新扫码。

> 二维码有效期为 3 分钟。如果终端显示不全或变形，请拉宽 SSH 窗口；扫码遇到困难时，也可改用文末的“手动更新 Cookie”。

## 3. 启动服务并检查

运行以下命令启用开机自启并启动服务：

```sh
systemctl enable --now wx-notes-resolver wx-notes-gateway
systemctl status wx-notes-resolver wx-notes-gateway --no-pager
```

当 `wx-notes-resolver` 和 `wx-notes-gateway` 都显示 `active (running)` 时，说明服务已正常运行。如果启动失败，用下面命令查看报错日志：

```sh
journalctl -u wx-notes-resolver -u wx-notes-gateway -n 50 --no-pager
```

## 4. 连接客户端

先在服务器上查看自动生成的 `access_key`：

```sh
cat config.json
```

接着回到**运行 Agent 的电脑**，将 Skill 指向你的服务器（推荐直接修改配置文件，也可用环境变量覆盖）。

### 首选方式：修改已安装 Skill 的 `runtime/resolver_config.json`

找到你电脑上实际安装的 `wx-video-account-notes` 目录下的 `runtime/resolver_config.json`（修改仓库源码不会对已安装的插件生效）：

| 安装方式 | 常见配置文件路径 |
| --- | --- |
| `skills` CLI 全局安装 | `~/.agents/skills/wx-video-account-notes/runtime/resolver_config.json` |
| Antigravity 插件安装 | `~/.gemini/config/plugins/wx-video-account-notes/skills/wx-video-account-notes/runtime/resolver_config.json` |
| Codex 插件安装 | `~/.codex/plugins/cache/wx-video-account-notes-dev/wx-video-account-notes/<版本号>/skills/wx-video-account-notes/runtime/resolver_config.json` |
| Claude Code 插件安装 | `~/.claude/plugins/` 下对应插件目录中的 `skills/wx-video-account-notes/runtime/resolver_config.json` |
| Grok Build / Copilot CLI | 各自插件安装目录中的 `skills/wx-video-account-notes/runtime/resolver_config.json` |

先备份原文件，再将内容改为你自己的服务器地址和凭证：

```json
{
  "api_url": "http://你的服务器IP/api/channels/parse_sph",
  "access_key": "填写服务器 config.json 中的 access_key"
}
```

> 以后更新或重装 Skill / 插件时，安装目录可能会被新文件覆盖；更新前请记得备份此文件，更新后再重新填入。

### 备选方式：设置环境变量

如果不想在每次更新插件后重新修改文件，也可以在你本机或启动 Agent 的环境中同时配置以下两个环境变量（会优先覆盖 `resolver_config.json` 中的设置，必须成对配置）：

- `WX_VIDEO_ACCOUNT_RESOLVE_API`：`http://你的服务器IP/api/channels/parse_sph`
- `WX_VIDEO_ACCOUNT_RESOLVE_KEY`：服务器 `config.json` 中的 `access_key`

配置完成后，给 Agent 发送一条真实的视频号分享链接测试：能正常下载并生成笔记即部署完成。

> **安全提示**：自部署失败时**不会**悄悄切回默认公网服务。如果通过 HTTP 访问，凭证、链接和解析结果会明文传输；建议生产使用时在前面配置 HTTPS 反向代理。切勿把 `cookie` 或 `config.json` 提交到 Git。

## 日常维护

### Cookie 失效后重新扫码

服务端没有定时自动登录或邮件提醒。当客户端提示“登录态失效”时，SSH 登录服务器运行：

```sh
cd /root/projects/wx-video-account-notes
.runtime/server/.venv/bin/python maintain_cookie.py
```

更新成功后立即生效，无需重启服务。如果只是网络波动导致检查异常，程序会保留原 Cookie，不会直接触发重新扫码。

### 手动更新 Cookie（扫码不可用时）

1. 在电脑浏览器正常登录元宝网页版，按 `F12` 打开“网络（Network）”面板。
2. 随便触发一次解析或刷新，找到发往元宝接口的请求，从**请求头（Request Headers）**里复制完整的 `Cookie` 字符串（不要使用控制台的 `document.cookie`，它缺少必要凭证）。
3. 回到服务器执行以下命令并按提示粘贴（输入内容不会回显在屏幕上）：

```sh
cd /root/projects/wx-video-account-notes
python3 update_cookie.py
```

看到 `Cookie 已更新；解析验证通过` 即表示成功；如果验证失败，程序会保留原来的 Cookie。

### 更新服务端程序

先备份 `config.json`、`cookie` 和 `.runtime/`，然后运行：

```sh
cd /root/projects/wx-video-account-notes
git pull --ff-only
sh server/install.sh
systemctl restart wx-notes-resolver wx-notes-gateway
```

安装脚本会自动保留原有的 `access_key` 和 `cookie`。

### 停止服务

```sh
systemctl stop wx-notes-gateway wx-notes-resolver
```

如需取消开机自启，运行 `systemctl disable wx-notes-gateway wx-notes-resolver`。恢复时重新执行第 3 步的启动命令即可。

## 遇到问题

| 情况 | 处理方法 |
| --- | --- |
| 终端太窄、二维码变形扫不出来 | 拉宽终端窗口、换用支持 UTF-8 的终端，或改用“手动更新 Cookie”。 |
| 扫码超时或不小心取消 | 重新运行 `maintain_cookie.py` 再扫一次。 |
| 提示额外安全验证或网页流程变化 | 在自己电脑浏览器完成登录后，用“手动更新 Cookie”导入。 |
| 提示 `LOGIN_TERMS_CHANGED` | 元宝协议页面有更新，需先核对并更新程序中的协议链接。 |
| 提示已有维护命令在运行 | 等待前一条 `maintain_cookie.py` 退出后再执行，不要同时开两个。 |
| 服务器本机正常，客户端连不上 | 检查云服务器安全组/防火墙是否放行 80 端口，以及 `api_url` 与 `access_key` 是否填写正确。 |
| 提示 Cookie 检查失败但不确定是否真过期 | 先确认服务器公网正常，并检查 `config.json` 中的 `verify_link` 是否仍然有效。 |

开发调试与完整验收步骤见[独立扫码检查与验收清单](test-cases.md#standalone-wechat-login-check)，技术背景见 [ADR 0005](adr/0005-manual-wechat-cookie-maintenance.md) 与[扫码验收记录](research/yuanbao-manual-qr-login.md)。
