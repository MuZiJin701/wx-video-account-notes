# QQ 密码登录与元宝 Cookie 实验

日期：2026-10-20。测试代码基于 `d5ebf23`，探索分支为 `codex/explore-qq-yuanbao-login`。

## 结论

本次本机实验中，QQ 密码登录取得的**元宝 Cookie**可以用于现有视频号解析流程；关闭并重新打开浏览器后，登录态仍可复用。早先的可视实验仅验证可行性；后续已集成浏览器自动登录、每日 Cookie 维护与 QQ 邮箱告警，操作见[部署指南](../resolver-deployment.md)。

## 方法与结果

环境为 Windows x64、可视 Chromium 和 Playwright；现有 Linux 解析二进制通过 WSL 执行。仅测试了一个账号和一条真实分享链接 `https://weixin.qq.com/sph/AHhuzPE3Pi`。

| 检查 | 结果 |
| --- | --- |
| 从项目外私有 JSON 读取 QQ 账号密码并自动填写 | 成功；未在聊天或日志中输出凭证。 |
| QQ 登录后的可选手机号绑定 | 两次选择“跳过，直接登录”后进入元宝主界面；本次成功流程未要求人工验证码。 |
| 提取 Cookie | 从浏览器上下文获取元宝解析接口适用的 Cookie，不使用 QQ 网站 Cookie 代替。 |
| 调用元宝解析接口 | HTTP 200、`code=0`，含 `wx_export_id` 和 `playable_url`。 |
| 现有 `resolver --check-cookie` 验证 | Cookie 经标准输入传入，返回 `PARSE_OK`，退出码为 0。 |
| 关闭并重新打开同一专用浏览器资料目录 | 无需再次输入密码；完整解析检查再次返回 `PARSE_OK`。 |

这次验证覆盖元宝解析和视频号详情两步请求，未重新执行媒体下载、OCR/ASR 或最终笔记生成。未修改线上 Cookie 或服务；账号密码、浏览器资料和登录态均留在项目外，不纳入 Git，也不保存原始响应或媒体令牌。

## 已集成的维护方案

1. [`maintain_cookie.py`](../../server/maintain_cookie.py) 在部署后立即、之后每天验证已有 Cookie；验证成功就直接复用，不启动浏览器。
2. 解析失败后用元宝 `GET /api/getuserinfo` 区分明确未登录（HTTP 401）和状态不明。只有明确失效或缺失时，才以新无头 Chromium 打开专用浏览器资料，复用登录态或从私有 `config.json` 读取 QQ 账号密码登录，跳过可选手机号绑定。
3. 新 Cookie 通过完整解析检查后，复用 [`update_cookie`](../../server/update_cookie.py) 原子替换；失败保留旧文件，解析进程无需重启。
4. 异常登录失败持久化暂停密码重试，需要 `--resume` 恢复；首次维护错误尝试用独立 QQ 邮箱资料目录给自己发通知。只发送固定错误码和时间，通知失败不递归。

`LOGIN_EXPIRED_OR_UPSTREAM_CHANGED` 也可能表示上游接口变化，不能对所有解析失败都反复重新登录。服务端统一使用 `config.json`；客户端的 `runtime/resolver_config.json` 继续只配置服务地址和访问凭证。配置、浏览器资料和 Cookie 不进入 Git 或公开日志。

## 后续无头验证（2026-10-20）

Windows x64、Playwright 1.64.0 配套 Chromium、新无头模式，使用独立资料目录及用户提供的私有凭据文件：

| 检查 | 结果 |
| --- | --- |
| QQ 密码登录元宝 | 成功；`getuserinfo` 返回 HTTP 200。 |
| 新 Cookie 完整解析验证 | WSL 执行仓库 Go 解析器，标准输入传入 Cookie，得到 `PARSE_OK`。 |
| 关闭、重新打开无头浏览器 | 登录态复用成功，未再次提交密码。 |
| QQ 邮箱网页登录 | 同一组账号密码登录成功，使用独立资料目录。 |
| 一封授权的“部署验证”邮件 | 仅发送到账号自己的 QQ 邮箱；“已发送”确认，用户确认收到。 |

邮箱的发送成功提示未被最初的精确匹配捕获，但已发送邮件和用户收信确认了实际送达。实现已补上在提示未捕获时，按唯一主题核查“已发送”的确认路径；该分支使用离线回归验证，没有再发第二封测试邮件。

Linux x64 补充验证：WSL Ubuntu 26.04、项目私有 Python 3.13.14、相同锁定 Playwright 和 Chromium，以新无头模式成功完成 QQ 密码登录及 `PARSE_OK`。重启浏览器后复用登录态，实际 Cookie 原子更新成功；完整维护返回 `COOKIE_REUSED`，没有再次启动浏览器或发邮件。浏览器曾缺少 NSS 和音频动态库；测试仅将对应系统包下载解压到项目私有目录，通过进程级 `LD_LIBRARY_PATH` 使用，未向系统安装包。真实登录发现 iframe 初始空白地址的加载竞态，已修复并增加离线回归。无凭据的浏览器启动、JavaScript 和资料持久化 smoke 检查通过，并已接入 GitHub Actions 工作流；各次提交的实际结果见 [Actions 运行记录](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml)。

## 阿里云隔离验证（2026-10-20）

经用户指定，通过 `ssh aliyun_wlcb` 在 Ubuntu 24.04 x64 的独立临时目录测试，未改动现有配置、Cookie、systemd 服务或公网端口，也未安装系统包。QQ 凭据只通过 SSH 标准输入交给测试进程；未写入远端配置或日志，测试浏览器资料和临时 Cookie 已清理，没有再发送邮件。

| 检查 | 结果 |
| --- | --- |
| 服务端离线回归 | 20 项通过。 |
| uv 选择检查 | 2 项通过，Windows 专属项跳过；私有 uv 归档 SHA256 校验通过。 |
| 真实 Chromium、新无头模式、JavaScript 与资料持久化 | 通过，与新增 Actions smoke job 使用同一检查脚本。 |
| 已在本机取得的 Cookie 交给远端 Go 解析器 | 通过；Cookie 仅经标准输入传递，没有写入服务器。 |
| 服务器 QQ 密码登录元宝 | 未通过；停留在 `graph.qq.com`，最终 `QQ_LOGIN_FAILED_OR_VERIFICATION_REQUIRED`。受限诊断未确认可见验证码或密码错误提示，根因未确定。已停止密码尝试。 |
| 服务器 QQ 邮箱登录 | 未通过，未发送邮件。Windows 的实际收信结果不能证明服务器能登录邮箱。 |

因此不能将本次改造视为云服务器自动登录验收已通过，也不能用无凭据 CI 的成功代替真实账号验收。服务器可继续使用手动更新 Cookie 的恢复入口；QQ 网页自动登录需要在目标环境进一步验证。

待验证：服务器网页登录失败原因、真实过期或被服务端注销后的重新登录、不可跳过的验证、浏览器资料损坏，以及长期运行的稳定性。尚未在远程服务器安装或启动正式服务，也未执行真实 systemd 重启验收；本机成功不能保证所有账号可用或永久无人值守，也不能保证登录异常时 QQ 邮箱仍可登录。
