# Strategy Reference

This document covers the three categories of pluggable strategies used by the backtesting framework and how they work together.

## How Strategies Relate

The framework composes three independent strategy types into a complete trading system:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Symbol Universe                          │
│              (all US tickers from turtle.ticker)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Trading Strategy                             │
│          (generates entry Signal for each ticker)               │
│   DarvasBoxStrategy │ MarsStrategy │ MomentumStrategy           │
└────────────────────────────┬────────────────────────────────────┘
                             │  Signal (ticker, date, price, ...)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Ranking Strategy                             │
│       (scores each signal 0–100 for portfolio selection)        │
│   MomentumRanking │ VolumeMomentumRanking │ BreakoutQualityRanking │
└────────────────────────────┬────────────────────────────────────┘
                             │  ranked Signal
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Exit Strategy                               │
│       (determines when to close each open position)             │
│   BuyAndHold │ ProfitLoss │ EMA │ MACD │ ATR │ TrailingPct     │
└────────────────────────────┬────────────────────────────────────┘
                             │  Trade (entry, exit, return)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              BacktestService / PortfolioService                 │
│            (aggregates trades into performance report)          │
└─────────────────────────────────────────────────────────────────┘
```

**Typical usage pattern:**

| Use case | Trading | Ranking | Exit |
|----------|---------|---------|------|
| Trend-following backtest | `darvas_box` | `momentum` | `atr` |
| Momentum screening | `momentum` | `volume_momentum` | `trailing_percentage_loss` |
| Tight breakout | `mars` | `breakout_quality` | `profit_loss` |
| Baseline / benchmark | any | any | `buy_and_hold` |

All strategy names used by CLI scripts (`--trading-strategy`, `--ranking-strategy`, `--exit-strategy`) are registered in `turtle/factory.py`.

---

## Trading Strategies

Trading strategies implement `TradingStrategy` (ABC in `turtle/trading/base.py`). They scan historical OHLCV data and emit `Signal` objects at breakout or momentum events.

### Darvas Box (`darvas_box`)

**File**: `turtle/trading/darvas_box.py`

Identifies breakouts from price consolidation boxes, inspired by Nicolas Darvas's method.

**Data requirements**
- Time frame: configurable (default: daily)
- Minimum bars: 201
- Warmup period: 730 days

**Entry conditions**

| Category | Condition |
|----------|-----------|
| Box formation | Local max: high that exceeds 10 preceding and 4 following bars |
| Box formation | Local min: low followed by 3 higher lows |
| Breakout | Close > established box top |
| New highs | Close > max of last 20 closes |
| Trend | Close > EMA(10), EMA(20), EMA(50); EMA(10) > EMA(20) |
| Daily filters | Close > EMA(200); EMA(50) > EMA(200) |
| Volume | Volume > 110% of EMA(10) volume |
| Momentum | `(close − open) / close > 1%` |

---

### Mars (`mars`)

**File**: `turtle/trading/mars.py`

Focuses on breakouts from tight price consolidation, attributed to the @marsrides approach.

**Data requirements**
- Time frame: weekly (default)
- Minimum bars: 30
- Warmup period: 730 days

**Entry conditions**

| Category | Condition |
|----------|-----------|
| Consolidation | Price range of last 4 bars < 12% of current price |
| Breakout | Close > max of last 10 closes |
| Risk distance | Distance from consolidation midpoint < 25% of current price |
| EMA alignment | EMA(10) > EMA(20) |
| MACD | Both MACD line and signal must be valid (not NaN) |

**Built-in risk parameter**: Hard stop loss set at midpoint of 4-bar consolidation range minus 2%.

---

### Momentum (`momentum`)

**File**: `turtle/trading/momentum.py`

Identifies weekly momentum breakouts with EMA trend confirmation.

**Data requirements**
- Time frame: weekly signals, daily EMA validation
- Minimum bars: 30 weekly, 240 daily
- Lookback period: 360 days

**Entry conditions**

| Category | Condition |
|----------|-----------|
| Trend | Close > SMA(20) (weekly); ≤ 40 days below EMA(200) in past year |
| Long-term momentum | 10% price increase from 1, 3, or 6 months ago |
| New highs | Close > max of last 10 weekly closes |
| Weekly momentum | 2–20% price increase from previous week |
| Volume | Volume > 110% of previous week |
| Price position | Close > `(high + low) / 2` for the week |

---

### Strategy Comparison

| | Darvas Box | Mars | Momentum |
|--|-----------|------|----------|
| **Primary signal** | Box breakout | Tight consolidation breakout | Weekly momentum |
| **Time frame** | Daily | Weekly | Weekly |
| **Volume required** | Yes (>110% EMA10) | Optional | Yes (>110% prev week) |
| **EMA stack** | EMA10 > EMA20 > EMA50 > EMA200 | EMA10 > EMA20 | EMA(200) proximity |
| **New highs window** | 20 bars | 10 bars | 10 weeks |
| **Stop loss** | At box bottom | Consolidation midpoint −2% | None specified |

---

## Ranking Strategies

Ranking strategies implement `RankingStrategy` (ABC in `turtle/ranking/base.py`). They score signals 0–100 after entry conditions are met. The portfolio backtester uses this score to prioritise which signals to trade and applies a `min_ranking` threshold to filter low-quality signals.

### Momentum Ranking (`momentum`)

**File**: `turtle/ranking/momentum.py`

Evaluates price performance relative to EMA(200) over multiple time horizons plus period-high persistence.

**Score breakdown** (max 80 + 20 = 100):

| Component | Method | Range | Max score |
|-----------|--------|-------|-----------|
| Price tier | `_price_to_ranking()` | ≤$10 → 20 pts; ≤$1000 → 4 pts | 20 |
| EMA200 vs 1 month ago | `_ranking_ema200_1month()` | Linear 0–10% gain | 20 |
| EMA200 vs 3 months ago | `_ranking_ema200_3month()` | Linear −5% to +20% gain | 20 |
| EMA200 vs 6 months ago | `_ranking_ema200_6month()` | Linear −10% to +30% gain | 20 |
| Period high persistence | `_ranking_period_high()` | Days as highest close / 365 | 20 |

Lower-priced stocks score higher on the price component. EMA200 growth components reward sustained uptrends across multiple timeframes.

---

### Volume Momentum Ranking (`volume_momentum`)

**File**: `turtle/ranking/volume_momentum.py`

Combines price momentum, volatility adjustment, liquidity, and technical confluence. Uses `SPY` as a market benchmark for relative calculations.

**Score breakdown** (max 100):

| Component | Method | Range | Max score |
|-----------|--------|-------|-----------|
| Volume-weighted momentum | `_volume_weighted_momentum()` | 20-day return weighted by recent volume | 30 |
| Volatility-adjusted strength | `_volatility_adjusted_strength()` | 60-day risk-adjusted return | 30 |
| Liquidity quality | `_liquidity_quality()` | 60-day avg dollar volume (≥$5M for max) | 20 |
| Technical confluence | `_technical_confluence()` | RSI(14), EMA(20)/EMA(50) stack, price momentum | 20 |

**Quality gates**: signals scoring < 5 on volume momentum, < 5 on volatility strength, < 8 on liquidity, or < 40 overall are returned as score 1 (effectively filtered out at typical `min_ranking` thresholds).

---

### Breakout Quality Ranking (`breakout_quality`)

**File**: `turtle/ranking/breakout_quality.py`

Scores the strength of the breakout event itself at signal time — useful for confirming that an entry has real conviction behind it.

**Score breakdown** (max 100):

| Component | Method | Criteria | Max score |
|-----------|--------|----------|-----------|
| Volume conviction | `_volume_conviction()` | Volume / EMA10 volume; ratio ≥3.0 = max | 30 |
| Breakout extension | `_breakout_extension()` | (close − 20d high) / 20d high; ≥5% = max | 25 |
| Trend health | `_trend_health()` | EMA10 > EMA20 > EMA50 > EMA200 stack + distance from EMA200 (optimal 5–30% above) | 25 |
| MACD conviction | `_macd_conviction()` | (MACD − signal) / price; ≥0.5% = max | 20 |

---

### Ranking Strategy Comparison

| | Momentum | Volume Momentum | Breakout Quality |
|--|----------|----------------|-----------------|
| **Primary focus** | EMA(200) trend strength | Risk-adjusted momentum + liquidity | Breakout event conviction |
| **Lookback** | 1/3/6 months | 20–60 days | At signal bar |
| **Volume factor** | No | Yes (30 pts) | Yes (30 pts) |
| **Quality gates** | No | Yes (returns 1 if below thresholds) | No |
| **Best paired with** | Trend-following strategies | High-volume momentum setups | Darvas Box, Mars breakouts |

---

## Exit Strategies

Exit strategies implement `ExitStrategy` (ABC in `turtle/exit/base.py`). They receive the entry signal and the subsequent price history, and return a `Trade` with the exact exit date, price, and reason.

All strategies fetch additional historical data before the signal date to warm up their indicators.

### Buy and Hold (`buy_and_hold`)

**File**: `turtle/exit/buy_and_hold.py`

Holds the position until the end of the analysis period. Use as a baseline to measure what active exits add or cost.

| Parameter | Default | Description |
|-----------|---------|-------------|
| — | — | No configurable parameters |

**Exit reason**: `period_end`

---

### Profit / Loss Target (`profit_loss`)

**File**: `turtle/exit/profit_loss.py`

Exits as soon as either a profit target or a stop loss is hit. Whichever triggers first wins.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `profit_target` | `10.0` | % gain at which to exit (e.g. 10 = +10%) |
| `stop_loss` | `5.0` | % loss at which to exit (e.g. 5 = −5%) |

**Exit reasons**: `profit_target`, `stop_loss`, `period_end`

---

### EMA Exit (`ema`)

**File**: `turtle/exit/ema.py`

Exits when the close price drops below the EMA. Useful for trend-following exits that let winners run while cutting losses on trend breaks.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ema_period` | `20` | Period for EMA calculation |

Fetches 40 days of pre-signal data to seed the EMA. **Exit reasons**: `stop_loss`, `period_end`

---

### MACD Exit (`macd`)

**File**: `turtle/exit/macd.py`

Exits when the MACD line crosses below the signal line (bearish crossover). Captures the bulk of the move while exiting on momentum deterioration.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fastperiod` | `12` | Fast EMA period |
| `slowperiod` | `26` | Slow EMA period |
| `signalperiod` | `9` | Signal line period |

Fetches 40 days of pre-signal data for MACD seeding. **Exit reasons**: `below_signal`, `period_end`

---

### ATR Trailing Stop (`atr`)

**File**: `turtle/exit/atr.py`

Volatility-based trailing stop. The stop is set at `atr_multiplier × ATR` below the running high, and only moves up (never down).

| Parameter | Default | Description |
|-----------|---------|-------------|
| `atr_period` | `14` | Period for ATR calculation |
| `atr_multiplier` | `2.0` | Multiplier applied to ATR for stop distance |

- Initial stop: `entry_price − (atr_multiplier × ATR at entry)`
- Trailing stop: `cummax(high) − (atr_multiplier × current ATR)`, floored at the initial stop
- Fetches 60 days of pre-signal data for ATR calculation

**Exit reasons**: `atr_trailing_stop`, `period_end`

---

### Trailing Percentage Loss (`trailing_percentage_loss`)

**File**: `turtle/exit/trailing_percentage_loss.py`

Simpler trailing stop based on a fixed percentage below the running maximum close. No volatility calculation required.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `percentage_loss` | `10.0` | % below running max close at which to exit |

- Initial stop: `entry_price × (1 − percentage_loss / 100)`
- Trailing stop: `cummax(close) × (1 − percentage_loss / 100)`, floored at initial stop
- Stop only moves up, never down

**Exit reasons**: `trailing_percentage_stop`, `period_end`

---

### Exit Strategy Comparison

| | Buy & Hold | Profit/Loss | EMA | MACD | ATR | Trailing % |
|--|-----------|-------------|-----|------|-----|------------|
| **Stop loss** | None | Fixed % | Dynamic (EMA) | Momentum | Volatility-adjusted | Fixed % trailing |
| **Profit target** | None | Fixed % | None | None | None | None |
| **Adapts to volatility** | — | No | No | No | Yes | No |
| **Trailing** | — | No | Yes | Yes | Yes | Yes |
| **Warm-up data** | None | None | 40 days | 40 days | 60 days | None |
| **Best for** | Baseline | Range-bound | Trending | Momentum | Volatile | Trending |
