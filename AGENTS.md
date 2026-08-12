# Agent Instructions / Agent 协作说明

本文件记录本仓库对编码代理的通用约定。This file records repository-wide guidance for coding agents.

## Agent skills

### Issue tracker

Issues for this repo live in GitHub Issues and are managed with `gh`. See `docs/agents/issue-tracker.md`.

本项目使用 GitHub Issues 管理需求与问题，代理应通过 `gh` CLI 操作。详见 `docs/agents/issue-tracker.md`。

### Triage labels

Use the canonical triage labels mapped in `docs/agents/triage-labels.md`.

使用 `docs/agents/triage-labels.md` 中映射的标准 triage 标签。

### Domain docs

This is a single-context repo. Read `CONTEXT.md` and relevant ADRs under `docs/adr/`. See `docs/agents/domain.md`.

这是单上下文仓库。工作前读取根目录 `CONTEXT.md` 以及 `docs/adr/` 下相关 ADR。详见 `docs/agents/domain.md`。
