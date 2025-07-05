# Trading Strategy Analysis

This document analyzes the stock selection conditions implemented in the three trading strategies: Momentum, Darvas Box, and Mars.

## 1. Momentum Strategy

The Momentum Strategy (`turtle/strategy/momentum.py`) identifies stocks based on weekly momentum signals with the following selection criteria:

### Data Requirements
- **Time Frame**: Weekly data for momentum analysis, daily data for EMA validation
- **Minimum Data**: 30 weekly bars, 240 daily bars (filtered period)
- **Lookback Period**: 360 days for analysis

### Selection Conditions

#### Trend Validation
- **Current price above SMA(20)**: `close > sma_20` (weekly)
- **Limited downside**: Maximum 40 days below 200-day EMA in the past year
- **Strong momentum**: 10% price increase from 1, 3, or 6 months ago
- **New highs**: Current close must exceed maximum of last 10 weekly closes

#### Entry Timing
- **Weekly momentum**: 2-20% price increase from previous week
- **Volume confirmation**: Volume must be >10% higher than previous week
- **Price position**: Close must be above midpoint of current week's range `(high + low) / 2`

## 2. Darvas Box Strategy

The Darvas Box Strategy (`turtle/strategy/darvas_box.py`) identifies breakout opportunities from consolidation patterns:

### Data Requirements
- **Time Frame**: Configurable (default: weekly)
- **Minimum Data**: 201 bars minimum
- **Warmup Period**: 300 days for indicator calculation

### Selection Conditions

#### Box Formation
- **Local Maximum**: Price high that exceeds 10 preceding and 4 following periods
- **Local Minimum**: Price low followed by 3 higher lows
- **Box Validation**: High must remain unbroken until box formation is complete

#### Breakout Confirmation
- **Darvas breakout**: Close price breaks above established box top
- **New highs**: Close > maximum of last 20 closes
- **Trend alignment**: Close above EMA(10), EMA(20), and EMA(50)
- **EMA sequence**: EMA(10) > EMA(20) for short-term momentum

#### Additional Filters (Daily timeframe)
- **Long-term trend**: Close > EMA(200) and EMA(50) > EMA(200)
- **Volume surge**: Volume > 110% of EMA(10) volume
- **Daily momentum**: `(close - open) / close > 1%`

## 3. Mars Strategy

The Mars Strategy (`turtle/strategy/mars.py`) focuses on breakouts from tight consolidation patterns:

### Data Requirements
- **Time Frame**: Weekly (default)
- **Minimum Data**: 30 bars minimum
- **Warmup Period**: 300 days for indicator calculation

### Selection Conditions

#### Consolidation Analysis
- **Tight consolidation**: Price range of last 4 periods < 12% of current price
- **Breakout level**: Close above maximum of last 10 closes
- **Risk management**: Distance from consolidation midpoint < 25% of current price

#### Trend Confirmation
- **EMA alignment**: EMA(10) > EMA(20) indicating upward momentum
- **MACD validation**: Both MACD line and signal must be valid (not NaN)

#### Risk Controls
- **Hard stop loss**: Calculated as midpoint of 4-period consolidation range minus 2%
- **Maximum risk**: Position size limited by distance to stop loss

## Strategy Comparison

| Criteria | Momentum | Darvas Box | Mars |
|----------|----------|------------|------|
| **Primary Signal** | Weekly momentum | Box breakout | Consolidation breakout |
| **Trend Filter** | SMA(20), EMA(200) | Multiple EMAs | EMA(10) > EMA(20) |
| **Volume Requirement** | >10% increase | >110% of EMA(10) | Optional |
| **New Highs** | 10-week high | 20-period high | 10-period high |
| **Risk Management** | None specified | Stop at box bottom | Hard stop loss |
| **Time Sensitivity** | Weekly momentum | Pattern completion | Tight consolidation |

## Common Success Factors

All strategies share these key principles:
1. **New highs requirement**: Stocks must be making new highs over their respective lookback periods
2. **Trend confirmation**: Multiple indicators must align to confirm upward momentum
3. **Volume validation**: Increased volume provides conviction for breakout moves
4. **Risk awareness**: Position sizing and stop loss considerations are built into selection criteria

## Usage Recommendations

- **Momentum Strategy**: Best for capturing sustained weekly trends with strong fundamental momentum
- **Darvas Box Strategy**: Ideal for identifying breakouts from established consolidation patterns
- **Mars Strategy**: Optimal for tight consolidation breakouts with defined risk parameters

Each strategy can be backtested using the provided framework with historical data to validate performance across different market conditions.