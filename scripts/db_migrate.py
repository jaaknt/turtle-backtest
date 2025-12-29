#!/usr/bin/env python3
"""Database migration management using Alembic.

Replaces liquibase.sh functionality with Python-based Alembic management.

Usage:
    python scripts/db_migrate.py upgrade        # Apply all pending migrations
    python scripts/db_migrate.py downgrade -1   # Rollback one migration
    python scripts/db_migrate.py current        # Show current version
    python scripts/db_migrate.py history        # Show migration history
    python scripts/db_migrate.py create "description"  # Create new migration
"""

import sys
import subprocess
from pathlib import Path

# Project root directory
project_root = Path(__file__).resolve().parents[1]


def run_alembic(command: list[str]) -> int:
    """Run Alembic command with proper environment setup."""

    # Ensure virtual environment is activated
    venv_python = project_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        print("❌ Virtual environment not found. Run: uv sync")
        return 1

    # Build full command
    full_command = [str(venv_python), "-m", "alembic"] + command

    print(f"🔧 Running: alembic {' '.join(command)}")
    print(f"📂 Working directory: {project_root}")
    print()

    # Run command
    result = subprocess.run(full_command, cwd=project_root)

    if result.returncode == 0:
        print()
        print("✅ Command completed successfully")
    else:
        print()
        print(f"❌ Command failed with exit code: {result.returncode}")

    return result.returncode


def show_help():
    """Show usage information."""
    help_text = """
Database Migration Management (Alembic)

Usage: python scripts/db_migrate.py <command> [options]

Commands:
    upgrade [revision]       Apply migrations up to target (default: head)
    downgrade <revision>     Rollback migrations to target
    current                  Show current migration version
    history                  Show migration history
    stamp <revision>         Mark database at specific version without running migrations
    create <message>         Create new migration file

Examples:
    python scripts/db_migrate.py upgrade              # Apply all pending migrations
    python scripts/db_migrate.py upgrade +1           # Apply next migration only
    python scripts/db_migrate.py downgrade -1         # Rollback one migration
    python scripts/db_migrate.py current              # Show current version
    python scripts/db_migrate.py history              # Show all migrations
    python scripts/db_migrate.py create "add_new_column"  # Create new migration
    python scripts/db_migrate.py stamp head           # Mark as up-to-date without running

Configuration:
    Database: config/settings.toml (with .env overrides)
    Migrations: db/migrations/versions/
    Alembic Config: alembic.ini
"""
    print(help_text)


def main():
    """Main entry point."""
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        show_help()
        return 0

    command = sys.argv[1]
    args = sys.argv[2:]

    # Map commands to Alembic commands
    if command == "upgrade":
        target = args[0] if args else "head"
        return run_alembic(["upgrade", target])

    elif command == "downgrade":
        if not args:
            print("❌ Error: downgrade requires target revision")
            print("Example: python scripts/db_migrate.py downgrade -1")
            return 1
        return run_alembic(["downgrade", args[0]])

    elif command == "current":
        return run_alembic(["current"])

    elif command == "history":
        return run_alembic(["history", "--verbose"])

    elif command == "stamp":
        if not args:
            print("❌ Error: stamp requires target revision")
            return 1
        return run_alembic(["stamp", args[0]])

    elif command == "create":
        if not args:
            print("❌ Error: create requires migration message")
            print("Example: python scripts/db_migrate.py create 'add new column'")
            return 1
        message = " ".join(args)
        return run_alembic(["revision", "-m", message])

    else:
        print(f"❌ Error: Unknown command '{command}'")
        show_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
