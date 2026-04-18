from datetime import date
from turtle.common.enums import TimeFrameUnit
from turtle.config.settings import Settings
from turtle.repository.analytics import OhlcvAnalyticsRepository
from turtle.service.signal_service import SignalService
from turtle.strategy.ranking.momentum import MomentumRanking
from turtle.strategy.trading.darvas_box import DarvasBoxStrategy

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

end_date = date.today()

# Create settings and database connection
settings = Settings.from_toml()
engine = settings.engine
bars_history = OhlcvAnalyticsRepository(engine)

# Create DarvasBoxStrategy instance
darvas_strategy = DarvasBoxStrategy(
    bars_history=bars_history,
    ranking_strategy=MomentumRanking(),
    time_frame_unit=TimeFrameUnit.DAY,
    warmup_period=730,
)

# Create strategy runner with the trading strategy
strategy_runner = SignalService(engine=engine, trading_strategy=darvas_strategy)

# Get ticker list and collect all signals
signals = []
for ticker in strategy_runner.get_symbol_list():
    signals.extend(strategy_runner.get_signals(ticker, end_date, end_date))

df: pd.DataFrame = pd.DataFrame([{"ticker": s.ticker, "date": s.date, "ranking": s.ranking} for s in signals])

# Streamlit commands to visualize the DataFrame
st.title("DataFrame Visualization with Streamlit")
st.write("Here is a simple DataFrame:")

# Display the DataFrame
st.dataframe(df)
