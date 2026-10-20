# 自部署指南

服务器只解析视频号分享链接；媒体下载、OCR、ASR 和笔记仍在客户端完成。普通使用无需自部署，见 [README](../README.md)。

支持 Linux x64 + systemd。准备 Git、`/usr/bin/python3`、curl、tar 和可用网络，以 root 安装到固定目录 `/root/projects/wx-video-account-notes`。选择 Playwright 当前支持的 Linux 发行版，见[系统要求](https://playwright.dev/python/docs/intro#system-requirements)。开放公网 80 端口；解析器的 17879 端口仅监听回环。

## 0. 先验收开发分支

在 Linux x64 的独立目录检查分支代码，避免覆盖已有部署：

```sh
git clone --branch codex/explore-qq-yuanbao-login --single-branch \
  https://github.com/MuZiJin701/wx-video-account-notes.git ~/wx-notes-branch-check
cd ~/wx-notes-branch-check
git rev-parse HEAD
uv_command=$(sh plugins/wx-video-account-notes/skills/wx-video-account-notes/scripts/ensure_uv.sh)
export UV_PROJECT_ENVIRONMENT="$PWD/.runtime/server/.venv"
export UV_PYTHON_INSTALL_DIR="$PWD/.runtime/server/python"
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.runtime/server/browsers"
"$uv_command" sync --locked --project server --python 3.13.14
"$UV_PROJECT_ENVIRONMENT/bin/python" -m unittest discover -s server
"$UV_PROJECT_ENVIRONMENT/bin/python" -m playwright install --with-deps --no-shell chromium
"$UV_PROJECT_ENVIRONMENT/bin/python" server/smoke_browser.py
```

预期单测全部通过、最后输出 `BROWSER_SMOKE_OK`。浏览器安装中的 `--with-deps` 会调用系统包管理器，需要 root 或 sudo 权限；其余运行资产保存在此检出目录。上述检查无需 QQ 配置，不登录账号、不发送邮件、不改服务或定时任务。客户端三平台完整单测同时由 [Actions](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml) 执行。

真实部署验收继续按第 1–4 节操作。新部署时将下方的克隆命令改为上面的 `--branch` 形式，并使用固定部署目录。**不要在此测试目录直接运行 `server/install.sh`**：安装器会切换到 `/root/projects/wx-video-account-notes` 并安装系统服务。已有部署先保留配置、Cookie 与运行资产，确认该目录检出的分支后再升级。首次维护失败可能尝试给自己的 QQ 邮箱发一封错误通知；只有真实登录、Cookie 解析、服务请求和 timer 都通过，才算完成目标服务器验收。

## 1. 填写统一配置并安装

```sh
umask 077
mkdir -p /root/projects
git clone https://github.com/MuZiJin701/wx-video-account-notes.git /root/projects/wx-video-account-notes
cd /root/projects/wx-video-account-notes
sh server/install.sh
```

首次运行会创建权限为 `0600` 的 `config.json`，并提示 `CONFIG_INVALID`，此时尚未登录或启动服务。用文本编辑器填写其中的 QQ 账号和密码后，再运行同一安装命令。配置示例见 [`server/config.example.json`](../server/config.example.json)：

```json
{
  "access_key": "",
  "qq": {"account": "你的QQ号", "password": "你的QQ密码"},
  "cookie_check_interval_hours": 24,
  "verify_link": "https://weixin.qq.com/sph/AHhuzPE3Pi"
}
```

`access_key` 用于客户端调用服务，留空时自动生成，已有值则保留；QQ 账号密码仅用于服务器登录元宝和 QQ 邮箱。若验证链接失效，将 `verify_link` 换成有效的视频号分享链接。不要把配置文件、Cookie、浏览器资料或完整日志提交、发给他人；也不要在命令参数中填写密码。

安装脚本会：

1. 优先使用 PATH 中可执行的 uv（最低 `0.11.25`）；缺失、损坏或版本过旧时，沿用 Skill 的固定版本、SHA256 校验及平台私有目录方案。
2. 在项目 `.runtime/server/` 准备私有 Python 3.13.14、锁定的 Playwright 依赖和配套完整 Chromium；`playwright install --with-deps --no-shell chromium` 也会通过系统包管理器安装所需 Linux 库。浏览器依赖只安装在服务端。
3. 安装 Go 解析器、网关和 Cookie 维护程序，启用 `wx-notes-cookie.timer`，立即执行一次 Cookie 检查。QQ 密码登录会自动跳过可选的手机号绑定提示。

Cookie 验证通过才原子替换，失败保留原文件。安装脚本不会启动对外网关或 Go 服务；Cookie 检查失败时先按第 3 节排查，再启动它们。

当前验收限制：本机元宝和邮箱无头登录成功，但本次阿里云服务器的网页登录未通过；已有 Cookie 在该服务器完整解析正常。因此首次部署可能需要第 3 节的手动 Cookie 恢复，不能保证只填账号密码即可在目标服务器登录。详见[真实测试记录](research/yuanbao-qq-login.md#阿里云隔离验证2026-10-20)。

## 2. 启动与定时维护

```sh
systemctl enable --now wx-notes-resolver wx-notes-gateway
systemctl status wx-notes-resolver wx-notes-gateway wx-notes-cookie.timer
systemctl list-timers wx-notes-cookie.timer
curl -i http://127.0.0.1/api/channels/parse_sph
```

最后的未认证请求应返回 `401`，只说明网关有响应；完整解析需要第 4 节的客户端测试。

定时任务默认每天检查一次，服务器重启后也会补做一次检查：

- 现有 Cookie 通过完整解析验证：直接复用，无需启动浏览器。
- 解析失败：额外查询元宝登录状态。只有明确返回未登录时，才启动浏览器，优先复用浏览器登录态，必要时输入 QQ 账号密码。
- 网络故障、接口变化或状态不明：保留旧 Cookie，记录错误，不直接触发密码重登。
- 密码错误、无法跳过的验证或页面流程变化：暂停自动密码重试，等待人工修复；有效旧 Cookie 仍可继续使用。

每天检查意味着 Cookie 意外失效后，自动恢复最长可能要等到下一天。可随时手动触发一次检查：

```sh
systemctl start wx-notes-cookie.service
journalctl -u wx-notes-cookie.service -n 30
```

首次出现某类维护错误时，程序尝试用同一 QQ 账号密码登录 QQ 邮箱，给 `<QQ号>@qq.com` 发一封通知，仅含时间和错误码。同一未解决错误不会重复尝试通知；暂停状态也不会产生第二封告警。发信失败仅记录 `ERROR_MAIL_FAILED`，不递归发信。QQ 邮箱登录同样可能遇到风控或独立密码，因此请结合本地日志排查，不能保证告警送达。

## 3. 故障恢复、手动 Cookie 与升级

查看脱敏日志：

```sh
journalctl -u wx-notes-resolver -u wx-notes-gateway -u wx-notes-cookie.service -n 50
```

修正账号密码或处理登录异常后，显式恢复一次密码登录尝试：

```sh
PLAYWRIGHT_BROWSERS_PATH=/root/projects/wx-video-account-notes/.runtime/server/browsers \
  /root/projects/wx-video-account-notes/.runtime/server/.venv/bin/python \
  /root/projects/wx-video-account-notes/maintain_cookie.py --resume
```

恢复失败会再次暂停，旧 Cookie 保留。普通 `systemctl start` 不会解除暂停。程序用文件锁避免手动命令和定时任务并发操作浏览器。

仍可从电脑浏览器登录元宝，在开发者工具的网络面板复制元宝 API 请求的完整 Cookie，然后在服务器运行：

```sh
python3 /root/projects/wx-video-account-notes/update_cookie.py
```

输入不回显；候选 Cookie 会使用 `config.json` 的验证链接检查，通过后替换，无需重启解析器。保留 `WX_NOTES_VERIFY_LINK` 作为临时兼容覆盖。不使用 `document.cookie`，它可能缺少 HttpOnly 凭证。手动更新 Cookie 不会解除自动密码重试暂停。

升级时保留 `config.json`、`cookie` 和 `.runtime/`，重新运行 `sh server/install.sh`，随后重启网关和解析器。旧版只有 `client.json` 时，安装脚本会将其访问凭证迁入新 `config.json`，保留旧文件和 Cookie；补齐 QQ 配置后重跑。新配置已存在时以新配置为准。修改检查周期后也需重跑安装脚本，以更新 timer。

停止全部服务与定时维护：

```sh
systemctl disable --now wx-notes-cookie.timer
systemctl stop wx-notes-cookie.service wx-notes-gateway wx-notes-resolver
```

若也不希望网关和解析器开机启动，运行 `systemctl disable wx-notes-gateway wx-notes-resolver`。恢复时重新启用 timer 并启动上述两个服务。修复服务失败后可运行 `systemctl reset-failed` 再重试；手动修改 unit 后先 `systemctl daemon-reload`。

| 错误码或现象 | 处理 |
| --- | --- |
| `CONFIG_INVALID` | 填好 `config.json` 的 QQ 账号密码和有效验证链接；不要公开整个配置。 |
| `LOGIN_RETRY_PAUSED` | 修复账号或登录流程后手动运行 `maintain_cookie.py --resume`。 |
| `QQ_LOGIN_FLOW_FAILED` / `QQ_LOGIN_FAILED_OR_VERIFICATION_REQUIRED` | 检查密码、验证要求或页面变化；自动密码重试已暂停。 |
| `COOKIE_OR_UPSTREAM_UNAVAILABLE` | Cookie 无法解析且无法确认登录失效；检查网络、验证链接及上游接口。 |
| `NEW_COOKIE_VALIDATION_FAILED` | 新 Cookie 未通过完整解析检查，旧文件保留。 |
| `ERROR_MAIL_FAILED` | 邮箱登录、独立密码、风控或发信流程有变化；查看本地维护结果。 |
| `UNAUTHORIZED` | 客户端访问凭证与服务器 `config.json` 不一致。 |
| `LOGIN_REQUIRED` | 服务器尚无有效 Cookie，触发一次维护或手动更新。 |
| `LOGIN_EXPIRED_OR_UPSTREAM_CHANGED` | 登录态或元宝接口异常，不应仅凭此错误反复登录。 |
| `RESOLVER_UNAVAILABLE` | 检查解析器服务和本地 17879 端口。 |
| `RATE_LIMITED` | 等待一分钟；网关全局每分钟最多处理 30 次请求。 |

## 4. 客户端连接

仅查看访问凭证，不要输出包含 QQ 密码的整个配置：

```sh
python3 -c 'import json; print(json.load(open("/root/projects/wx-video-account-notes/config.json"))["access_key"])'
```

在**运行 agent 的电脑**备份并编辑实际安装的 Skill 中的 `runtime/resolver_config.json`：

```json
{
  "api_url": "http://<服务器>/api/channels/parse_sph",
  "access_key": "服务器config.json中的access_key"
}
```

填写实际公网地址；配置了 HTTPS 时填写完整 HTTPS 接口地址。插件安装副本与源码仓库各自独立；更新或重装前备份客户端配置。已有的 `WX_VIDEO_ACCOUNT_RESOLVE_API` 和 `WX_VIDEO_ACCOUNT_RESOLVE_KEY` 仍须成对设置，并优先于客户端文件。

交给 agent 一条真实分享链接，确认生成媒体、`note_materials.json` 和笔记，检查 OCR/ASR 状态。自部署失败不会自动切换到默认服务；恢复默认配置时还原备份。

HTTP 会明文传输链接、访问凭证和结果；需要加密时为网关配置 HTTPS，并只转发解析接口。更多见[登录实验与验收范围](research/yuanbao-qq-login.md)、[完整验收清单](../plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md)及[解析原理](research/wx-channels-upstream.md)。

[GitHub Actions](../.github/workflows/tests.yml) 的独立 Linux 浏览器任务会在干净 runner 上安装所需库，检查 Chromium 启动、JavaScript 和资料持久化。它使用合成页面和测试 Cookie，不包含真实 QQ 凭据，也不发送邮件；真实登录和远程服务生命周期仍须受控验收。
