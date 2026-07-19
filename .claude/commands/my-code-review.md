---
description: Review staged and unstaged changes before committing, or review a specific commit. Use when the user wants a code review of pending or already-committed changes.
---

# Code Review

## Usage

- `/my-code-review` — review all uncommitted and staged changes
- `/my-code-review <commit>` — review a specific commit (e.g. `/my-code-review 8350bf8`)

## Steps

**If a commit hash was provided:**

1. Run `git show <commit>` to get the full diff
2. Run `git show <commit> --stat` to see affected files and the commit message

**If no commit hash (default — reviewing uncommitted changes):**

1. Run `git diff HEAD` and `git diff --cached` to get all staged and unstaged changes
2. Run `git status` to understand what files are affected

Then review the changes against the criteria below and report findings grouped by severity.

## Review Criteria

### Project Conventions

Check the diff against CLAUDE.md — in particular the "Design Patterns & Principles" section (strategy/repository/DI patterns, dataclasses vs Pydantic, async boundary, naming, docstrings, type hints, logging, error handling) and the "Standard Workflow" section (polars for all new code; flag any new pandas import). Do not restate those rules here — CLAUDE.md is the single source of truth.

### Correctness

- Logic errors, off-by-one errors, incorrect conditionals
- Edge cases not handled (empty lists, None values, date boundaries)
- Data transformations that could silently produce wrong results

### Security

- No secrets, API keys, or credentials in code or logs
- No command injection risks in shell calls
- SQL parameterisation (no string formatting into queries)

### Tests

- New logic has corresponding tests in `tests/` (mirroring the source tree)
- Fixtures belong in `conftest.py` (shared) or the individual test file (local)

### Documentation

- Affected `*.md` files updated to match the change
- Comments/docstrings in changed code still accurate

## Output Format

Report findings as:

**[CRITICAL]** — Must fix before committing (bugs, security issues, broken conventions)
**[WARNING]** — Should fix (design smells, missing tests, style violations)
**[SUGGESTION]** — Optional improvements

End with a one-line overall verdict: `READY TO COMMIT`, `FIX BEFORE COMMITTING`, or `NEEDS DISCUSSION`.
