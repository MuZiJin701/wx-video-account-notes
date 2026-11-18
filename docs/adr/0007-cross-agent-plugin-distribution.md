# ADR 0007: Distribute one client Skill across Agent hosts

Status: Accepted (2026-11-18).

The [client plugin package boundary](0006-client-plugin-package-boundary.md) keeps the separately deployed resolver, repository tests and development documentation outside the installed plugin. Keep a single client Skill and runtime under `plugin/skills/wx-video-account-notes/` for all distribution channels.

Recommend the `skills` CLI for standalone Skill installation. Maintain native plugin installation entry points for Codex, Claude Code, Grok Build, Cursor and GitHub Copilot CLI. Each host has its own documented Marketplace index. Codex and Copilot CLI share the Agent Plugins 1.0 manifest, with Codex presentation metadata under `extensions.com.openai`. Claude Code, Grok Build and Cursor also have their native package manifests. All indexes point to the same client package. Preserve explicit-only Skill invocation and the existing Codex installation identifiers.

Check all five indexes and package manifests in the repository test suite. Local client installation checks cover Codex and Claude Code. The maintainer can verify Grok Build, Cursor and Copilot CLI on the intended client versions.
