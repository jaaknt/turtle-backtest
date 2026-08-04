---
name: commit-push
description: Commit work to main and push it — runs the full CI-parity gate first, stages deliberately so unrelated work never rides along, and reports the pushed SHA range. Use when the user asks to commit, push, or ship changes.
---

# Commit and Push to main

The local `.git/hooks/pre-commit` hook is check-only: `ruff check`, `ruff format --check` and
`mypy` over `turtlex/ scripts/`. It aborts the commit rather than rewriting anything. CI
(`.github/workflows/build.yml`, on push to `main`) additionally runs markdownlint and `pytest` —
the gate below covers those, so a commit that passes it will not break the build.

1. **Run the gate**, in CI's order, so the first failure is the one CI would report:

   ```bash
   uv run ruff check turtlex/ scripts/
   uv run ruff format turtlex/ scripts/   # write mode — fix formatting here, not in the hook
   uv run mypy                            # no arguments, per CLAUDE.md
   uv run pytest                          # the hook does NOT run this
   npx markdownlint-cli2                  # nor this — needed only if a tracked .md changed
   ```

   Any failure stops here — report it and fix it. Never reach for `git commit --no-verify`.

2. **Stage deliberately**: `git status --porcelain` first, then stage. Prefer naming the paths you
   changed; `git add -A` is fine only once you have read that list and every entry belongs to the
   change. Anything else — work in progress the user started, an unrelated edit — gets
   `git restore --staged <path>` and a mention in your summary, never a silent ride along.

   `.gitignore` excludes `data/lightyear/` (personal financial records) and `.secrets/` for a
   reason. If anything sensitive is staged, or the diff is larger than the user expects, say so
   rather than committing it silently.

3. **Read the staged diff**: `git diff --cached`, immediately before writing the message — not
   earlier in the session. The message is a claim about what the diff contains, and the tree can
   change between an earlier read and the commit. Line counts from `--stat` cannot tell you what
   the lines say; use them only to orient yourself in a large diff.

4. **Check the branch**: trunk-based development means committing straight to `main` (CLAUDE.md
   §Git Workflow). If `git branch --show-current` is not `main`, stop and ask — do not assume.

5. **Commit** with a heredoc so the body survives intact:

   ```bash
   git commit -F - <<'EOF'
   Short imperative subject

   Body explaining why the change was made, not what the diff already shows.

   Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
   EOF
   ```

6. **Push**: `git push origin main`, then report the SHA range from the push output and note that
   the `Build` workflow is now running.
