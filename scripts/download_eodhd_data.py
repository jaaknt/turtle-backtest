import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path to import turtle modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from turtle.config.settings import Settings
from turtle.service.eodhd_service import EodhdService

logger = logging.getLogger(__name__)


async def main():
    # Force logging to stdout for this script
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="[%(levelname)s|%(module)s|%(funcName)s] %(message)s")
    logger.info("Starting EODHD data download script.")
    settings = Settings.from_toml()
    eodhd_service = EodhdService(settings)
    try:
        await eodhd_service.download_exchanges()
        logger.info("EODHD exchange data download completed successfully.")
    except Exception as e:
        logger.error(f"EODHD data download script failed: {e}", exc_info=True)
        # Re-raise the exception for the script to exit with an error code
        raise
    finally:
        await eodhd_service.close()
        logger.info("EODHD data download script finished.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        # The logger already captured the exception, just exit with error code
        exit(1)
