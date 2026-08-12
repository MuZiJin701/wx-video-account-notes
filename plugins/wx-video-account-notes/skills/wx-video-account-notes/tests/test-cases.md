# Manual smoke test checklist

This is the release checklist for real bootstrap and end-to-end processing. It is not the automated `unittest` entry point. Automated tests run in the locked uv environment and do not contact external download services.

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

## Record

Record the date, platform, architecture, Python version, bootstrap result, pipeline result, and a short failure summary. Do not commit downloaded runtime assets, user media, or sensitive logs.
