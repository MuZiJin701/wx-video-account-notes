# 自部署指南

自部署采用 **手动检查 Cookie + Playwright/Chromium 微信扫码登录**，同时保留原有的无回显手动 Cookie 更新入口。QQ 账号密码登录、QQ 邮箱通知和定时维护已移除。维护者按需 SSH 到服务器运行命令；Playwright 启动临时无头 Chromium，命令结束后退出，不持续监控，也不连接常驻浏览器的远程调试端口。设计见 [ADR 0005](adr/0005-manual-wechat-cookie-maintenance.md)，实验见[扫码记录](research/yuanbao-manual-qr-login.md)。

服务器只解析视频号分享链接；媒体下载、OCR、ASR 和笔记仍在客户端完成。普通使用无需自部署，见 [README](../README.md)。

支持 Linux x64 + systemd。准备 Git、`/usr/bin/python3`、curl、tar 和可用网络，以 root 安装到固定目录 `/root/projects/wx-video-account-notes`。选择 Playwright 支持的 Linux 发行版。网关默认监听 80 端口；Go 解析器的 17879 端口仅监听回环。

## 0. 独立检查

在独立检出目录准备锁定的服务端运行环境，不安装项目服务：

```sh
git clone --branch main --single-branch \
  https://github.com/MuZiJin701/wx-video-account-notes.git ~/wx-notes-branch-check
cd ~/wx-notes-branch-check
uv_command=$(sh plugins/wx-video-account-notes/skills/wx-video-account-notes/scripts/ensure_uv.sh)
export UV_PROJECT_ENVIRONMENT="$PWD/.runtime/server/.venv"
export UV_PYTHON_INSTALL_DIR="$PWD/.runtime/server/python"
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.runtime/server/browsers"
"$uv_command" sync --locked --project server --python 3.13.14
"$UV_PROJECT_ENVIRONMENT/bin/python" -m unittest discover -s server
"$UV_PROJECT_ENVIRONMENT/bin/python" -m playwright install --with-deps --no-shell chromium
"$UV_PROJECT_ENVIRONMENT/bin/python" server/smoke_browser.py
```

预期单测全部通过，浏览器检查输出 `BROWSER_SMOKE_OK`。`--with-deps` 会通过系统包管理器安装 Chromium 所需 Linux 库，需要 root 或 sudo 权限。检查本身不登录账号。

独立验收真实扫码与解析时，在交互式 SSH 终端执行：

```sh
umask 077
mkdir -p .runtime/server
if [ ! -e .runtime/server/login-check.json ]; then
  cp server/config.example.json .runtime/server/login-check.json
fi
chmod 600 .runtime/server/login-check.json
```

用编辑器填写 `access_key` 为 `login-check-only`，并确认 `verify_link` 是有效视频号分享链接；无需 QQ 账号或密码。继续运行：

```sh
.runtime/server/.venv/bin/python server/check_login.py \
  --config .runtime/server/login-check.json
```

确认协议后显示微信二维码。依次输出 `YUANBAO_LOGIN_OK`、`YUANBAO_PARSE_OK` 才表示登录与完整解析均通过。此入口只检查新会话，不发布 Cookie；退出后删除临时状态。历史 `yuanbao` / `mail` 密码检查参数已移除。

## 1. 安装与升级

以下克隆只用于固定目录尚不存在的新部署：

```sh
umask 077
mkdir -p /root/projects
git clone --branch main --single-branch \
  https://github.com/MuZiJin701/wx-video-account-notes.git /root/projects/wx-video-account-notes
cd /root/projects/wx-video-account-notes
sh server/install.sh
```

安装会创建私有 `config.json`，自动生成空缺的 `access_key`，默认使用示例验证链接：

```json
{
  "access_key": "",
  "verify_link": "https://weixin.qq.com/sph/AHhuzPE3Pi"
}
```

`access_key` 是客户端访问凭证；已有值保留。验证链接失效时，用编辑器更换 `verify_link`。配置、Cookie 和浏览器资料不应提交到 Git、发送给他人或粘贴到公开日志。

安装器准备项目私有 Python 3.13.14、锁定的 Playwright 和配套 Chromium，以及网关、解析器和手动维护命令；不会扫码、检查 Cookie 或启动对外服务。

已有部署先保留 `config.json`、`cookie`、`.runtime/` 和源码修改，在固定部署目录更新源码后重新运行 `sh server/install.sh`。升级会停用并移除旧 `wx-notes-cookie.timer` / `wx-notes-cookie.service`，从活动配置移除 `qq` 和 `cookie_check_interval_hours`，保留访问凭证和 Cookie。旧 `client.json` 的访问凭证可迁入新配置，原文件保留。旧浏览器资料和历史维护状态不再使用，也不会批量删除。

## 2. 手动检查与微信扫码更新

在服务器交互式 SSH 终端运行：

```sh
cd /root/projects/wx-video-account-notes
.runtime/server/.venv/bin/python maintain_cookie.py
```

- 已有 Cookie 通过完整解析检查：输出 `COOKIE_REUSED`，不启动浏览器、不改文件。
- Cookie 缺失，或解析失败且登录状态明确失效：显示服务/隐私协议链接。输入 `yes` 后启动无头 Chromium，展示微信二维码。
- 网络或上游异常、登录状态不明，或登录有效但解析失败：保留原 Cookie 并退出，不直接重登。
- 扫码后确认元宝登录成功，并用新 Cookie 完成解析检查；通过后以 `0600` 权限原子替换，输出 `COOKIE_UPDATED`，无需重启解析器。

终端需支持 UTF-8、ANSI 颜色和 Unicode 半格字符，宽度至少容纳二维码（当前样本约 55 列）。使用微信扫描终端中的黑白二维码并在手机确认。程序同时显示临时图片路径，供辅助查看，命令退出后删除。终端过窄或无法输出字符时会失败，可调整终端后重跑。

扫码可能创建元宝账号，且可能不同于旧 QQ 登录账号；不绑定或迁移旧账号。若网页出现已识别的“同意并注册/登录”按钮，终端会再次要求确认；可选手机号绑定只点击“跳过，直接登录”。其他注册/绑定页面不保证支持，应在正常网页完成后重试。

扫码等待最多 3 分钟；发现二维码过期时使用网页刷新控件，期限不延长。超时、拒绝协议、手机取消、Ctrl+C、额外图形验证或候选 Cookie 校验失败均退出，旧 Cookie 保留。确认协议最多等待 3 分钟，解析验证另有超时；整个命令可能超过 3 分钟。使用文件锁避免维护命令并发；非交互终端不能发起扫码。

没有定时检查、后台登录、邮件通知或短信后备。请按需要手动运行；`--resume` 已移除。腾讯未来也可能要求额外验证，此流程不保证永久免验证。

## 3. 启动、恢复与停止

首次 Cookie 维护成功后启动网关与解析器：

```sh
systemctl enable --now wx-notes-resolver wx-notes-gateway
systemctl status wx-notes-resolver wx-notes-gateway
curl -i http://127.0.0.1/api/channels/parse_sph
```

未认证请求预期返回 `401`。升级后重启这两个服务；日常更新 Cookie 无需重启。日志：

```sh
journalctl -u wx-notes-resolver -u wx-notes-gateway -n 50
```

扫码不能完成时，仍可在正常元宝网页登录，从开发者工具的元宝 API 请求复制完整 Cookie，在服务器无回显输入：

```sh
python3 /root/projects/wx-video-account-notes/update_cookie.py
```

不要使用可能缺少 HttpOnly 凭证的 `document.cookie`。手动粘贴入口同样先验证后替换，失败保留原文件；可用 `WX_NOTES_VERIFY_LINK` 临时覆盖验证链接。

| 错误码 | 处理 |
| --- | --- |
| `COOKIE_OR_UPSTREAM_UNAVAILABLE` | 检查网络、验证链接和元宝接口；不能仅凭解析失败认定登录过期。 |
| `NEW_COOKIE_VALIDATION_FAILED` | 新 Cookie 未通过完整解析检查；旧文件保留。 |
| `INTERACTIVE_TERMINAL_REQUIRED` | 直接在交互式 SSH 终端运行，不通过定时任务或管道扫码。 |
| `TERMINAL_TOO_NARROW` / `TERMINAL_UTF8_REQUIRED` | 增大终端宽度或配置 UTF-8 后重跑。 |
| `LOGIN_CONFIRM_TIMEOUT` / `WECHAT_SCAN_TIMEOUT` / `LOGIN_CANCELLED` | 本次已退出，需要时重新运行。 |
| `LOGIN_ADDITIONAL_VERIFICATION_REQUIRED` | 在正常网页处理额外验证，或使用手动 Cookie 入口。 |
| `WECHAT_LOGIN_FLOW_FAILED` / `WECHAT_QR_EXPIRED` | 网页、二维码或网络有变化；先排查，再手动重跑。 |
| `LOGIN_TERMS_CHANGED` | 网页协议链接已变化；核对并更新协议展示后重试，不沿用旧确认。 |
| `MAINTENANCE_ALREADY_RUNNING` | 另一维护命令仍在运行，不同时启动。 |
| `CONFIG_OR_RUNTIME_INVALID` | 检查私有配置、运行目录、权限和 Python 环境。 |
| `LOGIN_REQUIRED` / `LOGIN_EXPIRED_OR_UPSTREAM_CHANGED` | 手动检查 Cookie，并检查上游；没有自动恢复。 |

停止服务：

```sh
systemctl stop wx-notes-gateway wx-notes-resolver
```

如也不需要开机启动，运行 `systemctl disable wx-notes-gateway wx-notes-resolver`；恢复时重新 `enable --now`。本方案不需要 Cookie 定时任务。

## 4. 客户端连接

仅查看访问凭证：

```sh
python3 -c 'import json; print(json.load(open("/root/projects/wx-video-account-notes/config.json"))["access_key"])'
```

在运行 agent 的电脑，备份并编辑实际安装 Skill 的 `runtime/resolver_config.json`：

```json
{
  "api_url": "http://<服务器>/api/channels/parse_sph",
  "access_key": "服务器config.json中的access_key"
}
```

插件安装副本与源码仓库相互独立；更新或重装前备份客户端配置。`WX_VIDEO_ACCOUNT_RESOLVE_API` 和 `WX_VIDEO_ACCOUNT_RESOLVE_KEY` 仍须成对设置，并优先于客户端文件。交给 agent 一条真实分享链接，确认生成媒体、`note_materials.json` 和笔记。自部署失败不会自动切换到默认服务。

HTTP 会明文传输链接、访问凭证和结果；需要加密时为网关配置 HTTPS。完整功能与模型检查见[手动验收清单](../plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md)。[GitHub Actions](../.github/workflows/tests.yml) 只使用离线单测和无凭据浏览器检查，真实账号扫码及远程服务生命周期需单独验收。
