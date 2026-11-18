# ADR 0007: Distribute one client Skill across Agent hosts

Status: Accepted (2026-11-18).

The [client plugin package boundary](0006-client-plugin-package-boundary.md) keeps the separately deployed resolver, repository tests and development documentation outside the installed plugin. Keep a single client Skill and runtime under `plugin/skills/wx-video-account-notes/` for all distribution channels.

Recommend the `skills` CLI for standalone Skill installation. Maintain native CLI plugin installation entry points for Codex, Claude Code, Antigravity, Grok Build and GitHub Copilot CLI. Share one repository-level Marketplace index at `.claude-plugin/marketplace.json` pointing to `./plugin` for Claude Code, Codex, Grok Build and Copilot CLI, while Antigravity installs `./plugin` directly from the repository URL. Inside `plugin/`, Codex, Antigravity, Grok Build and Copilot CLI share the Agent Plugins 1.0 manifest (`plugin/plugin.json`, with Codex presentation metadata under `extensions.com.openai`), and Claude Code uses `plugin/.claude-plugin/plugin.json`. All distribution channels deliver the same client package. Preserve explicit-only Skill invocation and the existing Codex installation identifiers.

Check the Marketplace index and package manifests in the repository test suite. Local client installation checks cover Codex, Claude Code and Antigravity; the maintainer can verify Grok Build and Copilot CLI on the intended client versions.
