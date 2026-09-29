# Manual smoke test checklist

This is the release checklist for real bootstrap and end-to-end processing. It is not the automated `unittest` entry point. Automated tests run in the locked uv environment and do not contact external download services.

The maintainer-hosted default resolver was delivered under [issue #4](https://github.com/MuZiJin701/wx-video-account-notes/issues/4). For optional user hosting, set both `WX_VIDEO_ACCOUNT_RESOLVE_API` and `WX_VIDEO_ACCOUNT_RESOLVE_KEY` to the user's own service before running the resolver and full Skill checks below. The September 29 acceptance record covers the default service only.

## Prerequisites

- Run on Windows x64, Intel macOS x64, or Linux x64.
- Allow access to the WeChat Channels resolver, GitHub Releases, and Hugging Face.
- Use a fresh skill directory, or back up and remove the platform-specific `.runtime/<os>-<arch>/` before testing first-run behavior.

## Cases

1. **Video post, default output**: use `https://weixin.qq.com/sph/AybwTXRwkt`. Confirm the output contains `<slug>.mp4`, `note_materials.json`, `raw.json`, `ocr.txt`, `asr.txt`, `ocr_frames/`, `frames/`, and `audio/`; confirm that `note_materials.json` contains `visual_frames`.
2. **Image post, default output**: use `https://weixin.qq.com/sph/AeGgo9k3KL`. Confirm images are written to `frames/`, video/audio/ASR are skipped, `asr.txt` is empty, and the result records that the image post has no audio.
3. **Custom output directory**: confirm all note materials are written to the requested directory and the agent can create the final `<slug>.md` beside them.
4. **First bootstrap**: confirm creation of `.runtime/<os>-<arch>/`, download and verification of private uv, Python, FFmpeg, and model, followed by locked dependency sync.
5. **Repeat bootstrap**: confirm verified assets are reused rather than downloaded again and different platform directories are not reused.
6. **Failure recovery**: simulate an asset download, verification, or extraction failure. Confirm a non-zero exit, an error naming the asset, cleanup of `.tmp` files, preservation of completed assets, and no success report.
7. **Unsupported platform**: run on an unsupported OS or architecture. Confirm immediate failure with the detected OS/architecture and supported scope.
8. **Public resolver**: from the maintainer's machine, check that a missing Cookie produces `LOGIN_REQUIRED`, a wrong access key produces `UNAUTHORIZED`, and a working Cookie resolves a valid share link. Confirm unrelated routes return 404 and repeated requests hit the rate limit. Do not record response bodies or tokens.
9. **Full Skill acceptance**: use `https://weixin.qq.com/sph/AHhuzPE3Pi` from the maintainer's machine through the public HTTP endpoint. Confirm media download, `note_materials.json`, OCR/ASR status and final `<slug>.md`. If the media is unavailable, use another valid link and record only the reason for substitution.
10. **Cookie update**: with a temporary file and placeholder Cookies, confirm no echo, successful replacement, non-zero exit and preservation of the old file after a failed verification.

## Record

Record the date, platform, architecture, Python version, bootstrap result, HTTP/business status, pipeline result, artifact existence and a short error category. Do not commit downloaded runtime assets, user media, Yuanbao Cookies, full media URLs or sensitive logs. The shared access key in the public Skill is intentionally distributed and must not be treated as secret.

2026-09-29 acceptance: Windows x64, Python 3.13.14. The maintainer's machine received HTTP 200 / `OK` from the public resolver and completed the video pipeline: media, `note_materials.json`, OCR, ASR, and final Markdown present. Runtime verification passed with previously installed local FFmpeg and a model whose SHA-256 matched the manifest. A clean download of the newly pinned FFmpeg archive was not completed on this network. ASR produced low-quality text for this sample; the final note marks it as unreliable.
