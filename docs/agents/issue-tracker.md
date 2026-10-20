# Issue tracker: GitHub

Use GitHub Issues via `gh` for requirements, specs, and bugs. The repository is inferred from `git remote -v` inside this clone.

## Conventions

- Read: `gh issue view <number> --json number,title,body,labels,comments`.
- List: `gh issue list --state open --json number,title,body,labels,comments`; filter by label/state and use `--limit` or pagination for a full queue.
- Write: `gh issue create --title "..." --body "..."`, `gh issue comment <number> --body "..."`, `gh issue close <number> --comment "..."`.
- Labels: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`.
- Children: `gh issue create --parent <parent-number> ...` or `gh issue edit <parent-number> --add-sub-issue <child-number>` (`gh` 2.94+). Fallback: parent task list plus `Part of #<parent-number>` atop the child body.

For multiline issue bodies and comments, write the exact Markdown to a temporary file and use `--body-file <path>`; preserve newlines and literal text.

## Pull requests as a triage surface

PRs are excluded from automatic request discovery; explicitly named PRs may be handled. Resolve bare `#42` with `gh pr view 42`, falling back to `gh issue view 42`, because both share one number space. Skill references to publishing/fetching tickets mean creating/reading Issues, including labels and comments.

## Wayfinding operations

Used by `/wayfinder`. The map is a single issue with child issues as tickets.

- Map: an issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body.
- Child ticket: an issue linked to the map as a sub-issue, with the task-list fallback above. Labels: `wayfinder:<type>` (`research`, `prototype`, `grilling`, or `task`). Once claimed, assign it to the driving developer.
- Blocking: use GitHub's native issue dependencies, e.g. `gh issue edit <child-number> --add-blocked-by <blocker-number>` when supported by the installed CLI. Check open blockers with `gh api repos/<owner>/<repo>/issues/<child-number> --jq .issue_dependencies_summary.blocked_by`. If dependencies are unavailable, put `Blocked by: #<number>, #<number>` at the top of the child body and check each blocker's state.
- Frontier query: list all of the map's open children, scoped to its sub-issues or task list. Exclude tickets with open blockers or an assignee; choose the first remaining ticket in map order.
- Claim: `gh issue edit <number> --add-assignee "@me"`.
- Resolve: comment with the answer, close the child issue, then append a gist and link to the map's Decisions-so-far.
