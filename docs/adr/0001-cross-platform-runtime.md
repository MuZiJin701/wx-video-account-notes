# Cross-platform runtime

本项目将 Python 作为运行时业务逻辑的唯一规范入口，支持 Windows、macOS 和 Linux x64；保留极薄的平台启动器以解决首次运行时尚未安装 Python/uv 的引导问题。运行时资产按 OS 与架构隔离在 `.runtime/<os>-<arch>/` 下，首次运行下载并校验私有 uv、Python、FFmpeg 和模型；不复用系统 Python 或 FFmpeg。Windows 保留 PowerShell 兼容层，macOS/Linux 使用 POSIX `sh` 启动器，启动器只负责平台识别、获取 uv 和转发到 Python。

## Considered Options

- **全部改成可直接运行的 Python**：不可行，因为首次运行时可能没有 Python 解释器。
- **保留 PowerShell 作为完整编排层**：放弃，因为它限制 macOS/Linux，并重复承载平台逻辑。
- **平台薄启动器 + Python 规范入口**：采用，在免预装运行时与跨平台之间取得平衡。

## Consequences

- `.ps1` 不再承载业务逻辑，只作为 Windows 兼容入口。
- 需要维护各平台 uv 与运行时资产清单、SHA256 和三平台 CI 验证。
- 旧的单目录 Windows `.runtime/` 不迁移；按用户要求删除后由新初始化流程重建。
- 当前支持范围固定为 Windows/macOS/Linux x64、Python 3.13.14、CPU-only；ARM64 和 GPU 不属于本次范围。
