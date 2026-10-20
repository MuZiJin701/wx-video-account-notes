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

1. **Video post, default output**: use `https://weixin.qq.com/sph/AybwTXRwkt`. Confirm the output contains `<slug>.mp4`, `note_materials.json`, `raw.json`, `ocr.txt`, `asr.txt`, `ocr_frames/`, `frames/`, and `audio/`; confirm that `note_materials.json` contains `visual_frames`.
2. **Image post, default output**: use `https://weixin.qq.com/sph/AeGgo9k3KL`. Confirm images are written to `frames/`, video/audio/ASR are skipped, `asr.txt` is empty, and the result records that the image post has no audio.
3. **Custom output directory**: confirm all note materials are written to the requested directory and the agent can create the final `<slug>.md` beside them.
4. **First bootstrap**: confirm creation of `.runtime/<os>-<arch>/`, reuse of compatible PATH uv (>=0.11.25) or download and verification of pinned private uv when missing/incompatible, then private Python, FFmpeg, model, and locked dependency sync. Check missing, old, broken, and compatible PATH uv separately; preserve the system installation.
5. **Repeat bootstrap**: confirm verified assets are reused rather than downloaded again and different platform directories are not reused.
6. **Failure recovery**: simulate an asset download, verification, or extraction failure. Confirm a non-zero exit, an error naming the asset, cleanup of `.tmp` files, preservation of completed assets, and no success report.
7. **Unsupported platform**: run on an unsupported OS or architecture. Confirm immediate failure with the detected OS/architecture and supported scope.
8. **Public resolver**: from the maintainer's machine, check that a missing Cookie produces `LOGIN_REQUIRED`, a wrong access key produces `UNAUTHORIZED`, and a working Cookie resolves a valid share link. Confirm unrelated routes return 404 and repeated requests hit the rate limit. Do not record response bodies or tokens.
9. **Full Skill acceptance**: use `https://weixin.qq.com/sph/AHhuzPE3Pi` from the maintainer's machine through the public HTTP endpoint. Confirm media download, `note_materials.json`, OCR/ASR status and final `<slug>.md`. If the media is unavailable, use another valid link and record only the reason for substitution.
10. **Cookie update**: check that real terminal input does not echo. Replacement, failure exit and preservation of the old file are covered by [unit tests](../../../../../server/test_update_cookie.py).
11. **systemd lifecycle (test server only)**: install with private `config.json`; check migration from `client.json` preserves the access key and original file. Verify the resolver, gateway, Cookie oneshot and timer units with `systemd-analyze verify`. Installation enables maintenance and immediately checks Cookie, leaving the resolver/gateway stopped. Enable/start those two services, check the unauthenticated gateway returns 401, then resolve a real link. Stop services and timer, reboot, and verify disabled units stay disabled. Test enabled restart recovery separately. Reinstall with a changed interval and check the generated timer; preserve configuration, Cookie and browser profiles. Follow the [deployment guide](../../../../../docs/resolver-deployment.md).
12. **QQ headless login and maintenance**: use a dedicated persistent profile and private credentials. Verify fresh QQ password login, optional binding skip, Yuanbao Cookie extraction and full Go parsing through stdin. Close/reopen and verify reuse without passwords; a valid Cookie maintenance run must not start any browser. Simulate explicit expiry separately from network/5xx/interface errors. Check failed replacement preserves Cookie, unexpected login failure persists its pause across restart, and `--resume` allows a repaired attempt. See the [record](../../../../../docs/research/yuanbao-qq-login.md).
13. **Self-addressed mail (explicit send authorization required)**: verify QQ Mail password login and send one clearly marked test message only to the configured account itself. Confirm delivery; repeated errors must not duplicate notification attempts, a paused-login status must not create another alert, and a mail failure must not recurse or disclose credentials. Use mocks for routine regression, not live messages.

## Record

Record the date, platform, architecture, Python version, bootstrap result, HTTP/business status, pipeline result, artifact existence and a short error category. Do not commit downloaded runtime assets, user media, Yuanbao Cookies, full media URLs or sensitive logs. The shared access key in the public Skill is intentionally distributed and must not be treated as secret.

2026-09-29 acceptance: Windows x64, Python 3.13.14. The maintainer's machine received HTTP 200 / `OK` from the public resolver and completed the video pipeline: media, `note_materials.json`, OCR, ASR, and final Markdown present. Runtime verification passed with previously installed local FFmpeg and a model whose SHA-256 matched the manifest. A clean download of the newly pinned FFmpeg archive was not completed on this network. ASR produced low-quality text for this sample; the final note marks it as unreliable.

2026-10-20 QQ login experiment: Windows x64, headed Chromium/Playwright, existing Linux resolver via WSL. Password login and session reuse after browser restart both passed real parsing (`PARSE_OK`, exit 0); Yuanbao's parse API returned HTTP 200 / code 0. This covers resolver feasibility only, not another full Skill acceptance run. Details and unverified cases are in the [experiment record](../../../../../docs/research/yuanbao-qq-login.md).

2026-10-20 integrated headless checks: Windows x64 and WSL Ubuntu 26.04 x64, private Python 3.13.14, locked Playwright 1.64.0/Chromium. Fresh QQ password login and real Go parsing passed on both platforms; Windows profile reuse passed without another password attempt. One authorized self-addressed QQ Mail test was confirmed in Sent and received by the user. Offline regressions cover pause/resume, failure preservation, notification deduplication, and send confirmation fallback. Linux credential-free browser smoke passed locally; the new Actions job has not yet run on GitHub. No production deployment, remote systemd lifecycle, or new media/OCR/ASR acceptance was performed.

2026-10-20 Alibaba Cloud follow-up: after the user requested stopping local WSL tests, isolated SSH checks on Ubuntu 24.04 x64 passed 20 server regressions, two applicable uv checks, Chromium smoke, and remote parsing using an existing Cookie through stdin. Fresh Yuanbao and QQ Mail web login did not complete; a bounded Yuanbao diagnostic ended with `QQ_LOGIN_FAILED_OR_VERIFICATION_REQUIRED` without a confirmed visible challenge or password-error message. No further password retries or mail sends were performed, and temporary remote login state was removed. Cloud automatic-login acceptance is not passed; production configuration and services were not changed.
