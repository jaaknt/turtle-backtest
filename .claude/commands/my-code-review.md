---
description: Review staged and unstaged changes before committing, or review a specific commit. Use when the user wants a code review of pending or already-committed changes.
---

# Code Review

## Usage
- `/code-review` — review all uncommitted and staged changes
- `/code-review <commit>` — review a specific commit (e.g. `/code-review 8350bf8`)

## Steps

**If a commit hash was provided:**
1. Run `git show <commit>` to get the full diff
2. Run `git show <commit> --stat` to see affected files and the commit message

**If no commit hash (default — reviewing uncommitted changes):**
1. Run `git diff HEAD` and `git diff --cached` to get all staged and unstaged changes
2. Run `git status` to understand what files are affected

3. Review changes against the criteria below and report findings grouped by severity

## Review Criteria

### Correctness
- Logic errors, off-by-one errors, incorrect conditionals
- Edge cases not handled (empty lists, None values, date boundaries)
- Data transformations that could silently produce wrong results

### Project Conventions (from CLAUDE.md)
- Type hints on all function signatures — use `X | None` not `Optional[X]`, `list[X]` not `List[X]`
- No `Any` except at external API boundaries
- Dataclasses for internal domain objects; Pydantic only for external API responses needing `alias=`
- Private methods prefixed with `_`; constants in `UPPER_SNAKE_CASE`
- One module-level logger per file via `logging.getLogger(__name__)` — never log secrets
- No SQL outside `turtle/repository/` (repository pattern)
- Services and repos must stay synchronous — only `turtle/client/` is async

### Design Patterns
- Strategy pattern: new signal/exit/ranking strategies must extend the correct ABC
- Repository pattern: data access only in `turtle/data/`, private `_get_*` for raw rows
- Dependency injection: dependencies passed via constructor, no globals or service locators
- `Settings.from_toml()` is the only config entry point

### Code Quality
- No bare `except` clauses; no swallowed exceptions
- No `Any` type without justification
- Preconditions validated early with descriptive `ValueError`
- No unnecessary abstractions or premature generalisation
- Dead code or unused imports

### Security
- No secrets, API keys, or credentials in code or logs
- No command injection risks in shell calls
- SQL parameterisation (no string formatting into queries)

### Tests
- New logic has corresponding tests in `tests/`
- Fixtures belong in `conftest.py` (shared) or the individual test file (local)

### Documentation
- Check all *.md files and propose improvements in these files
- Check existing comments/docstrings in *.py files

## Output Format

Report findings as:

**[CRITICAL]** — Must fix before committing (bugs, security issues, broken conventions)
**[WARNING]** — Should fix (design smells, missing tests, style violations)
**[SUGGESTION]** — Optional improvements

End with a one-line overall verdict: `READY TO COMMIT`, `FIX BEFORE COMMITTING`, or `NEEDS DISCUSSION`.
