# Test Cases

1. Basic share link with default output directory, using `https://weixin.qq.com/sph/AClgYpX4KB`, and verify the pipeline output contains `<slug>.mp4`, `note_materials.json`, `raw.json`, `ocr.txt`, `asr.txt`, `frames/`, and `audio/`.
2. Share link with explicit output directory, and verify the same material files are written there and are ready for the current agent / model to produce the default final `<slug>.md` unless the user explicitly skips notes.
3. Fresh machine path where `uv` is missing and bootstrap must download it, then continue into the normal flow: the `.runtime` directory is created, required assets are prepared, and the output contains the material set.
4. Asset download failure produces a clear error that identifies the failing asset or command, and the run stops before claiming success for either the material set or the final note.
