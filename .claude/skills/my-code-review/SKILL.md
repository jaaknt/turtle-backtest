---
name: my-code-review
description: Review staged and unstaged changes before committing, or review a specific commit — runs the built-in code-review for bugs, then checks project conventions, tests and docs. Use when the user wants a code review of pending or already-committed changes.
---

# Code Review

## Usage

- `/my-code-review` — review all uncommitted and staged changes
- `/my-code-review <commit>` — review a specific commit (e.g. `/my-code-review 8350bf8`)
- `/my-code-review [<commit>] <level>` — set the bug-review depth (`low`, `medium`, `high`, `xhigh`,
  `max`); without one, the built-in review reuses the level used last

## Steps

1. **Bug review**: invoke the built-in `code-review` skill via the Skill tool, passing the commit
   hash (if given) and the level (if given) as its arguments. It covers correctness, security,
   reuse and simplification — do not repeat any of that below. Wait for it to finish before step 2.

2. **Gather the diff for the project checks:**

   **If a commit hash was provided:**

   1. Run `git show <commit>` to get the full diff
   2. Run `git show <commit> --stat` to see affected files and the commit message

   **If no commit hash (default — reviewing uncommitted changes):**

   1. Run `git diff HEAD` to get all staged and unstaged changes to tracked files
   2. Run `git status --porcelain` to see what files are affected, then read every untracked (`??`)
      file in full — `git diff HEAD` does not include them, so a brand-new module is otherwise never
      reviewed

3. **Project review**: check the diff against the criteria below only, and report findings grouped
   by severity.

## Project Review Criteria

### Project Conventions

Check the diff against CLAUDE.md — in particular the "Package Rules" section (shared dataclasses in `turtlex/model.py`, SQL only in `turtlex/repository/`, strategy registries in `factory.py`, Pydantic only for EODHD responses, research/production parity, shared metrics), the "Design Patterns & Principles" section (configuration, async boundary, naming, docstrings, logging, error handling) and the "Standard Workflow" section (polars for all new code; flag any new pandas import). Do not restate those rules here — CLAUDE.md is the single source of truth.

### Tests

- New logic has corresponding tests in `tests/` (mirroring the source tree)
- Fixtures belong in `conftest.py` (shared) or the individual test file (local)

### Documentation

- Affected `*.md` files updated to match the change
- Comments/docstrings in changed code still accurate

## Output Format

Report the project findings as:

**[CRITICAL]** — Must fix before committing (broken conventions)
**[WARNING]** — Should fix (missing tests, stale docs, style violations)
**[SUGGESTION]** — Optional improvements

End with a one-line overall verdict covering both reviews — a confirmed bug from step 1 counts as
critical: `READY TO COMMIT`, `FIX BEFORE COMMITTING`, or `NEEDS DISCUSSION`.
