# Test Cases

1. Video share link with default output directory, using `https://weixin.qq.com/sph/AybwTXRwkt`, and verify the pipeline output contains `<slug>.mp4`, `note_materials.json`, `raw.json`, `ocr.txt`, `asr.txt`, `ocr_frames/`, `frames/`, and `audio/`. Verify `ocr_frames/` contains OCR subtitle crops, `frames/` contains about 5 visual reference frames, and `note_materials.json` includes `visual_frames`.
2. Image-feed share link with default output directory, using `https://weixin.qq.com/sph/AeGgo9k3KL`, and verify the pipeline downloads images into `frames/`, skips video/audio/ASR extraction, writes empty `asr.txt`, marks ASR as `图文动态无音频`, and includes `visual_frames`.
3. Share link with explicit output directory, and verify the same material files are written there and are ready for the current agent / model to produce the default final `<slug>.md` unless the user explicitly skips notes.
4. Fresh machine path where private `uv` is missing and bootstrap must download `uv 0.11.25`, install Python `3.13.14`, then run `uv sync --locked`; verify `.runtime` is created, required assets are prepared, and `.runtime/` is not tracked by git.
5. Asset download failure produces a clear error that identifies the failing asset or command, and the run stops before claiming success for either the material set or the final note.
