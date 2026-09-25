---
name: commit-and-push-all-changes
description: "Use when: commit and push all changes, save all work, stage and push repo changes, git add . and push to remote, create a commit for the current branch."
---

# Commit and Push All Changes

## Use when
- The user asks to commit and push all changes.
- The user wants the current work saved to git and uploaded to the remote branch.
- The repo has local edits that should be staged, committed, and pushed.

## Standard workflow
1. Check repository status with `git status --short`.
2. If there are no modified files, report that there are no changes to commit.
3. Stage everything with `git add .`.
4. Create a concise commit message describing the change.
5. Run `git commit -m "<short summary>"`.
6. Push the branch with `git push`.
7. Report the commit hash and push confirmation.

## Guardrails
- Do not discard user work or reset the repo unless explicitly requested.
- Preserve the current branch and remote selection.
- Keep commit messages short and descriptive.
- If there is a merge conflict, missing remote, or auth issue, stop and report the precise error.

## Example command sequence
```bash
git status --short
git add .
git commit -m "Update dashboard and historical IPO data"
git push
```

## Output expectations
- Confirm whether there were changes to commit.
- Present the commit hash if created.
- Confirm whether the push succeeded.
- If push fails, quote the exact Git error and stop.
