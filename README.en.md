# wx-video-account-notes

Turn one WeChat Channels share link into structured note materials for an agent, then produce a Markdown note.

[中文 README](README.md) · [![Tests](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml/badge.svg)](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml)

## Why use it

- **One link in**: automatically handles video and image posts.
- **Structured handoff**: preserves the raw response, metadata, OCR, ASR, visual frames, and processing status for the agent.
- **Inspectable results**: failures are recorded explicitly instead of being presented as successful output.
- **Cross-platform and CPU-first**: supports Windows x64, Intel macOS x64, and Linux x64 without GPU, CUDA, or system FFmpeg setup.
- **Self-contained runtime**: private Python, uv, FFmpeg, and models are cached per platform and reused after bootstrap.

## Current resolver status

As of 2026-09-29, the default resolver returns `401 unauthorized` for share links, so a successful installation does not yet mean the link-to-note flow works. The resolver is rejecting access; this does not establish that the share link is invalid. The shared self-hosted resolver and local end-to-end acceptance test are still planned in [spec issue #4](https://github.com/MuZiJin701/wx-video-account-notes/issues/4).

## Quick start

### Install

```sh
npm install -g skills
skills add https://github.com/MuZiJin701/wx-video-account-notes.git -g -y
```

The first run downloads the private runtime, locked dependencies, FFmpeg, and model for the current platform. Allow network access and enough disk space.

### Codex plugin (optional)

You can also install it through the Codex plugin marketplace:

```sh
codex plugin marketplace add https://github.com/MuZiJin701/wx-video-account-notes.git
codex plugin add wx-video-account-notes@wx-video-account-notes-dev
```

With `cc-switch`, paste the repository URL directly.

### Process a link

Send this request with a real share link to your agent:

```text
Process this WeChat Channels share link and create a note:
https://weixin.qq.com/sph/your_share_id_here
```

To choose an output directory, add a path:

```text
Process this WeChat Channels link into D:\notes\wx:
https://weixin.qq.com/sph/your_share_id_here
```

## Output

```text
<output-dir>/
  <slug>.mp4          # video posts only
  note_materials.json # structured handoff for the agent
  raw.json            # raw resolver response
  ocr.txt             # OCR text
  asr.txt             # ASR text; empty for image posts
  ocr_frames/         # subtitle crops for video OCR
  frames/             # visual frames or source images
  audio/              # extracted audio for video posts
  <slug>.md           # final note written by the agent
```

Image posts skip video, audio, and ASR. Source images go to `frames/` and may be exposed as `visual_frames` to vision-capable models.

## Support

| Item | Scope |
| --- | --- |
| Operating systems | Windows x64, Intel macOS x64, Linux x64 |
| Python | 3.13.14, private project runtime |
| Inference | CPU-only, faster-whisper tiny |
| Input | `https://weixin.qq.com/sph/...` share links |
| Services | WeChat Channels resolver, GitHub Releases, Hugging Face |

ARM64, GPU inference, and offline first-time bootstrap are not currently supported.

## Development

```sh
cd plugins/wx-video-account-notes/skills/wx-video-account-notes
uv sync --locked
uv run --locked python -m unittest discover -s runtime/tests
```

Real bootstrap and end-to-end processing are manual smoke tests:

```powershell
pwsh -File scripts\bootstrap.ps1
pwsh -File scripts\verify_runtime.ps1
pwsh -File scripts\invoke_pipeline.ps1 -ShareUrl "https://weixin.qq.com/sph/your_share_id_here"
```

```sh
sh scripts/bootstrap.sh
sh scripts/verify_runtime.sh
sh scripts/invoke_pipeline.sh --share-url "https://weixin.qq.com/sph/your_share_id_here"
```

## Documentation

- [Skill guide](plugins/wx-video-account-notes/skills/wx-video-account-notes/SKILL.md)
- [Repository map](目录说明.md)
- [Domain glossary](CONTEXT.md)
- [Architecture decisions](docs/adr/)
- [WeChat Channels acquisition architecture](docs/research/wx-channels-architecture.md)
- [Self-hosted resolver spec and acceptance criteria](https://github.com/MuZiJin701/wx-video-account-notes/issues/4)
- [Tests and evaluation](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md)
- [Changelog](CHANGELOG.md)

## Contributing and license

Read [AGENTS.md](AGENTS.md) before contributing. Use GitHub Issues for requests and bug reports. This project is released under the MIT License; see [LICENSE](LICENSE).
