from datetime import datetime
from turtle.common.enums import TimeFrameUnit
from turtle.config.settings import Settings
from turtle.data.bars_history import BarsHistoryRepo
from turtle.ranking.momentum import MomentumRanking
from turtle.services.signal_service import SignalService
from turtle.signal.darvas_box import DarvasBoxStrategy

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

end_date = datetime(year=2025, month=8, day=12)

# Create settings and database connection
settings = Settings.from_toml()
engine = settings.engine
bars_history = BarsHistoryRepo(engine)

# Create DarvasBoxStrategy instance
darvas_strategy = DarvasBoxStrategy(
    bars_history=bars_history,
    ranking_strategy=MomentumRanking(),
    time_frame_unit=TimeFrameUnit.DAY,
    warmup_period=730,
)

# Create strategy runner with the trading strategy
strategy_runner = SignalService(engine=engine, app_config=settings.app, trading_strategy=darvas_strategy)

# Get ticker list (now with correct method signature)
signals = []
for ticker in strategy_runner.get_symbol_list():
    signals = strategy_runner.get_signals(ticker, end_date, end_date)


# Extract just the symbol names for get_company_list
symbol_names = [ticker.ticker for ticker in signals]
df: pd.DataFrame = strategy_runner.get_company_list(symbol_names)

# Streamlit commands to visualize the DataFrame
st.title("DataFrame Visualization with Streamlit")
st.write("Here is a simple DataFrame:")

# Display the DataFrame
st.dataframe(df)  # You can also use st.write(df) or st.table(df)
