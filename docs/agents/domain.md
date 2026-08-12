# Domain Docs / 领域文档

How engineering skills should consume this repo's domain documentation。
工程 skill 探索本仓库时应遵循以下领域文档约定。

## Before exploring, read these / 探索前读取

- `CONTEXT.md` at the repo root, if it exists / 根目录的 `CONTEXT.md`（如存在）
- Relevant ADRs under `docs/adr/`, if they exist / `docs/adr/` 下相关 ADR（如存在）

If these files do not exist, proceed silently. Do not create them upfront; create them when domain decisions or terminology are actually established。

如果这些文件不存在，直接继续，不要提前创建占位文件；只有在确立领域决策或术语时再创建。

## File structure / 文件结构

This is a single-context repo / 本仓库采用单上下文结构：

```text
/
├── CONTEXT.md
├── docs/
│   ├── agents/
│   └── adr/
└── plugins/
```

## Use the glossary's vocabulary / 使用术语表

When naming a domain concept in an issue, proposal, refactor, or test, use the term defined in `CONTEXT.md`。在 issue、提案、重构或测试中命名领域概念时，使用 `CONTEXT.md` 定义的术语。

If the concept is not defined yet, reconsider inventing a synonym and record the gap for domain modeling。

如果术语尚未定义，先确认是否真的需要新增概念，并将缺口交给 domain modeling 流程。

## Flag ADR conflicts / 标记 ADR 冲突

If proposed work contradicts an existing ADR, surface the conflict explicitly instead of silently overriding it。

如果提议的工作与现有 ADR 冲突，必须明确指出，不要静默覆盖既有决策。
