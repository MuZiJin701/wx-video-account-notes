# Agent instructions

User documentation: [README.md](README.md).

## Read when needed

- Before code exploration: `GLOSSARY.md`, relevant `docs/adr/` decisions, and `docs/agents/domain.md`.
- Before tracker operations: `docs/agents/issue-tracker.md` (GitHub Issues via `gh`).
- Before triage: `docs/agents/triage-labels.md` (canonical label mapping).
- Before resolver changes: `docs/research/wx-channels-architecture.md` and `docs/research/wx-channels-upstream.md`.

## Change policy

- Preserve unrelated changes; reuse existing code and conventions.
- Keep code, tests, and docs aligned; verify according to risk.
- Protect credentials, personal data, and sensitive logs.
- Require explicit authorization to push, message others, change permissions, delete important data, or affect production.
