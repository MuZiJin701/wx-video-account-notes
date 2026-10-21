# 元宝手动扫码登录需求澄清

日期：2026-10-21。分支：`codex/explore-qq-yuanbao-login`。

状态：用户已选定 Playwright/Chromium 微信扫码方案，手动维护与安装流程已改造，并通过隔离服务器的真实扫码、完整解析和 Cookie 复用检查；尚未部署生产。当前设计见 [ADR 0005](../adr/0005-manual-wechat-cookie-maintenance.md)。[ADR 0004](../adr/0004-self-deployed-browser-login.md) 与 [QQ 登录实验](yuanbao-qq-login.md) 中的定时密码登录和邮件告警属于历史方案。

## 交付范围确认（2026-10-21）

用户通过 `grill-with-docs` 再次确认：沿用 Playwright 启动临时无头 Chromium，在交互式 SSH 终端展示微信二维码，不采用常驻 Chromium/CDP；有效 Cookie 复用，缺失或明确失效才扫码，同时保留原手动粘贴入口，不启用定时登录、QQ 密码或邮件告警。本轮核对实现、同步所有受影响文档并执行本地回归，通过后提交探索分支并在本地合并 `main`；不推送、不部署，也不重复真实扫码。现有术语和 ADR 0005 已覆盖这些决定，无需新增术语或 ADR。

## 已明确的需求

- 自部署解析服务取消自动登录维护，不持续监控登录态，不设置定时维护任务；维护者自行决定何时手动运行。
- 移除全部 QQ 账号密码登录（包括元宝入口）、QQ 邮箱登录及发送邮件功能；新流程不要求 QQ 账号、密码或邮箱配置。历史实验记录保留。
- 已有元宝 Cookie 有效时直接复用；明确失效时，最终选定 Playwright/Chromium 微信扫码取得新的 Cookie。QQ 扫码和纯 HTTP 只保留实验记录。
- 维护者通过 SSH 在自部署 Linux 服务器手动执行命令，并在同一个终端扫描二维码、等待结果。
- 手动命令期间允许启动现有 Playwright 无头浏览器，获取网页二维码、等待扫码回跳；命令结束后退出浏览器。
- 接受微信登录与旧 QQ 登录不是同一个元宝账号，只要求能完成视频号解析；不做账号绑定或聊天记录迁移。
- 每次命令最多等待扫码 3 分钟，二维码过期可在此期间刷新；超时、取消或遇到其他人工验证时退出，保留旧 Cookie，由维护者重跑。
- 用户已放弃手机号短信登录方案，改为验证微信扫码与 QQ 扫码；不再进行短信登录实验。
- 实现微信二维码的 SSH 终端字符显示，图片只作辅助；无法完成图形验证时退出，保留手动粘贴 Cookie 的恢复入口。
- 终端先展示协议链接并要求输入 `yes`，明确告知扫码可能注册元宝账号；已识别的额外注册按钮需再次终端确认。新账号完整注册仍需单独实测，不能默默勾选协议。

## 改造前核实的实现基础（历史）

- `server/maintain_cookie.py` 已先调用解析器校验已有 Cookie，通过则直接返回 `COOKIE_REUSED`，不启动浏览器。
- `server/yuanbao_login.py` 提供登录态检查；现有维护流程不把所有解析失败都当成登录失效。
- `server/update_cookie.py` 已校验候选 Cookie，通过后原子替换文件；校验失败保留旧文件。
- 正式服务端流程尚无扫码入口、二维码提取或终端渲染实现；服务端直接依赖仅有 Playwright。已有 QQ 密码登录实验不能证明扫码端到端可用。
- Go 解析器每次请求重新读取 Cookie 文件，现有替换机制无需重启解析器。
- 当前维护由 systemd timer 定时启动一次命令，并非常驻轮询；安装器还会立即执行一次。实现新方案时需同时调整安装与升级流程，不能只删除仓库中的 timer 文件就假定已安装任务停止。

## 公开网页证据（2026-10-21 调查记录）

2026-10-21 只读核对[元宝首页](https://yuanbao.tencent.com/)及其当前运行时引用的公开脚本：

- [登录容器](https://static.yuanbao.tencent.com/_next/static/chunks/yb_v2_34399.32cee63cd292fde0.js)分别提供微信与 QQ 配置；[微信组件](https://static.yuanbao.tencent.com/_next/static/chunks/yb_v2_89912.4e5bfb3360cf7de7.js)使用 `WxLogin`、`snsapi_login` 和 `wechat_login`，并保存与回调关联的浏览器状态。
- [微信官方 SDK](https://res.wx.qq.com/connect/zh_CN/htmledition/js/wxLogin.js)创建 `open.weixin.qq.com/connect/qrconnect` iframe。终端展示二维码时，必须保留原浏览器上下文等待正常回跳，不能取到图片就销毁会话。
- 微信扫码是独立登录入口，不是 QQ 密码登录的附加验证。公开证据不能证明微信与 QQ 必然进入同一个元宝账号。
- 初步静态调查未创建二维码会话；后续隔离实验已确认可提取两种入口的真实二维码并输出终端字符，见下文。有效期、刷新和手机实际扫描仍需独立核实。

这些证据支持开展实现验证，不能替代目标服务器上的真实扫码和解析验收。扫码也不能保证永远不出现额外验证。

## 手机号路径的历史公开证据（已放弃）

用户明确表示短信验证会触发验证码，本轮不再尝试手机号方案。以下只保留此前的静态调查依据，不作为实现目标。

同日核对[当前登录组件](https://static.yuanbao.tencent.com/_next/static/chunks/yb_v2_97592.ae0cf12e1444a08c.js)：页面有独立手机验证码登录入口，包含手机号、区号、验证码及登录控件。但“获取验证码”先校验手机号与协议同意，再调用 `TencentCaptcha`；其回调提供 `ticket` 和 `randstr` 后才提交短信请求。因此短信登录也可能受图形验证阻碍，不能承诺仅靠终端文字输入就能成功。

[业务代码](https://static.yuanbao.tencent.com/_next/static/chunks/yb_v2_34399.32cee63cd292fde0.js)使用 `POST /api/login/getverificationcode` 并传递验证票据；这是网页内部实现，不是已承诺稳定的公开 API。手机号登录有独立成功处理，但还存在注册、协议确认、账号选择及安全复核分支。未请求上述接口、发送短信或提交手机号，也未验证账号关联与目标服务器上的最终解析。

页面协议链接：[元宝用户服务协议](https://rule.tencent.com/rule/202403110001)、[隐私政策](https://privacy.qq.com/document/preview/eb9be56572ab4886b6ca124e72abf413)。不应把账号注册或同意协议默认为普通 Cookie 维护的一部分。

## 运行边界

手动 Cookie 维护不会保证解析服务持续可用。若 Cookie 在两次手动运行之间失效，解析将失败，直至维护者再次执行命令并成功更新；没有可靠依据承诺固定的 Cookie 有效期。人机验证也由上游动态决定：只能验证特定环境与尝试的结果，不能承诺任一登录方式永久免验证。

## 早期实验计划（历史，已由下文验收记录取代）

用户已要求尝试微信扫码与 QQ 扫码并展示二维码，隔离显示实验已启动。下一阶段以手机识别二维码、确认授权后回到元宝且完整解析检查通过为验收；取得二维码不等于登录成功。失败则明确报告，保留手动 Cookie 入口，不接入图形验证码自动识别，也不循环尝试登录。

终端协议与注册交互应显示页面提供的协议链接和具体操作，等待维护者明确确认后才继续。注册不等于必须与旧 QQ 账号关联，账号绑定、安全复核及其他不可在本轮终端流程完成的步骤仍需明确报告。

## 阿里云隔离二维码显示实验（2026-10-21）

复用 `aliyun_wlcb` 上既有测试检出的 Python、Playwright 与 Chromium，不安装新依赖，不读取账号密码配置。使用无痕内存浏览器上下文分别打开两个登录入口，没有复用旧浏览器资料或 Cookie。

- 微信：当前网页默认展示微信登录，二维码在 `open.weixin.qq.com` iframe 的可见 `img.qrcode.js_qrcode_img` 中；取得原始 470×470 图片。
- QQ：点击元宝 `QQ` 入口后进入 `graph.qq.com`，二维码在 `xui.ptlogin2.qq.com` 的 `ptlogin_iframe` 中，图片元素为 `#qrlogin_img`；取得原始 111×111 图片，不点击密码登录。
- 从浏览器已经收到的图片响应读取原图，没有重新请求 QQ 二维码图片以免改变二维码会话。使用浏览器 Canvas 读取像素，按整数模块大小采样，加白边后以 Unicode 半块字符输出；微信图片模块为 10 像素，QQ 为 3 像素，两者均成功输出。
- 二维码提取与字符渲染只用已有 Playwright 和 Python 标准库，无需新增依赖。字符渲染的合成自检通过；真实终端的手机识别仍需维护者实扫，不能由自检替代。
- 两张原图已复制到本机忽略目录并在聊天显示。隔离命令保持原上下文最多 3 分钟等待扫描；没有将 Cookie 输出到日志或发布到现有 Cookie 文件。
- 维护者反馈两张二维码都已扫描并登录成功，没有额外验证。第一轮脚本独立得到 `WECHAT_LOGIN_OK`，但 QQ 在等待结束前没有通过元宝登录态检查，返回 `QQ_SCAN_NOT_COMPLETED`；手机提示成功不能单独替代元宝网页登录态验收。
- 为区分 QQ 授权与元宝最终回跳，第二轮仅检查 QQ，加入“跳过，直接登录”可选绑定处理和明确的“授权并登录”按钮处理；不输入密码、不读取凭据。维护者再次确认手机扫码成功。脚本确认网页已从 `graph.qq.com` 返回 `yuanbao.tencent.com`，但 3 分钟内仍未通过元宝登录态检查，最终 `QQ_SCAN_NOT_COMPLETED`；没有观察到上述两个精确文字控件。具体原因未确定，不能声称 QQ 完整登录已由服务器验收。
- 两轮均输出 `BROWSER_CLOSED_NO_COOKIE_PUBLISHED`，浏览器已退出，没有后台登录监控。没有更新现有 Cookie、配置或服务，也没有执行真实分享链接解析校验。

初步结论：微信与 QQ 的二维码均可以在阿里云无头浏览器中取得、复制原图并输出为普通终端字符；维护者反馈两张原图都可扫码，且手机端未出现额外验证。微信通过程序端登录态检查；当时 QQ 尚未通过，后续已查明原因并完成实扫与完整解析验证，见下节。字符码在真实 SSH 终端中的手机实扫与自动刷新仍未验收。

验证：诊断脚本字符渲染自检与 Python 语法编译通过，未新增依赖。正式业务代码未变更，本轮不重复运行整套服务端回归。

实验脚本和二维码位于本机忽略目录 `.runtime/login-diagnostics/`，远端仅在既有测试检出 `.runtime/server/` 中保存诊断脚本与二维码图片。它们不是正式登录入口，二维码会过期，不纳入 Git。

新 Cookie 只在完整解析验证成功后原子发布；网络或上游故障不能单独判定 Cookie 失效。取消定时维护时应调整安装、升级入口；保留无关私有数据，不进行服务器部署或删除历史资产。

## QQ 回跳失败根因与对照验证（2026-10-21）

**已确认根因：QQ 授权会话使用的 nonce 与元宝本地保存的 `hyc-login-nonce` 不一致，元宝拒绝完成网页登录。QQ 扫码本身可用。** 实验脚本原先没有检查这一会话条件，并以宽泛异常处理隐藏了具体失败信息，最终仅输出 `QQ_SCAN_NOT_COMPLETED`，不能准确表达实际阶段。

### 失败证据

新增脱敏诊断后再次实扫 QQ，回调带有授权码和 nonce，且 `state=qq_login`；页面初始化时的 `nonce_matches_storage=false`。元宝浏览器内 `fetch` 与原脚本的 `context.request` 检查均返回 HTTP 401，排除了仅原脚本请求方式不适用这一解释。没有观察到绑定、注册或其他待操作的页面控件。

进一步构造无需手机扫码的最小探针，复用浏览器执行同一 QQ 入口，比较授权 URL 的 nonce 与元宝本地保存的 nonce；仅用临时序号关联值，不输出实际内容。捕获到以下失败样本，命令返回 1：

```text
NONCE_CHECK {"active_nonce_id": 2, "first_qr_nonce_id": 2,
 "saved_nonce_id": 5, "nonce_matches": false,
 "qr_changed_after_capture": false, "oauth_count": 1}
```

该样本中本地 nonce 先后写入五个不同的值，但实际进入的 QQ 授权页仍使用较早的值。另有匹配样本，说明是时序问题，不能简单归结为所有 QQ 登录均不可用，也不能仅靠固定延时保证正确。

当前腾讯公开的 [QQ 登录组件](https://static.yuanbao.tencent.com/_next/static/chunks/yb_v2_97592.ae0cf12e1444a08c.js)在组件执行时生成随机 nonce 并写入 localStorage，再通过延迟 200 毫秒的回调跳转 QQ。这个实现与多次写入、实际导航落在较早会话的轨迹一致，支持前端重渲染和延迟导航形成竞态的解释。[元宝回调校验代码](https://static.yuanbao.tencent.com/_next/static/chunks/yb_v2_26411.8d1e006b42c4c4a0.js)会在 nonce 缺失或不匹配时拒绝后续登录，因此 QQ 手机端确认成功仍可能没有取得元宝登录态。

### 实验脚本处理与成功对照

只调整隔离实验：展示 QQ 二维码前，核对当前授权 URL nonce 与元宝 localStorage 中的值；等待短暂的导航变化并重新定位当前 iframe 的二维码。值仍不一致的会话直接丢弃，最多重新创建三个匿名会话；不修改 nonce、不忽略校验、不复用失配回调。新会话只用于产生二维码，尚未提交密码或进行账号登录。此检查不改变正式服务端代码。

实际观察到失配会话在展示前被拦截；随后取得通过检查的二维码，维护者再次扫码确认，结果如下：

```text
QR_SESSION_CHECK {"nonce_matches": true}
CALLBACK_INITIAL_STATE {"nonce_matches_storage": true, "state_is_qq_login": true}
ORIGINAL_PROBE {"http": 200, "body": {"userId_present": true}}
QQ_LOGIN_OK
QQ_PARSE_OK
BROWSER_CLOSED_NO_COOKIE_PUBLISHED
```

其中 `QQ_PARSE_OK` 复用仓库的 `check_cookie`，用现有 Go 解析器及默认验证分享链接完成检查；Cookie 仅经标准输入交给独立临时解析器，没有输出到日志或保存到现有 Cookie 文件。临时解析器副本随检查退出清理，浏览器也已关闭。

### 复现入口与限制

脚本及脱敏日志继续保存在忽略的诊断目录，不作为正式用户入口。服务器已有依赖下的最小会话检查命令：

```sh
/root/wx-notes-branch-check/.runtime/server/.venv/bin/python \
  /root/wx-notes-branch-check/.runtime/server/qq-nonce-probe-20261021.py original
```

扫码对照使用同一诊断脚本的 `--qq-only --diagnose --nonce-guard` 模式。二维码字符渲染与脱敏摘要自检、Python 语法编译均通过。诊断前后没有修改生产配置、现有 Cookie 或服务，没有发送短信、邮件或提交密码；正式业务代码没有新增调试日志。

结论限于本次阿里云、当前前端和本次账号的实扫与完整解析。两种扫码方式都没有永久免额外验证的保证；普通 SSH 字符码实扫、过期刷新、长期 Cookie 复用及正式手动维护改造仍需分别验收。

## 纯 HTTP 对照（2026-10-21）

用户随后要求验证不启动 Playwright/Chromium 的方案。QQ 和微信的纯 HTTP 二维码、扫码确认及 OAuth 回跳均通过，但两条路径在元宝登录接口都遇到 `57002 / waterProof` 额外安全验证，尚未取得通过验收的元宝 Cookie，未运行新 Cookie 的完整解析。详细过程与限制见[纯 HTTP 扫码登录对照](yuanbao-http-qr-login.md)；此前 `QQ_LOGIN_OK`、`QQ_PARSE_OK` 的成功记录属于浏览器方案，不能当作纯 HTTP 成功。

随后按维护者要求展示具体验证：微信纯 HTTP 流程触发安全验证后，仅在展示题目时启动官方验证码组件，实际看到“按文字描述选择图片”的六图题；没有作答或提交。此样本不能证明 QQ 题型相同，也不代表未来每次固定出现此题型，详见[实际验证码展示](yuanbao-http-qr-login.md#实际验证码展示2026-10-21)。

## 待澄清或验证

- 普通 SSH 字符二维码的手机实扫、真实过期刷新、新账号注册与其他额外账号页面；字符渲染、有限刷新和异常退出已有离线检查。
- 生产安装/升级和 systemd 生命周期；安装器迁移已在隔离 fixture 检查，没有修改生产服务。

## 微信手动维护改造与真实验收（2026-10-21）

用户最终选择浏览器微信扫码，已实现 `server/maintain_cookie.py` 手动入口：先完整解析校验现有 Cookie，通过则不启动浏览器；仅缺失或明确失效时进入微信扫码。候选 Cookie 完整解析通过后原子替换；网络/上游异常、扫码失败、额外验证和候选检查失败保留原文件。

同一分支移除 QQ 密码与邮箱实现、旧诊断入口和 Cookie timer/service，配置只要求访问凭证及验证链接。安装不再立即维护；升级时停用并移除已安装的旧维护 unit，清除活动配置中的 QQ 密码及周期字段，保留旧 Cookie 和访问凭证。原手动粘贴 Cookie 入口保留。

隔离阿里云运行目录使用本次实现和既有锁定的浏览器依赖。维护者明确确认协议后，命令在真实 SSH PTY 输出带白色静区的 ANSI/Unicode 字符码及辅助图，维护者扫描辅助图并确认。结果：

```text
FIRST_MANUAL_RUN COOKIE_UPDATED
SECOND_MANUAL_RUN COOKIE_REUSED
WECHAT_MANUAL_MAINTENANCE_ACCEPTANCE_OK
ACCEPTANCE_PRIVATE_STATE_REMOVED
```

第一次从缺失 Cookie 开始，实际登录、完整 Go 解析并保存权限 `0600` 的 Cookie；第二次禁止调用浏览器获取函数，仍通过已有 Cookie 完整解析并返回复用。临时 Cookie、解析器副本和二维码随独立验收目录清理；未覆盖生产配置、Cookie 或服务。此验收没有模拟真正过期的有效 Cookie、等待真实二维码过期或注册新账号；相关分支由离线回归覆盖，普通终端字符码手机实扫仍未确认。

操作与恢复命令见[自部署指南](../resolver-deployment.md)。

## 本轮本地交付验证（2026-10-21）

需求再次确认后的检查：Windows 锁定客户端环境运行 76 项测试（1 项平台专用检查跳过），服务端 23 项（Linux 安装器检查跳过）；本机 WSL Ubuntu 的服务端 23 项全部通过，包含隔离安装升级 fixture。复用已有锁定浏览器运行时，`BROWSER_SMOKE_OK` 与临时上下文隔离检查 `EPHEMERAL_CONTEXT_SMOKE_OK` 均通过；后者确认新上下文不继承前一上下文的合成 Cookie。安装脚本语法和受影响文档的本地链接/锚点检查通过。

本轮没有访问元宝登录页、使用真实账号或 Cookie、重新扫码、修改生产服务或安装新依赖。上节隔离服务器实扫属于此前验收，本轮本地检查不能替代实扫；普通 SSH 字符码实扫、真实过期刷新、新账号注册及生产 systemd 生命周期仍未验收。
