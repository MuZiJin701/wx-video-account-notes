# ADR 0006: Separate the client plugin from the repository

Status: Accepted (2026-11-18).

The repository contains a single client Skill and the separately deployed resolver. Using the repository root as the plugin root would bundle the resolver and development files. A local Codex 0.170.0 installation test also copied a Git-ignored fixture from the plugin root into the cache. [Codex packaging documentation](https://developers.openai.com/plugins/build/plugins#how-local-marketplaces-work)

Use `plugin/` as the Codex plugin root and `plugin/skills/wx-video-account-notes/` as the independently installable client Skill package. Keep one copy of the Skill for both the Codex Marketplace and standalone Skill installers. Keep the resolver, development documentation and repository test tooling outside the plugin package. Preserve the existing Marketplace, Plugin and Skill names and the Skill's path relative to the plugin root.

Move the client unit tests and acceptance materials to the repository's development tree. Keep the resolver unit tests in `server/`.

The layout migration covers repository files only.
