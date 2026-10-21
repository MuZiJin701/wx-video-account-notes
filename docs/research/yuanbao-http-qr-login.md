# 元宝纯 HTTP 扫码登录对照

日期：2026-10-21。分支：`codex/explore-qq-yuanbao-login`。

**结论：QQ 与微信的二维码获取、手机确认和 OAuth 回跳均可通过纯 HTTP 完成；本轮两条路径都在元宝换取登录态时收到 `57002 / waterProof` 额外安全验证要求，未取得通过验收的元宝 Cookie。** 这不是完整登录成功，也不能据此断言所有环境下纯 HTTP 永远不可用。

用户随后选定 Playwright/Chromium 微信扫码用于正式手动维护，已在隔离服务器通过登录、完整解析及 Cookie 复用，见[实现验收](yuanbao-manual-qr-login.md#微信手动维护改造与真实验收2026-10-21)。本文保留纯 HTTP 对照，不是当前登录实现。

## 范围与环境

- 纯 HTTP 登录对照使用既有 `aliyun_wlcb` 测试检出和 Python 运行时，只调用标准库 `urllib.request`、`http.cookiejar` 等，不启动 Chromium，不导入 Playwright，不执行网页 JavaScript。随后为查看具体验证码，单独使用现有 Chromium 展示官方验证码组件，见下文；该展示不属于纯 HTTP 登录成功。
- 每次初始试验使用新的内存 CookieJar，不读取 QQ 账号密码或之前的浏览器 Cookie；维护者扫码并在手机上确认。
- 元宝接口请求使用网页客户端标识 `X-Instance-ID: 5`、`X-Source: web`，以及原有 HTTP 预检查使用的 User-Agent。没有伪造验证码成功票据、忽略安全验证或提交密码。
- 仅在隔离诊断目录保存脚本、二维码和脱敏阶段日志；不覆盖现有 Cookie、配置或服务，不安装新依赖，不发送邮件或短信。

## QQ 路径

1. 以客户端生成并保管的 nonce 构造元宝 QQ OAuth 入口，通过公开授权页取得登录 iframe 配置。本轮参数为 QQ 登录 `appid=716027609`、`daid=383`、第三方应用 `102115537`。
2. 请求 `ptqrshow` 得到二维码及配对的 `qrsig`，按 [QQ 官方登录脚本](https://qq-web.cdn-go.cn/monorepo/3ea7b82c/ptlogin/js/c_login_2.js)的 hash33 算法生成轮询参数；没有账号密码检查或提交。
3. 维护者扫码后，轮询依次收到 `66`、`67`、`0`，随后完成原生 `check_sig` 跳转。
4. QQ 的 `login_jump` 返回通知父页继续授权的 JavaScript，不会单靠 HTTP 302 完成全部步骤。依据 [QQ 官方授权页脚本](https://imgcache.qq.com/c/=/open/connect/widget/pc/login/pt_adapt.js,qlogin_v2.js?v=20181229)，用同一会话提交授权表单，包括 `p_skey` 对应的防 CSRF 参数及原授权字段，然后验证元宝回调的 nonce、state 和授权码。
5. 参考[元宝公开登录业务代码](https://static.yuanbao.tencent.com/_next/static/chunks/yb_v2_26411.8d1e006b42c4c4a0.js)，向 `/api/joint/login` 提交 QQ 授权码；带 Web 客户端标识的请求返回 HTTP 400、错误码 `57002`、`safeVerifyTypes=["waterProof"]`，停止试验。

实现中曾分别停在 `login_jump` 的脚本通知、授权接口直接重定向的响应处理，两处均补齐后才到达元宝回调。早期未带 Web 客户端标识的请求返回 HTTP 200，但没有可用登录态，后续 `/api/getuserinfo` 仍为 401；没有把这些中间结果算作登录成功。

关键结果：

```text
HTTP_QQ_QR_READY browser_started=false cookie_jar=fresh
HTTP_QQ_POLL 66
HTTP_QQ_POLL 67
HTTP_QQ_POLL 0
HTTP_QQ_AUTHORIZE_REDIRECT_OK
HTTP_QQ_OAUTH_CALLBACK_OK
HTTP_YUANBAO_LOGIN_RESPONSE {"http":400,"error_code":"57002"}
SAFE_VERIFY_TYPES ["waterProof"]
```

## 微信路径

1. 使用元宝微信应用 `wx12b75947931a04ec` 和 `snsapi_login`，通过 `open.weixin.qq.com/connect/qrconnect` 创建新的授权会话。
2. 从当前公开页面取得二维码及轮询配置，直接获取原图供维护者扫描。本轮微信图片为 JPEG，不能只按 PNG 识别。
3. 按页面实现请求 `lp.open.weixin.qq.com/connect/l/qrconnect`，收到等待、已扫和已确认状态；解析返回的授权码后访问元宝回调，检查本次生成的 nonce 和 `wechat_login` 状态。
4. 向元宝 `/api/joint/login` 提交微信授权码，同样收到 HTTP 400、错误码 `57002` 和 `waterProof`，停止试验。

关键结果：

```text
HTTP_WECHAT_QR_READY browser_started=false cookie_jar=fresh
HTTP_WECHAT_POLL 408
HTTP_WECHAT_POLL 404
HTTP_WECHAT_POLL 405
HTTP_WECHAT_OAUTH_CALLBACK_OK
HTTP_YUANBAO_LOGIN_RESPONSE {"http":400,"error_code":"57002"}
HTTP_YUANBAO_SAFE_VERIFICATION ["waterProof"]
HTTP_QR_FAILED YUANBAO_SAFE_VERIFICATION_REQUIRED
```

## 安全验证与结论边界

元宝公开前端将 `waterProof` 路径交给 `SafeWaterwall` / `TencentCaptcha`，等待正常验证回调提供票据后再继续。首次对照仅记录验证类型，没有展开题目；随后按维护者要求查看了实际题型，结果如下。没有伪造结果或接入打码。

### 实际验证码展示（2026-10-21）

维护者重新微信扫码确认后，纯 HTTP 流程再次完成 OAuth 回跳，并在 `/api/joint/login` 收到 `57002 / waterProof`。使用同一 HTTP 会话和服务端返回的 `safeVerifyCode` 请求 `/api/v5/accountLogic/safeVerify/detail`，取得该验证的 `waterProofAppid`。

随后仅为展示题目，使用既有 Playwright/无头 Chromium，在元宝源下的隔离页面加载[官方验证码 SDK](https://static.yuanbao.tencent.com/m/lib/TCaptcha.js)，按公开前端调用方式创建 `TencentCaptcha` 并展示。隔离页面没有加载账号资料或复用现有登录 Cookie；没有将安全验证标识或登录响应输出到日志。

**本次实际出现的是按文字描述点选图片的验证码**：提示“选择最符合描述的图片”，关键词为“葡萄”，下方为 2 行 × 3 列共 6 张候选图，提供“换一组”和“确定”。界面标注“混元 AI 生成”。截图保留在本机忽略的诊断目录，未加入 Git。

```text
HTTP_WECHAT_OAUTH_CALLBACK_OK
HTTP_YUANBAO_SAFE_VERIFICATION ["waterProof"]
CAPTCHA_DETAIL_OK waterProofAppid_present=true
CAPTCHA_SDK_STATE {"ready":true,"result":null,"frameCount":1}
CAPTCHA_IMAGE_CAPTURED
CAPTCHA_INSPECTION_ONLY_NO_ANSWER_NO_LOGIN_SUBMISSION
CAPTCHA_BROWSER_CLOSED
HTTP_QR_FAILED YUANBAO_SAFE_VERIFICATION_REQUIRED
```

没有选择图片、点击“确定”、提交验证码票据或继续换取登录态；展示后关闭浏览器。此次确认只覆盖微信触发后的当前组件样本；QQ 虽返回相同 `waterProof` 类型，但没有另行展开其题目，不能断言题型完全相同。验证码可能动态变化，也不能将该样本视为永久固定题型。

对照说明：不启动浏览器也能获得两个入口的二维码并完成扫码授权，但本轮纯 HTTP 客户端尚不能直接取得可供解析器使用的元宝登录态。此前 Playwright 的 QQ 实扫和完整解析已通过，见[浏览器扫码实验](yuanbao-manual-qr-login.md#qq-回跳失败根因与对照验证2026-10-21)。这些不是严格的同期单变量实验，不能据此确定触发安全验证的是 IP、HTTP/TLS 特征、未执行设备脚本、请求字段或其他具体因素，也不能证明所有可能的 HTTP 实现都会失败。

未取得已验证的登录态，所以本轮没有运行新 Cookie 的 Go 完整解析检查。普通 SSH 字符二维码转码和过期刷新也未验收；本轮展示的是 HTTP 获取的原始图片。

## 资产、验证与清理

- 本机忽略目录中的 `http_qr_probe.py` 保留纯 HTTP 实验入口，`http_probe.py` 提供既有页面参数解析；QQ JSONP 只用受限字面量解析，不执行返回脚本，并校验 HTTPS 及跳转域名。
- `inspect_http_captcha.py` 是忽略目录中的题型查看辅助脚本，仅在显式 `--inspect-captcha` 时读取验证详情并启动官方组件；缺失或非法验证码配置的自检与 Python 语法编译通过。它不作答、不调用安全验证提交接口，也不更新 Cookie。
- 自检覆盖 hash33、CSRF 初始值、正常轮询回调、恶意回调拒绝及非法跳转 URL 拒绝；自检与 Python 语法编译通过。实扫检查的失败是研究结论，不能写成完整登录验收通过。
- 为避免反复扫码，QQ 后半段曾使用服务器独立诊断目录内、权限 `0600` 的临时 CookieJar 和状态文件续接。排查时的私有响应只用于本地解析，没有复制到聊天或 Git。
- 完成对照后已核实并删除本轮生成的临时 CookieJar、nonce/OAuth 状态及私有响应文件。只保留诊断脚本、过期二维码与脱敏日志；未修改现有 Cookie、配置或服务，也未提交、推送或部署。
