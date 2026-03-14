---
description: Run tests and lint, then commit and push staged changes to main. Use when the user wants to commit and push their work.
disable-model-invocation: true
argument-hint: "[commit message]"
allowed-tools: Bash
---

# Git Commit and Push

Commit all pending changes and push to `main`. Stop and report if any step fails — do not skip failures.

## Steps

1. **Verify branch** — confirm current branch is `main` (`git branch --show-current`). Warn if not.

2. **Run tests** — `uv run pytest`. If any tests fail, stop and report which tests failed. Do not proceed.

3. **Run lint** — `uv run --extra lint ruff check .`. If errors are found, attempt to fix them with `uv run --extra lint ruff check --fix .`, then re-run to confirm clean. If unfixable errors remain, stop and report.

4. **Run type checks** — `uv run pyright` (if configured). Report but do not block on type errors unless `$ARGUMENTS` includes `--strict`.

5. **Stage changes** — `git add` specific files that are modified or untracked (avoid `git add -A` or `git add .` to prevent accidentally staging `.env`, secrets, or large binaries). List what is being staged.

6. **Write commit message** — if `$ARGUMENTS` is provided, use it as the commit message. Otherwise, inspect `git diff --cached` and write a concise message:
   - First line: imperative mood, ≤72 chars, no period (e.g. `Add ATR exit strategy with configurable multiplier`)
   - Body (if needed): explain *why*, not *what*

7. **Commit** — `git commit -m "<message>"` with `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` trailer.

8. **Push** — `git push origin main`. Report the result and the final commit hash.
