---
name: commit-push
description: Commit work to main and push it — runs the full CI-parity gate first, keeps the pre-commit hook's write-mode ruff format from desyncing the index, and verifies the tree is clean afterwards. Use when the user asks to commit, push, or ship changes.
---

# Commit and Push to main

The local `.git/hooks/pre-commit` hook runs only `ruff format` and `mypy` over `turtlex/ scripts/`.
CI (`.github/workflows/build.yml`, on push to `main`) also runs `ruff check`, markdownlint and
`pytest` — so a commit can clear the hook and still break the build. These steps close that gap.

1. **Run the gate**, in CI's order, so the first failure is the one CI would report:

   ```bash
   uv run ruff check turtlex/ scripts/    # the hook does NOT run this
   uv run ruff format turtlex/ scripts/   # write mode, deliberately — see step 2
   uv run mypy                            # no arguments, per CLAUDE.md
   uv run pytest
   npx markdownlint-cli2                  # only if a tracked .md changed
   ```

   Any failure stops here — report it and fix it. Never reach for `git commit --no-verify`.

2. **Stage, then inspect**: `git add -A`, then `git status --porcelain` and `git diff --cached --stat`.

   Staging *after* the format step in step 1 is the point. The hook's own `ruff format` is
   write-mode with no `git add` afterward, and it exits 0 even when it rewrites a file — so a
   file it reformats mid-commit gets committed in its *unformatted* form while the formatted
   version is left unstaged, which CI's `ruff format --check` then fails. Formatting first makes
   the hook's run a no-op (`N files left unchanged`) and the trap cannot fire.

   Read the staged list before continuing. `.gitignore` excludes `data/lightyear/` (personal
   financial records) and `.secrets/` for a reason — if anything sensitive is staged, or the diff
   is larger than the user expects, say so rather than committing it silently.

3. **Check the branch**: trunk-based development means committing straight to `main` (CLAUDE.md
   §Git Workflow). If `git branch --show-current` is not `main`, stop and ask — do not assume.

4. **Commit** with a heredoc so the body survives intact:

   ```bash
   git commit -F - <<'EOF'
   Short imperative subject

   Body explaining why the change was made, not what the diff already shows.

   Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
   EOF
   ```

5. **Verify the tree is clean**: `git status --porcelain` must print nothing.

   Output here means the hook reformatted files during the commit, so the commit holds
   unformatted code. Recover with `git add -A && git commit --amend --no-edit`, then re-check.

6. **Push**: `git push origin main`, then report the SHA range from the push output. Mention that
   the `Build` workflow is now running — the gate in step 1 mirrors it, so it should pass.
