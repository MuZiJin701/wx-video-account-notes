# wx-video-account-notes

Give an agent one WeChat Channels share link to create inspectable note materials and a Markdown note. Supports video and image posts.

[中文 README](README.md) · [![Tests](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml/badge.svg)](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml)

## Get started

Supports Windows x64, Intel macOS x64, and Linux x64. The first run downloads a private Python runtime, dependencies, FFmpeg, and models from sources including GitHub Releases and Hugging Face. It needs network access and disk space; later runs reuse them.

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
Process this WeChat Channels share link and write a note:
https://weixin.qq.com/sph/your_share_id_here
```

To choose an output directory, include it in the request, for example, “Save this note under D:\notes\wx.”

### Want to use your own server?

Follow the [self-hosting guide (Chinese)](docs/resolver-deployment.md) to build, install, and start the resolver. Then configure your own endpoint and access key for the agent. A failure of your server does not fall back to the default resolver.

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
- The maintainer updates the default resolver's Yuanbao login. Its processes currently require manual startup. Self-hosting can use an HTTPS front end; see the [deployment guide (Chinese)](docs/resolver-deployment.md).
- ARM64, GPU inference, and offline first-time setup are not supported. The private Python version is 3.13.14; ASR uses faster-whisper tiny on CPU.

## Development

```sh
cd plugins/wx-video-account-notes/skills/wx-video-account-notes
uv sync --locked
uv run --locked python -m unittest discover -s runtime/tests
```

Real bootstrap and end-to-end processing require manual checks:

```powershell
pwsh -File scripts\bootstrap.ps1
pwsh -File scripts\verify_runtime.ps1
pwsh -File scripts\invoke_pipeline.ps1 -ShareUrl "https://weixin.qq.com/sph/your_share_id_here"
```

On macOS/Linux, use `sh scripts/bootstrap.sh`, `sh scripts/verify_runtime.sh`, and `sh scripts/invoke_pipeline.sh --share-url "https://weixin.qq.com/sph/your_share_id_here"`.

## More documentation

- [Self-hosting and troubleshooting (Chinese)](docs/resolver-deployment.md)
- [Skill execution guide (Chinese)](plugins/wx-video-account-notes/skills/wx-video-account-notes/SKILL.md)
- [Repository map (Chinese)](目录说明.md) · [Domain glossary (Chinese)](CONTEXT.md) · [Architecture decisions](docs/adr/)
- [Resolver architecture (Chinese)](docs/research/wx-channels-architecture.md) · [Tests and evaluation](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md) · [Changelog](CHANGELOG.md)

Read [AGENTS.md](AGENTS.md) before contributing. Use GitHub Issues for requests and bugs. Licensed under [MIT](LICENSE).
