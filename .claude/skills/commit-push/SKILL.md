---
name: commit-push
description: Commit work to main and push it — runs the full CI-parity gate first, stages deliberately so unrelated work never rides along, reports the pushed SHA range, and confirms the GitHub Build workflow passes. Use when the user asks to commit, push, or ship changes.
---

# Commit and Push to main

The `.githooks/pre-commit` hook is check-only: `ruff check` and `mypy` over `turtlex/ scripts/`,
and `ruff format --check` over `turtlex/ scripts/ docs/ *.md` — the formatter reads Python inside
markdown fenced blocks, so a doc snippet can fail it where the linter sees nothing. It aborts the
commit rather than rewriting anything, and is active only where
`git config core.hooksPath .githooks` has been run. CI (`.github/workflows/build.yml`, on push to
`main`) additionally runs markdownlint and `pytest` — the gate below covers those, so a commit
that passes it will not break the build.

1. **Run the gate**, in CI's order, so the first failure is the one CI would report:

   ```bash
   uv run ruff check turtlex/ scripts/
   uv run ruff format turtlex/ scripts/ docs/ *.md   # write mode — fix formatting here, not in the hook
   npx markdownlint-cli2                             # the hook does NOT run this — needed only if a tracked .md changed
   uv run mypy                                       # no arguments, per CLAUDE.md
   uv run pytest                                     # nor this
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

   Co-Authored-By: <the attribution line Claude Code currently supplies>
   EOF
   ```

   Copy the trailer from the session's current attribution instructions rather than from this
   template — the model name in it changes between releases.

6. **Push**: `git push origin main`, and note the SHA range from the push output.

7. **Confirm CI passed**: the push is not done until the `Build` workflow is green on the pushed
   head. The run takes a few seconds to register, so wait for it to appear before watching it:

   ```bash
   sha=$(git rev-parse HEAD)
   until run=$(gh run list --workflow build.yml --commit "$sha" --json databaseId \
       --jq '.[0].databaseId') && [ -n "$run" ]; do sleep 5; done
   gh run watch "$run" --exit-status
   ```

   Run this in the background (`run_in_background`), since a build takes minutes. When it exits,
   report the outcome with the run URL (`gh run view "$run" --json url --jq .url`). On failure,
   show the failing step's log (`gh run view "$run" --log-failed`) and diagnose it. A gate that
   passed locally but fails in CI usually means environment drift, such as an unpinned tool
   version or a test that depends on local data. Don't stop at "CI failed". `CodeQL` also runs
   on push, but it is slow and not part of the build gate, so don't wait for it.

   If `gh` returns 401, `GH_TOKEN` is probably unset. Say that CI was not verified rather than
   skipping the step without a word.
