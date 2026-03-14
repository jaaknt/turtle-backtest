---
description: Load and execute a task file from the /tasks folder. Use when given a task file name or issue number to work on.
argument-hint: "<issue-number or filename>"
---

# New Task

Load and execute the task described in the file specified by `$ARGUMENTS`.

## Steps

1. **Load task file** — read `/tasks/issue-$ARGUMENTS.md` (or `/tasks/$ARGUMENTS.md` if the full filename is provided). If the file does not exist, stop and report.

2. **Understand the task** — read the task description carefully. Identify the goal, acceptance criteria, and any constraints.

3. **Explore the codebase** — read relevant files to understand the current state. Use `Grep` and `Glob` to locate affected code before proposing changes.

4. **Draft a plan** — think through the approach, then append a concise TODO checklist to the task file under a `## Plan` heading. Each item should be a concrete, verifiable action.

5. **Check in** — present the plan to the user and wait for approval before making any changes. Note any risks or open questions.

6. **Execute** — once approved, work through the plan step by step:
   - Follow all conventions in `CLAUDE.md` (type hints, repo pattern, sync services, etc.)
   - Write or update tests for any changed logic
   - Run `uv run pytest` after each significant change to catch regressions early

7. **Verify** — run `uv run pytest` and `uv run ruff check .` to confirm everything passes. Fix any issues before reporting done.

8. **Update the task file** — mark completed items in the TODO list and add a `## Summary` section describing what was done and any follow-up items.
