# Issue tracker: GitHub

需求、规格和问题统一记录在 GitHub Issues。Requirements, specs, and bugs live in GitHub Issues.

Issues and specs for this repo live as GitHub Issues. Use the `gh` CLI for all operations。

本仓库的 issue 和规格说明存放在 GitHub Issues 中，所有相关操作使用 `gh` CLI。

## Conventions / 约定

- Create an issue / 创建 issue: `gh issue create --title "..." --body "..."`
- Read an issue / 读取 issue: `gh issue view <number> --comments`
- List issues / 列出 issue: `gh issue list --state open --json number,title,body,labels,comments`
- Comment on an issue / 评论 issue: `gh issue comment <number> --body "..."`
- Apply or remove labels / 添加或移除标签: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- Close an issue / 关闭 issue: `gh issue close <number> --comment "..."`

Infer the repository from `git remote -v`; `gh` does this automatically inside this clone。

## Pull requests as a triage surface / PR 是否进入 triage

**PRs as a request surface: no.**

外部 Pull Request 不作为本项目的 triage 请求入口。

## When a skill says “publish to the issue tracker” / 发布到 issue tracker

Create a GitHub issue / 创建 GitHub issue。

## When a skill says “fetch the relevant ticket” / 获取相关 ticket

Run `gh issue view <number> --comments` / 执行 `gh issue view <number> --comments`。
