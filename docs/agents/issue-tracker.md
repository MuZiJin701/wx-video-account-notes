# Issue tracker: GitHub

Requirements, specifications, and bugs for this repository live in GitHub Issues. Use the `gh` CLI for all issue operations.

## Conventions

- Create an issue: `gh issue create --title "..." --body "..."`.
- Read an issue: `gh issue view <number> --json number,title,body,labels,comments`.
- List issues: `gh issue list --state open --json number,title,body,labels,comments`. Apply appropriate `--label` and `--state` filters; use `--limit` or pagination when the full queue is needed.
- Apply or remove labels: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`.
- Comment on an issue: `gh issue comment <number> --body "..."`.
- Close an issue: `gh issue close <number> --comment "..."`.
- Make a child issue: `gh issue create --parent <parent-number> ...`, or `gh issue edit <parent-number> --add-sub-issue <child-number>` (`gh` 2.94+). If sub-issues are unavailable, add the child to a task list in the parent body and put `Part of #<parent-number>` at the top of the child body.

For multiline issue bodies and comments, write the exact Markdown to a temporary file and use `--body-file <path>`; preserve newlines and literal text.

Infer the repository from `git remote -v`; `gh` does this automatically inside this clone.

## Pull requests as a triage surface

**PRs as a request surface: no.**

GitHub shares one number space across issues and PRs. Resolve a bare `#42` with `gh pr view 42`, falling back to `gh issue view 42`. PRs are outside automatic triage discovery; an explicitly named PR can still be handled.

## Skill instructions

When a skill says to publish to the issue tracker, create a GitHub issue. When it says to fetch a relevant ticket, read the issue body, labels, and comments as above.

## Wayfinding operations

Used by `/wayfinder`. The map is a single issue with child issues as tickets.

- Map: an issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body.
- Child ticket: an issue linked to the map as a sub-issue, with the task-list fallback above. Labels: `wayfinder:<type>` (`research`, `prototype`, `grilling`, or `task`). Once claimed, assign it to the driving developer.
- Blocking: use GitHub's native issue dependencies, e.g. `gh issue edit <child-number> --add-blocked-by <blocker-number>` when supported by the installed CLI. Check open blockers with `gh api repos/<owner>/<repo>/issues/<child-number> --jq .issue_dependencies_summary.blocked_by`. If dependencies are unavailable, put `Blocked by: #<number>, #<number>` at the top of the child body and check each blocker's state.
- Frontier query: list all of the map's open children, scoped to its sub-issues or task list. Exclude tickets with open blockers or an assignee; choose the first remaining ticket in map order.
- Claim: `gh issue edit <number> --add-assignee "@me"`.
- Resolve: comment with the answer, close the child issue, then append a gist and link to the map's Decisions-so-far.
