# Issue tracker: GitHub

Requirements, specifications, and bugs for this repository live in GitHub Issues. Use the `gh` CLI for all issue operations.

## Conventions

- Create an issue: `gh issue create --title "..." --body "..."`
- Read an issue: `gh issue view <number> --comments`
- List issues: `gh issue list --state open --json number,title,body,labels,comments`
- Apply or remove labels: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`
- Comment on an issue: `gh issue comment <number> --body "..."`
- Close an issue: `gh issue close <number> --comment "..."`

Infer the repository from `git remote -v`; `gh` does this automatically inside this clone.

## Pull requests

Pull requests are not a request surface for repository triage.

## Skill instructions

When a skill says to publish to the issue tracker, create a GitHub issue. When it says to fetch a relevant ticket, run `gh issue view <number> --comments`.
