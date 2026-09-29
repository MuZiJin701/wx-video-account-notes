# Agent instructions

This file defines repository-wide guidance for coding agents. User-facing documentation is in `README.md`.

## Issue tracker

Issues for this repository live in GitHub Issues and are managed with `gh`. See `docs/agents/issue-tracker.md`.

## Triage labels

Use the canonical triage labels mapped in `docs/agents/triage-labels.md`.

## Domain docs

This repository has a single context. Read `CONTEXT.md` and relevant ADRs under `docs/adr/` before exploring the code. See `docs/agents/domain.md`.

For WeChat Channels share-link resolution work, read `docs/research/wx-channels-architecture.md` and `docs/research/wx-channels-upstream.md` before changing the resolver.

## Change policy

- Preserve unrelated user changes.
- Reuse existing code and project conventions before adding abstractions.
- Keep implementation, tests, and documentation aligned.
- Do not expose passwords, tokens, API keys, personal data, or sensitive logs.
- Do not push code, send messages, modify permissions, delete important data, or affect production resources without explicit authorization.
- Run tests, type checks, builds, or manual checks appropriate to the risk of the change.
