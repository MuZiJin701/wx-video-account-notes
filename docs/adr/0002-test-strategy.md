# Test strategy

本项目采用三层测试策略：快速单元测试验证 Python 业务规则与平台路径契约；CI 集成测试在锁定的 uv/Python 3.13.14 环境中运行完整 `unittest`，但不访问外部下载服务；受控 smoke test 验证真实 bootstrap、FFmpeg、模型下载和端到端处理。测试策略的目标是让跨平台代码可重复验证，同时不让网络和大模型资源成为每次提交的隐性依赖。

## Status

Accepted.

## Canonical test vocabulary

- **单元测试（unit test）**：不联网、不下载运行时资产、不调用真实 FFmpeg 或模型，验证单个模块或纯 Python 行为。
- **集成测试（integration test）**：在项目锁定依赖环境中运行多个 runtime 模块，验证参数、文件布局和模块协作；仍不依赖外部供应商服务。
- **Smoke test**：受控的真实运行检查，验证首次初始化和端到端处理是否能工作；不作为每次 push/PR 的默认门禁。
- **平台契约（platform contract）**：OS、架构、运行时目录、可执行文件命名和不支持平台的失败行为组成的稳定约定。

## Decisions

- 保留标准库 `unittest`，不新增测试框架。
- 测试通过锁定环境运行：`uv run --locked python -m unittest discover -s runtime/tests`。
- 不提交真实视频、音频、模型或 FFmpeg 二进制；测试使用合成输入、临时目录、mock 和小型内存图片。
- bootstrap 的下载、SHA256、断点恢复和解压测试使用本地 fixture 或 mock，不访问 GitHub、Hugging Face 或 evermeet。
- CI 使用 Windows x64、macOS Intel x64 和 Linux x64 矩阵；不承诺 ARM 或真实模型推理。
- 真实 bootstrap 和端到端处理通过独立手动 smoke test 验证。
- bootstrap 失败必须返回非零状态、指出失败资产、清理 `.tmp` 文件、保留已完成资产，且不生成成功状态。

## Consequences

- 现有 `runtime/tests/test_bootstrap.py` 中对 PowerShell、Windows 专用路径和单目录 `.runtime/` 的断言属于旧契约，后续实现时必须改为平台无关测试。
- `tests/test-cases.md` 是人工 smoke test 清单，不是自动测试入口。
- 系统 Python 缺少项目依赖时，不能把本地直接运行 `python -m unittest` 视为有效验收；应使用锁定的 uv 环境。
