# wx-video-account-notes

Download WeChat Channels videos or image posts from a share link, extract OCR/ASR note materials, and have an agent write a Markdown note.

[中文 README](README.md) · [![Tests](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml/badge.svg)](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml)

> **Playwright login exploration paused (2026-10-20):** `codex/explore-qq-yuanbao-login` preserves experimental QQ password login code for Yuanbao and QQ Mail, diagnostics, and research. Full cloud login acceptance has not passed, and the work is not merged into `main`. In the [pure HTTP account prechecks](docs/research/yuanbao-qq-login.md#纯-http-账号预检查2026-10-21) added on 2026-10-21, both sites waived CAPTCHA locally but required it on Alibaba Cloud; no password was submitted or complete login verified. Resume browser exploration only at the user's explicit request. See [`main`](https://github.com/MuZiJin701/wx-video-account-notes/tree/main) for released behavior and deployment.

## See it in action

![Sending a WeChat Channels share link in Codex and generating a Markdown note](docs/images/使用过程.png)

![Locally saved video, Markdown notes, reference frames, and OCR/ASR note materials](docs/images/产物.png)

OCR succeeded in this example; ASR recognized no speech. Notes flag failures and uncertainty.

## Get started

Supports Windows x64, Intel macOS x64, and Linux x64. The first run downloads a private Python runtime, dependencies, FFmpeg, and models from sources including GitHub Releases and Hugging Face. It needs network access and disk space; later runs reuse them.

An available system uv (0.11.25 or newer) is preferred. Missing or incompatible installations fall back to the existing pinned, checksum-verified project-private uv.

### 1. Install the Skill

```sh
npm install -g skills
skills add https://github.com/MuZiJin701/wx-video-account-notes.git -g -y
```

Codex users can also install the plugin:

```sh
codex plugin marketplace add https://github.com/MuZiJin701/wx-video-account-notes.git
codex plugin add wx-video-account-notes@wx-video-account-notes-dev
```

With `cc-switch`, enter the repository URL.

### 2. Send a share link

By default, the Skill uses the maintainer's resolver. You do not need a server or credentials. Send a real link to your agent:

```text
Download the content from this WeChat Channels share link and write a note:
https://weixin.qq.com/sph/your_share_id_here
```

To choose an output directory, include it in the request, for example, “Save this note under D:\notes\wx.”

### Want to use your own server?

Use the [self-hosting guide on `main` (Chinese)](https://github.com/MuZiJin701/wx-video-account-notes/blob/main/docs/resolver-deployment.md), which uses manual Yuanbao Cookie maintenance. Password login, daily maintenance, and QQ Mail alerts on this branch are paused experiments. The [branch guide (Chinese)](docs/resolver-deployment.md) preserves historical checks and a deployment draft; do not execute them while exploration is paused.

At pause time, both direct Alibaba Cloud login checks required image-selection CAPTCHAs in headed and headless modes. Agent-guided browser clicks passed one Yuanbao challenge, but QQ Mail verification and full cloud login have not passed; general image recognition is not integrated. Network exit is the strongest observed factor, while Tencent's exact triggering rule remains unknown. Green CI and `BROWSER_SMOKE_OK` do not establish account login. See the [pause status and research record (Chinese)](docs/research/yuanbao-qq-login.md#探索暂停与分支隔离2026-10-20).

## Output files

```text
<output-dir>/
  <slug>.mp4          # video posts only
  note_materials.json # structured materials and processing status
  raw.json            # raw resolver response
  ocr.txt             # text recognized from images
  asr.txt             # speech transcript; empty for image posts
  ocr_frames/         # video subtitle crops
  frames/             # video reference frames or source images
  audio/              # video audio
  <slug>.md           # final note
```

Image posts have no video or audio. Vision-capable agents also read images in `frames/` when writing the note. Failures appear in the materials instead of being reported as success.

## How it works and current limits

- The server only resolves share links. Media download, OCR, ASR, and note writing run locally; no GPU or system FFmpeg is required.
- The default resolver uses public HTTP, so share links and results travel in plaintext. Its shared access key ships with the public Skill and is not secret. The service handles at most 30 requests per minute across all users.
- The maintainer updates the default resolver's Yuanbao login. Self-hosting on `main` uses manual Cookie maintenance and can use HTTPS. Automatic maintenance and mail alerts on this branch remain unaccepted, paused experiments.
- ARM64, GPU inference, and offline first-time setup are not supported. The private Python version is 3.13.14; ASR uses faster-whisper tiny on CPU.

## Development

```sh
cd plugins/wx-video-account-notes/skills/wx-video-account-notes
uv sync --locked
uv run --locked python -m unittest discover -s runtime/tests
```

Run server tests from the repository root with `python3 -m unittest discover -s server` (standard library only). For real bootstrap and end-to-end checks, use the [manual acceptance checklist](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md).

GitHub Actions runs three-platform unit tests and a credential-free Linux Chromium launch, JavaScript, and profile-persistence smoke check, with manual dispatch support. Personal credentials are not uploaded to CI. The [historical branch checks (Chinese)](docs/resolver-deployment.md#0-先验收开发分支) retain the login entry points; do not run real login, mail delivery, or experimental deployment while exploration is paused. Offline tests and credential-free CI do not establish successful cloud authentication.

## More documentation

- [Self-hosting and troubleshooting (Chinese)](docs/resolver-deployment.md)
- [QQ login, Cookie maintenance, and mail notification checks (Chinese)](docs/research/yuanbao-qq-login.md)
- [Skill execution guide (Chinese)](plugins/wx-video-account-notes/skills/wx-video-account-notes/SKILL.md)
- [Repository map (Chinese)](目录说明.md) · [Domain glossary (Chinese)](GLOSSARY.md) · [Architecture decisions](docs/adr/)
- [Resolver architecture (Chinese)](docs/research/wx-channels-architecture.md) · [Tests and evaluation](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md) · [Changelog](CHANGELOG.md)

Read [AGENTS.md](AGENTS.md) before contributing. Use GitHub Issues for requests and bugs. Licensed under [MIT](LICENSE).
