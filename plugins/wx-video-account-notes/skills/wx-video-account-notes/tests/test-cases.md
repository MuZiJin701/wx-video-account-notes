# Manual smoke test checklist

Release checks that use real downloads, services, and models. Offline unit tests are documented in the [README](../../../../../README.md#本地开发).

For self-hosting, follow the [deployment guide](../../../../../docs/resolver-deployment.md) and edit `api_url` and `access_key` in the installed Skill's `runtime/resolver_config.json` before resolver and full Skill checks. Optional environment overrides take precedence. The September 29 record below covers only the default resolver ([issue #4](https://github.com/MuZiJin701/wx-video-account-notes/issues/4)).

## Prerequisites

- Run on Windows x64, Intel macOS x64, or Linux x64.
- Allow access to the WeChat Channels resolver, GitHub Releases, and Hugging Face.
- Use a fresh skill directory, or back up and remove the platform-specific `.runtime/<os>-<arch>/` before testing first-run behavior.

Run from the Skill directory; replace the sample link with a valid share link:

| Step | Windows | macOS / Linux |
| --- | --- | --- |
| Bootstrap | `pwsh -File scripts/bootstrap.ps1` | `sh scripts/bootstrap.sh` |
| Verify assets | `pwsh -File scripts/verify_runtime.ps1` | `sh scripts/verify_runtime.sh` |
| Process | `pwsh -File scripts/invoke_pipeline.ps1 -ShareUrl "https://weixin.qq.com/sph/your_share_id_here"` | `sh scripts/invoke_pipeline.sh --share-url "https://weixin.qq.com/sph/your_share_id_here"` |

## Cases

1. **Video post, default output**: use `https://weixin.qq.com/sph/AybwTXRwkt`. Confirm the output contains `<slug>.mp4`, `note_materials.json`, `raw.json`, `ocr.txt`, `asr.txt`, `ocr_frames/`, `frames/`, `audio/`, and `index.html`; confirm that `note_materials.json` contains `visual_frames`.
2. **Image post, default output**: use `https://weixin.qq.com/sph/AeGgo9k3KL`. Confirm images are written to `images/`, video/audio/ASR are skipped, `asr.txt` is empty, and the result records that the image post has no audio.
3. **Custom output directory**: confirm all note materials are written to the requested directory and the agent can create the final `<slug>.md` beside them.
4. **First bootstrap**: confirm creation of `.runtime/<os>-<arch>/`, reuse of compatible PATH uv (>=0.11.25) or download and verification of pinned private uv when missing/incompatible, then private Python, FFmpeg, model, and locked dependency sync. Check missing, old, broken, and compatible PATH uv separately; preserve the system installation.
5. **Repeat bootstrap**: confirm verified assets are reused rather than downloaded again and different platform directories are not reused.
6. **Failure recovery**: simulate an asset download, verification, or extraction failure. Confirm a non-zero exit, an error naming the asset, cleanup of `.tmp` files, preservation of completed assets, and no success report.
7. **Unsupported platform**: run on an unsupported OS or architecture. Confirm immediate failure with the detected OS/architecture and supported scope.
8. **Public resolver**: from the maintainer's machine, check that a missing Cookie produces `LOGIN_REQUIRED`, a wrong access key produces `UNAUTHORIZED`, and a working Cookie resolves a valid share link. Confirm unrelated routes return 404 and repeated requests hit the rate limit. Do not record response bodies or tokens.
9. **Full Skill acceptance**: use `https://weixin.qq.com/sph/AHhuzPE3Pi` from the maintainer's machine through the public HTTP endpoint. Confirm media download, `note_materials.json`, OCR/ASR status and final `<slug>.md`. If the media is unavailable, use another valid link and record only the reason for substitution.
10. **Cookie update**: check that real terminal input does not echo. Replacement, failure exit and preservation of the old file are covered by [unit tests](../../../../../server/test_update_cookie.py).
11. **systemd lifecycle (test server only)**: install with private `config.json`; migration from `client.json` preserves the access key and original file. Verify resolver/gateway units with `systemd-analyze verify`. Installation must not open a browser or maintain Cookie; upgrading disables/removes legacy Cookie timer/service and removes QQ credentials/schedule fields while preserving the access key and Cookie. Enable/start resolver/gateway, check unauthenticated 401, and resolve a real link. Test stop/disable/reboot and enabled restart recovery separately. Follow the [deployment guide](../../../../../docs/resolver-deployment.md).
12. **WeChat QR maintenance**: use the [standalone check](#standalone-wechat-login-check) to verify fresh WeChat QR login and full Go parsing through stdin without publishing Cookie. In an isolated maintenance runtime, test missing/expired Cookie, actual replacement with permissions 0600, and a second run that must reuse Cookie without a browser. Network/5xx/interface errors must preserve Cookie and avoid login. See the [record](../../../../../docs/research/yuanbao-manual-qr-login.md).
13. **Terminal QR and failure boundaries**: on ordinary SSH, confirm the Unicode QR is scannable with a phone, including light/dark themes and sufficient width. Confirm explicit agreement before QR display and before recognized registration controls; test new-account registration separately. Native QR expiry may refresh within the same three-minute deadline. Cancellation, extra verification, timeout, interruption or failed replacement must preserve the old Cookie and close Chromium. No passwords, SMS, mail or background retries may run. Manual Cookie pasting remains recovery.

## Standalone WeChat login check

Optional developer acceptance on a Linux x64 test host; ordinary deployment does not require this. Use an interactive SSH terminal and a separate checkout. Browser setup installs system libraries through the package manager and needs root or sudo.

```sh
git clone --branch main https://github.com/MuZiJin701/wx-video-account-notes.git ~/wx-notes-branch-check
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

Expect passing tests and `BROWSER_SMOKE_OK`. To check real login and full parsing without publishing Cookie, prepare a private test configuration:

```sh
umask 077
mkdir -p .runtime/server
if [ ! -e .runtime/server/login-check.json ]; then
  cp server/config.example.json .runtime/server/login-check.json
fi
chmod 600 .runtime/server/login-check.json
```

Set `access_key` to `login-check-only` and `verify_link` to a valid share link in that file. No QQ account or password is needed. Then run:

```sh
.runtime/server/.venv/bin/python server/check_login.py --config .runtime/server/login-check.json
```

Explicitly accept the displayed agreements before scanning. Both `YUANBAO_LOGIN_OK` and `YUANBAO_PARSE_OK` are required for success. The checker cleans temporary login state on exit and never publishes Cookie. Terminal QR scanning, refresh, registration and service lifecycle need the separate checks above.

## Record

Record the date, platform, architecture, Python version, bootstrap result, HTTP/business status, pipeline result, artifact existence and a short error category. Do not commit downloaded runtime assets, user media, Yuanbao Cookies, full media URLs or sensitive logs. The shared access key in the public Skill is intentionally distributed and must not be treated as secret.

2026-10-21 local delivery checks after scope confirmation: the locked Windows client suite passed 76 tests with one platform-specific skip; Windows server tests passed 23 with the Linux installer skipped. Local WSL Ubuntu passed all 23 server tests, including the isolated installer migration fixture. The existing locked browser runtime passed `BROWSER_SMOKE_OK` and an ephemeral-context isolation check with synthetic Cookie only; installer shell syntax and changed-document local links/anchors also passed. No new real login, scan, parsing with real Cookie, production operation, dependency installation or push was performed. The isolated real-scan record below is earlier evidence; ordinary SSH character-QR scanning, live expiry refresh, registration and production lifecycle remain unverified.

2026-10-21 manual WeChat maintenance: the isolated Aliyun Linux x64 runtime passed all 23 current server tests, shell syntax validation and `BROWSER_SMOKE_OK`. A real SSH PTY run displayed agreement links and the terminal QR; the maintainer explicitly agreed and scanned the auxiliary image. Full Go parsing and private atomic Cookie publication returned `COOKIE_UPDATED`, then a second run with browser acquisition prohibited returned `COOKIE_REUSED`. Temporary Cookie and runtime were removed. A subsequent anonymous live-page check passed the current WeChat entry and protocol-link checks without login. Ordinary SSH character-QR phone scanning, live expiry refresh, new-account registration and production systemd lifecycle remain unverified. Historical password/mail records below describe removed functionality.

2026-09-29 acceptance: Windows x64, Python 3.13.14. The maintainer's machine received HTTP 200 / `OK` from the public resolver and completed the video pipeline: media, `note_materials.json`, OCR, ASR, and final Markdown present. Runtime verification passed with previously installed local FFmpeg and a model whose SHA-256 matched the manifest. A clean download of the newly pinned FFmpeg archive was not completed on this network. ASR produced low-quality text for this sample; the final note marks it as unreliable.

2026-10-20 QQ login experiment: Windows x64, headed Chromium/Playwright, existing Linux resolver via WSL. Password login and session reuse after browser restart both passed real parsing (`PARSE_OK`, exit 0); Yuanbao's parse API returned HTTP 200 / code 0. This covers resolver feasibility only, not another full Skill acceptance run. Details and unverified cases are in the [experiment record](../../../../../docs/research/yuanbao-qq-login.md).

2026-10-20 integrated headless checks: Windows x64 and WSL Ubuntu 26.04 x64, private Python 3.13.14, locked Playwright 1.64.0/Chromium. Fresh QQ password login and real Go parsing passed on both platforms; Windows profile reuse passed without another password attempt. One authorized self-addressed QQ Mail test was confirmed in Sent and received by the user. Offline regressions cover pause/resume, failure preservation, notification deduplication, and send confirmation fallback. Linux credential-free browser smoke passed locally and subsequently in GitHub Actions (see the later records below). No production deployment, remote systemd lifecycle, or new media/OCR/ASR acceptance was performed.

2026-10-20 Alibaba Cloud follow-up: after the user requested stopping local WSL tests, isolated SSH checks on Ubuntu 24.04 x64 passed 20 server regressions, two applicable uv checks, Chromium smoke, and remote parsing using an existing Cookie through stdin. Fresh Yuanbao and QQ Mail web login did not complete; a bounded Yuanbao diagnostic ended with `QQ_LOGIN_FAILED_OR_VERIFICATION_REQUIRED` without a confirmed visible challenge or password-error message. No further password retries or mail sends were performed, and temporary remote login state was removed. Cloud automatic-login acceptance is not passed; production configuration and services were not changed.

2026-10-20 manual reproduction preparation: three-platform unit tests and credential-free Chromium smoke passed in [Actions](https://github.com/MuZiJin701/wx-video-account-notes/actions/runs/39425331428). The user's isolated server checkout at `b0e8eac` passed 20 server tests and `BROWSER_SMOKE_OK`; these commands did not attempt either QQ login. Added `server/check_login.py` for the next manual real-login checks, with offline regressions for profile cleanup, no mail sending, Cookie checking without publication, and sanitized failures. No additional real login or mail delivery was performed while adding this entry point.

2026-10-20 user manual reproduction: the independent checker introduced at `effab68` passed [three-platform unit tests, 23 Linux server tests and Chromium smoke in Actions](https://github.com/MuZiJin701/wx-video-account-notes/actions/runs/39428490824). On the user's server, Yuanbao printed `YUANBAO_CHECK_STARTED`, `YUANBAO_PASSWORD_ATTEMPT`, then `QQ_LOGIN_FAILED_OR_VERIFICATION_REQUIRED`; QQ Mail printed `MAIL_CHECK_STARTED`, then `MAIL_LOGIN_FAILED`. Both real-login checks failed, without deployment or mail sending. The password-attempt marker runs before filling credentials, and neither final error identifies a confirmed root cause. Detailed sanitized stage/page diagnostics are not implemented yet; the next thread should investigate the [handoff](../../../../../docs/research/yuanbao-qq-login.md#用户手动复现与排查交接2026-10-20) before another bounded login attempt. Do not use WSL, repeatedly submit passwords, deploy services, or send another test email as part of this handoff.
