# ADR 0002: Test strategy

Status: Accepted

## Decision

Use three test layers:

1. Fast unit tests verify Python business rules and platform path contracts.
2. CI runs the full `unittest` suite in the locked uv/Python 3.13.14 environment without external downloads.
3. Controlled manual smoke tests verify real bootstrap, FFmpeg, model download, and end-to-end processing.

This keeps cross-platform code repeatable without making network access or large model assets an implicit dependency of every commit.

## Canonical vocabulary

- **Unit test**: offline test of one module or pure Python behavior; it does not download assets or call real FFmpeg or models.
- **Integration test**: test of multiple runtime modules in the locked environment; it verifies parameters, file layout, and collaboration without external services.
- **Smoke test**: controlled real-run check of bootstrap and end-to-end processing; it is not a default push/PR gate.
- **Platform contract**: the stable agreement covering OS, architecture, runtime directory, executable names, and unsupported-platform failures.

## Rules

- Keep the standard-library `unittest`; do not add a test framework.
- Run tests with `uv run --locked python -m unittest discover -s runtime/tests`.
- Do not commit real video, audio, model, or FFmpeg binaries. Use synthetic inputs, temporary directories, mocks, and small in-memory images.
- Test bootstrap downloads, SHA256 checks, resume behavior, and extraction with local fixtures or mocks; do not contact GitHub, Hugging Face, or evermeet.
- CI covers Windows x64, Intel macOS x64, and Linux x64. ARM and real model inference are not promised.
- Real bootstrap and end-to-end processing are covered by the separate manual smoke checklist.
- A bootstrap failure must return non-zero, identify the failed asset, clean `.tmp` files, preserve completed assets, and avoid reporting success.

## Consequences

- Tests that assert PowerShell-only paths or the old single-directory `.runtime/` layout are obsolete and must use platform-neutral contracts.
- `tests/test-cases.md` is the manual smoke checklist, not the automated test entry point.
- If system Python lacks project dependencies, a direct `python -m unittest` run is not valid acceptance; use the locked uv environment.
