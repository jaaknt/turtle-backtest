"""Write repositories for the data-ingest paths.

The EODHD download repositories are async (AsyncSession); the Lightyear statement
importer and the signal writer are sync (Engine), matching the sync CLIs they run from.
"""

from turtlex.repository.ingest.company import CompanyRepository
from turtlex.repository.ingest.daily_bars import DailyBarsRepository
from turtlex.repository.ingest.exchange import ExchangeRepository
from turtlex.repository.ingest.job_run import JobRunRepository
from turtlex.repository.ingest.lightyear import LightyearRepository
from turtlex.repository.ingest.signal import SignalRepository
from turtlex.repository.ingest.ticker import TickerRepository

__all__ = [
    "CompanyRepository",
    "DailyBarsRepository",
    "ExchangeRepository",
    "JobRunRepository",
    "LightyearRepository",
    "SignalRepository",
    "TickerRepository",
]
