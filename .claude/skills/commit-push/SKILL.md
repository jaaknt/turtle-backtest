---
name: commit-push
description: Commit work to main and push it — runs the full CI-parity gate first, stages deliberately so unrelated work never rides along, reports the pushed SHA range, and confirms the GitHub Build workflow passes. Use when the user asks to commit, push, or ship changes.
---

# Commit and Push to main

1. **Check the branch.** Work is committed straight to `main`. If `git branch --show-current` is
   not `main`, stop and ask.

2. **Run the gate.** It covers every step of CI (`.github/workflows/build.yml`), so a commit that
   passes it will not break the build:

   ```bash
   uv run ruff format turtlex/ scripts/ tests/ docs/ *.md  # write mode: fix formatting here, the hook only checks
   bash .githooks/pre-commit                               # ruff check, ruff format --check, mypy
   npx markdownlint-cli2
   uv run pytest
   ```

   `ruff format` also reads Python in markdown fenced blocks, so a doc-only change can fail it. Any
   failure stops here: report it and fix it. Never use `git commit --no-verify`.

3. **Stage deliberately.** Read `git status --porcelain`, then name the paths that belong to the
   change (`git add -A` only when every entry does). Leave anything else unstaged and mention it in
   the summary. `.gitignore` excludes `data/lightyear/` (personal financial records) and `.secrets/`
   for a reason: if anything sensitive is staged, or the diff is larger than the user expects, stop
   and say so. Then read `git diff --cached`, immediately before writing the message, so it
   describes what is actually staged; `--stat` alone can't tell you what the lines say.

4. **Commit** with a heredoc, in the history's style (`git log -5`): a short imperative subject,
   then a prose body saying why, not what the diff already shows.

   ```bash
   git commit -F - <<'EOF'
   Short imperative subject

   Body explaining why the change was made.

   Co-Authored-By: <the attribution line Claude Code currently supplies>
   EOF
   ```

   Copy the trailer from the session's current attribution instructions, not from this template.

5. **Push**: `git push origin main`, and note the SHA range from the push output.

6. **Confirm CI passed** on the pushed commit. Watch it in the background (`run_in_background`);
   the run takes a few seconds to register, and the wait gives up after three minutes:

   ```bash
   gh auth status >/dev/null || { echo "gh not authenticated (GH_TOKEN unset?): CI not verified"; exit 1; }
   sha=$(git rev-parse HEAD)
   for _ in $(seq 36); do
     run=$(gh run list --workflow build.yml --commit "$sha" --json databaseId,url \
       --jq '.[0] | select(.) | "\(.databaseId) \(.url)"') && [ -n "$run" ] && break
     sleep 5
   done
   [ -n "$run" ] || { echo "no Build run registered for $sha"; exit 1; }
   echo "$run"; gh run watch "${run%% *}" --exit-status
   ```

   Report the outcome with the run URL. On failure, show `gh run view <id> --log-failed` and
   diagnose it: a gate that passed locally but fails in CI usually means environment drift (an
   unpinned tool, a test that depends on local data). CodeQL also runs on push; it is slow and not
   a gate, so don't wait for it.
