# ADR 0001: Cross-platform runtime

Status: Accepted

## Decision

Python is the only canonical entry point for runtime business logic. The project supports Windows, macOS, and Linux x64, with runtime assets isolated under `.runtime/<os>-<arch>/`.

Platform launchers remain thin: they handle first-run bootstrapping when Python or uv is not installed, identify the platform, acquire uv, and forward commands to Python. Windows keeps a PowerShell compatibility layer; macOS and Linux use POSIX `sh` launchers.

The first run downloads and verifies private uv, Python, FFmpeg, and the model. The project does not reuse system Python or FFmpeg.

## Considered options

- **Make Python directly runnable everywhere**: rejected because the first run may not have a Python interpreter.
- **Keep PowerShell as the full orchestration layer**: rejected because it limits macOS/Linux and duplicates platform logic.
- **Thin platform launchers plus a canonical Python entry point**: accepted because it balances zero-preinstalled-runtime setup with cross-platform support.

## Consequences

- `.ps1` files no longer contain business logic; they are Windows compatibility entry points.
- The project must maintain per-platform uv and runtime asset manifests, SHA256 checks, and three-platform CI.
- The old single-directory Windows `.runtime/` layout is not migrated; the new bootstrap flow recreates the platform-specific layout.
- The current support scope is Windows/macOS/Linux x64, Python 3.13.14, and CPU-only inference. ARM64 and GPU inference are out of scope.
