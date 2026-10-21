# ADR 0005: Manual WeChat QR Cookie maintenance

Status: Accepted (2026-10-21). Supersedes [ADR 0004](0004-self-deployed-browser-login.md).

## Decision

The operator periodically runs a command through an interactive SSH terminal on the Linux x64 server. Nothing schedules Cookie checks, starts login during installation, or keeps a browser monitoring login. Remove QQ account/password login, QQ Mail login and notifications, their required configuration, and the Cookie systemd timer/service.

First run the existing full resolver check on the saved Yuanbao Cookie. Success returns `COOKIE_REUSED` without launching a browser or changing the file. If parsing fails, independently check Yuanbao login: only an explicit unauthenticated response, or an absent Cookie, permits QR login. Network errors, upstream errors and an otherwise valid login preserve the previous Cookie and return a failure.

On expiry, use the existing locked Playwright and matching headless Chromium to open Yuanbao's native WeChat login. A fresh ephemeral browser context avoids retaining another source of credentials. Show the service/privacy agreement links and require explicit terminal confirmation before displaying the QR; warn that scanning can create a Yuanbao account. Allow a recognized native registration confirmation only after another explicit terminal confirmation. Skip an optional phone-binding prompt; do not link accounts, migrate history, request SMS or submit passwords.

Render the native QR as colored Unicode half blocks in the terminal, with a white quiet zone. A private image is auxiliary and is deleted on exit. Show changed QR codes and use the native refresh control when expiry is detected, without extending the three-minute scan deadline. Cancellation, timeout, additional verification, unknown page changes or failed resolver validation terminate the command and preserve the previous Cookie. Keep manual no-echo Cookie pasting as recovery.

After Yuanbao confirms login, extract Cookie scoped to the resolver API. The existing full resolver check must pass before an atomic private-file replacement. A nonblocking file lock prevents concurrent maintenance commands. Close Chromium on success, failure and interruption; do not log Cookie, OAuth parameters, private page text or raw browser errors.

## Consequences and validation

Upgrades preserve the existing resolver access key and Cookie, remove obsolete QQ credentials/schedule fields from the active configuration, and disable/remove the former maintenance units. Old browser profiles are not read; private runtime data is not indiscriminately deleted. Installation still prepares the locked browser runtime but requires a separate interactive maintenance command.

On the isolated Aliyun Linux checkout, a real WeChat scan produced `COOKIE_UPDATED` after full parsing, followed by `COOKIE_REUSED` with browser acquisition prohibited by the acceptance harness. Generated test Cookie and temporary runtime were removed; production configuration, Cookie and services were not modified. Offline tests cover safe replacement, unknown status, QR rendering, bounded refresh, cancellation/verification handling, browser cleanup and installer migration. Ordinary SSH terminal phone scanning, live QR expiry and new-account registration remain separate manual checks. Future Tencent verification behavior is not guaranteed.

The [QR research](../research/yuanbao-manual-qr-login.md) records the browser experiments; the [HTTP comparison](../research/yuanbao-http-qr-login.md) records why pure HTTP was not selected. User operation is documented in the [deployment guide](../resolver-deployment.md).
