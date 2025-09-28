"""
Setup script for live trading functionality.

This script:
1. Creates the live trading database schema
2. Validates the setup
3. Provides configuration guidance
"""

import os
import sys
import logging
from pathlib import Path

import psycopg

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


def setup_database_schema(db_dsn: str) -> bool:
    """
    Set up the live trading database schema.

    Args:
        db_dsn: Database connection string

    Returns:
        True if setup successful
    """
    try:
        schema_file = project_root / "db" / "live_trading_schema.sql"

        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False

        logger.info("Reading schema file...")
        schema_sql = schema_file.read_text()

        logger.info("Connecting to database...")
        with psycopg.connect(db_dsn) as conn:
            with conn.cursor() as cur:
                logger.info("Executing schema creation...")
                cur.execute(schema_sql)
                conn.commit()

        logger.info("Database schema created successfully!")
        return True

    except Exception as e:
        logger.error(f"Error setting up database schema: {e}")
        return False


def validate_database_setup(db_dsn: str) -> bool:
    """
    Validate that the database schema is set up correctly.

    Args:
        db_dsn: Database connection string

    Returns:
        True if validation passes
    """
    try:
        expected_tables = [
            "live_orders",
            "live_positions",
            "trading_sessions",
            "execution_reports",
            "account_snapshots",
            "risk_events"
        ]

        logger.info("Validating database schema...")
        with psycopg.connect(db_dsn) as conn:
            with conn.cursor() as cur:
                # Check if tables exist
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'turtle'
                    AND table_name IN %s
                """, (tuple(expected_tables),))

                existing_tables = {row[0] for row in cur.fetchall()}

                missing_tables = set(expected_tables) - existing_tables

                if missing_tables:
                    logger.error(f"Missing tables: {missing_tables}")
                    return False

                logger.info("All required tables found!")

                # Check indexes
                cur.execute("""
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = 'turtle'
                    AND indexname LIKE 'idx_%'
                """)

                indexes = [row[0] for row in cur.fetchall()]
                logger.info(f"Found {len(indexes)} indexes")

                # Check functions
                cur.execute("""
                    SELECT routine_name
                    FROM information_schema.routines
                    WHERE routine_schema = 'turtle'
                    AND routine_name = 'update_modified_column'
                """)

                functions = [row[0] for row in cur.fetchall()]
                if not functions:
                    logger.warning("update_modified_column function not found")
                else:
                    logger.info("Trigger function found")

        logger.info("Database validation passed!")
        return True

    except Exception as e:
        logger.error(f"Error validating database setup: {e}")
        return False


def check_environment_variables() -> bool:
    """Check if required environment variables are set."""
    logger.info("Checking environment variables...")

    required_vars = [
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY"
    ]

    optional_vars = [
        "DATABASE_DSN"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.info("Please set these variables in your .env file or environment:")
        for var in missing_vars:
            logger.info(f"  export {var}=your_value_here")
        return False

    logger.info("Required environment variables found!")

    # Check optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"{var}: {value}")
        else:
            logger.info(f"{var}: using default")

    return True


def test_alpaca_connection() -> bool:
    """Test connection to Alpaca API."""
    try:
        from turtle.trade.client import AlpacaTradingClient

        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")

        if not api_key or not secret_key:
            logger.warning("Alpaca credentials not found, skipping connection test")
            return True

        logger.info("Testing Alpaca API connection...")
        client = AlpacaTradingClient(api_key, secret_key, paper=True)

        # Test getting account info
        account = client.get_account()
        logger.info("Alpaca connection successful!")
        logger.info(f"Account ID: {account.account_id}")
        logger.info(f"Equity: ${account.equity}")
        logger.info(f"Cash: ${account.cash}")

        # Test market status
        market_status = client.get_market_status()
        logger.info(f"Market open: {market_status['is_open']}")

        return True

    except Exception as e:
        logger.error(f"Error testing Alpaca connection: {e}")
        return False


def create_example_env_file() -> None:
    """Create example .env file."""
    env_file = project_root / ".env.example"

    env_content = """# Alpaca API Configuration
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here

# Database Configuration (optional, will use default if not set)
DATABASE_DSN=host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres

# Live Trading Settings
PAPER_TRADING=true
INITIAL_CAPITAL=25000.0
MAX_POSITION_SIZE=5000.0
MAX_DAILY_LOSS=500.0
"""

    try:
        env_file.write_text(env_content)
        logger.info(f"Created example environment file: {env_file}")
        logger.info("Copy this to .env and update with your actual values")
    except Exception as e:
        logger.error(f"Error creating example .env file: {e}")


def main() -> bool:
    """Main setup function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger.info("Live Trading Setup Script")
    logger.info("=" * 50)

    # Step 1: Check environment variables
    if not check_environment_variables():
        logger.info("\nCreating example .env file...")
        create_example_env_file()
        logger.error("Please configure environment variables and run again")
        return False

    # Step 2: Set up database
    db_dsn = os.getenv("DATABASE_DSN",
                      "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=postgres")

    logger.info(f"\nUsing database: {db_dsn}")

    choice = input("Set up database schema? (Y/n): ")
    if choice.lower() != 'n':
        if not setup_database_schema(db_dsn):
            logger.error("Database setup failed")
            return False

    # Step 3: Validate database
    if not validate_database_setup(db_dsn):
        logger.error("Database validation failed")
        return False

    # Step 4: Test Alpaca connection
    choice = input("Test Alpaca API connection? (Y/n): ")
    if choice.lower() != 'n':
        if not test_alpaca_connection():
            logger.warning("Alpaca connection test failed, but setup can continue")

    logger.info("\n" + "=" * 50)
    logger.info("Live trading setup completed successfully!")
    logger.info("\nNext steps:")
    logger.info("1. Review the example at examples/live_trading_example.py")
    logger.info("2. Configure your trading strategy and risk parameters")
    logger.info("3. Test with paper trading before going live")
    logger.info("4. Monitor your trades and adjust as needed")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
