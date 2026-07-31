# Strategy Reference

This document covers the three categories of pluggable strategies used by the backtesting framework and how they work together.

## How Strategies Relate

The framework composes three independent strategy types into a complete trading system:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                     Symbol Universe                                     │
│                           (all US tickers from turtle.ticker)                           │
└─────────────────────────────────────────────┬───────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                     Trading Strategy                                    │
│                         (generates entry Signal for each ticker)                        │
│        DarvasBoxStrategy │ MarsStrategy │ MomentumStrategy │ QullamaggieStrategy        │
└─────────────────────────────────────────────┬───────────────────────────────────────────┘
                                              │  Signal (ticker, date, price, ...)
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                     Ranking Strategy                                    │
│                    (scores each signal 0–100 for portfolio selection)                   │
│  MomentumRanking │ VolumeMomentumRanking │ BreakoutQualityRanking │ QullamaggieRanking  │
└─────────────────────────────────────────────┬───────────────────────────────────────────┘
                                              │  ranked Signal
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                      Exit Strategy                                      │
│                      (determines when to close each open position)                      │
│                 BuyAndHold │ ProfitLoss │ EMA │ MACD │ ATR │ TrailingPct                │
└─────────────────────────────────────────────┬───────────────────────────────────────────┘
                                              │  Trade (entry, exit, return)
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            BacktestService / PortfolioService                           │
│                       (aggregates trades into performance report)                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

**Typical usage pattern:**

| Use case | Trading | Ranking | Exit |
| ---------- | --------- | --------- | ------ |
| Trend-following backtest | `darvas_box` | `momentum` | `atr` |
| Momentum screening | `momentum` | `volume_momentum` | `trailing_percentage_loss` |
| Tight breakout | `mars` | `breakout_quality` | `profit_loss` |
| Baseline / benchmark | any | any | `buy_and_hold` |

All strategy names used by CLI scripts (`--trading-strategy`, `--ranking-strategy`, `--exit-strategy`) are registered in `turtlex/strategy/factory.py`.

---

## Trading Strategies

Trading strategies implement `TradingStrategy` (ABC in `turtlex/strategy/trading/base.py`). They scan historical OHLCV data and emit `Signal` objects at breakout or momentum events.

### Darvas Box (`darvas_box`)

**File**: `turtlex/strategy/trading/darvas_box.py`

Identifies breakouts from price consolidation boxes, inspired by Nicolas Darvas's method.

#### Data requirements

- Time frame: configurable (default: daily)
- Minimum bars: 201
- Warmup period: 730 days

#### Entry conditions

| Category | Condition |
| ---------- | ----------- |
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

**File**: `turtlex/strategy/trading/mars.py`

Focuses on breakouts from tight price consolidation, attributed to the @marsrides approach.

#### Data requirements

- Time frame: weekly (default)
- Minimum bars: 30
- Warmup period: 730 days

#### Entry conditions

| Category | Condition |
| ---------- | ----------- |
| Consolidation | Price range of last 4 bars < 12% of current price |
| Breakout | Close > max of last 10 closes |
| Risk distance | Distance from consolidation midpoint < 25% of current price |
| EMA alignment | EMA(10) > EMA(20) |
| MACD | Both MACD line and signal must be valid (not NaN) |

**Built-in risk parameter**: Hard stop loss set at midpoint of 4-bar consolidation range minus 2%.

---

### Momentum (`momentum`)

**File**: `turtlex/strategy/trading/momentum.py`

Identifies weekly momentum breakouts with EMA trend confirmation.

#### Data requirements

- Time frame: weekly signals, daily EMA validation
- Minimum bars: 30 weekly, 240 daily
- Lookback period: 360 days

#### Entry conditions

| Category | Condition |
| ---------- | ----------- |
| Trend | Close > SMA(20) (weekly); ≤ 40 days below EMA(200) in past year |
| Long-term momentum | 10% price increase from 1, 3, or 6 months ago |
| New highs | Close > max of last 10 weekly closes |
| Weekly momentum | 2–20% price increase from previous week |
| Volume | Volume > 110% of previous week |
| Price position | Close > `(high + low) / 2` for the week |

---

### Qullamaggie (`qullamaggie`)

**File**: `turtlex/strategy/trading/qullamaggie.py`

Qullamaggie-style 50-day-high breakout (bk50d_s15_v1.3_roc100), ported from the validated signal in `scripts/qullamaggie-backtest-v4.py`. Unlike the other strategies it defines its own fundamentals-based universe (US common stocks with market cap ≥ $1.5B, excluding Communication Services and Real Estate) instead of a symbol group, and gates entries on market regime. All rolling indicators are computed on prior-day (shift-1) values so filters only use information available at the previous close.

Bars with a non-positive close or adjusted close, or zero volume, are dropped before the minimum-history check — keeping them would skew the rolling volume averages.

`turtlex/research/qullamaggie.py` is the bulk (whole-universe-in-one-query) counterpart used by the `scripts/` studies. The two are kept identical by `tests/research/test_qullamaggie_parity.py`, which asserts both produce the same `(symbol, signal_date, entry_date, entry_price)` tuples. Change one, change the other.

#### Data requirements

- Time frame: daily
- Minimum bars: 300
- Warmup period: 730 days (plus 300 extra days of SPY history for the regime gate)

#### Entry conditions

| Category | Condition |
| ---------- | ----------- |
| Breakout | Adjusted close > max of prior 50 closes |
| Trend distance | Adjusted close more than 12% above the 50-day SMA — the default of the `sma_thresh` constructor parameter, overridable with `--trading-param sma_thresh=0.20` |
| Volume | Average volume ≥ 500k; dry-up < 0.90 of average; surge capped at 2.0× |
| Momentum caps | 12-month ROC < 100%; RSI(14) < 70 |
| Volatility | ADR(20) ≥ 3%; ADR change ≤ 0.90 |
| Price band | Raw close between $5 and $250 |
| Market regime | SPY above its 200-day SMA |
| Cooldown | Signals within 30 calendar days of the previous accepted trigger are suppressed |

---

### Strategy Comparison

| | Darvas Box | Mars | Momentum | Qullamaggie |
| -- | ----------- | ------ | ---------- | ------------- |
| **Primary signal** | Box breakout | Tight consolidation breakout | Weekly momentum | 50-day-high breakout |
| **Time frame** | Daily | Weekly | Weekly | Daily |
| **Volume required** | Yes (>110% EMA10) | Optional | Yes (>110% prev week) | Yes (dry-up + surge cap) |
| **EMA stack** | EMA10 > EMA20 > EMA50 > EMA200 | EMA10 > EMA20 | EMA(200) proximity | >12% above SMA(50) (default) |
| **New highs window** | 20 bars | 10 bars | 10 weeks | 50 bars |
| **Stop loss** | At box bottom | Consolidation midpoint −2% | None specified | None specified |

---

## Ranking Strategies

Ranking strategies implement `RankingStrategy` (ABC in `turtlex/strategy/ranking/base.py`). They score signals 0–100 after entry conditions are met. The portfolio backtester uses this score to prioritise which signals to trade and applies a `min_ranking` threshold to filter low-quality signals.

### Momentum Ranking (`momentum`)

**File**: `turtlex/strategy/ranking/momentum.py`

Evaluates price performance relative to EMA(200) over multiple time horizons plus period-high persistence.

**Score breakdown** (max 80 + 20 = 100):

| Component | Method | Range | Max score |
| ----------- | -------- | ------- | ----------- |
| Price tier | `_price_to_ranking()` | ≤$10 → 20 pts; ≤$1000 → 4 pts | 20 |
| EMA200 vs 1 month ago | `_ranking_ema200_1month()` | Linear 0–10% gain | 20 |
| EMA200 vs 3 months ago | `_ranking_ema200_3month()` | Linear −5% to +20% gain | 20 |
| EMA200 vs 6 months ago | `_ranking_ema200_6month()` | Linear −10% to +30% gain | 20 |
| Period high persistence | `_ranking_period_high()` | Days as highest close / 365 | 20 |

Lower-priced stocks score higher on the price component. EMA200 growth components reward sustained uptrends across multiple timeframes.

---

### Volume Momentum Ranking (`volume_momentum`)

**File**: `turtlex/strategy/ranking/volume_momentum.py`

Combines price momentum, volatility adjustment, liquidity, and technical confluence. Uses `SPY` as a market benchmark for relative calculations.

**Score breakdown** (max 100):

| Component | Method | Range | Max score |
| ----------- | -------- | ------- | ----------- |
| Volume-weighted momentum | `_volume_weighted_momentum()` | 20-day return weighted by recent volume | 30 |
| Volatility-adjusted strength | `_volatility_adjusted_strength()` | 60-day risk-adjusted return | 30 |
| Liquidity quality | `_liquidity_quality()` | 60-day avg dollar volume (≥$5M for max) | 20 |
| Technical confluence | `_technical_confluence()` | RSI(14), EMA(20)/EMA(50) stack, price momentum | 20 |

**Quality gates**: signals scoring < 5 on volume momentum, < 5 on volatility strength, < 8 on liquidity, or < 40 overall are returned as score 1 (effectively filtered out at typical `min_ranking` thresholds).

---

### Breakout Quality Ranking (`breakout_quality`)

**File**: `turtlex/strategy/ranking/breakout_quality.py`

Scores the strength of the breakout event itself at signal time — useful for confirming that an entry has real conviction behind it.

**Score breakdown** (max 100):

| Component | Method | Criteria | Max score |
| ----------- | -------- | ---------- | ----------- |
| Volume conviction | `_volume_conviction()` | Volume / EMA10 volume; ratio ≥3.0 = max | 30 |
| Breakout extension | `_breakout_extension()` | (close − 20d high) / 20d high; ≥5% = max | 25 |
| Trend health | `_trend_health()` | EMA10 > EMA20 > EMA50 > EMA200 stack + distance from EMA200 (optimal 5–30% above) | 25 |
| MACD conviction | `_macd_conviction()` | (MACD − signal) / price; ≥0.5% = max | 20 |

---

### Qullamaggie Ranking (`qullamaggie`)

**File**: `turtlex/strategy/ranking/qullamaggie.py`

Cohort-derived ranking for Qullamaggie-style breakout signals. Scores each signal by three entry-time parameters against the Sortino gradients in the cohort research (`docs/research/result-qullamaggie-cohorts-*.md`, `bk50d_s15_v1.3_roc100` tables, 2026-07-22 run). Each dimension's bands mimic the cohort buckets, with points equal to the bucket's Sortino rescaled to 0–weight within the dimension, using only the *reachable* buckets a candidate can actually land in given that dimension's own entry filter. The weights come from `result-qullamaggie-ranking-weights.md` (2026-07-29): a per-trade scan of 1685 signals over 2010-2020 on year-demeaned 366d returns, which found only these three of the original six dimensions carried a cross-sectional effect holding its sign across both halves of the period.

**Score breakdown** (max 100):

| Component | Column | Best cohort | Max score |
| ----------- | -------- | ------------- | ----------- |
| ADR%(20) | `adr_pct` | ≥8% daily range | 40 |
| Distance above SMA50 | `pct_vs_sma50` | >30% above SMA50 | 35 |
| Entry price | `close` | $5–$10 raw close | 25 |

ADR compression (`adr_pct_change`), 12-month ROC (`roc_252d`) and RSI(14) previously carried 12/10/3 points. They were dropped in 2026-07-29: 25–75% of each one's apparent power was a time effect (years with high average readings were high-return years), and all three reversed sign between the halves of 2010-2020. Re-adding them at low weight purely as tie-breakers was tested and recovered nothing.

Expects the shift-1 indicator columns produced by `QullamaggieStrategy`; a missing column or null value scores that component 0 — so pairing this ranking with a strategy that computes neither `adr_pct` nor `pct_vs_sma50` (darvas_box, mars, momentum) caps every signal at 25, below the default `--min-signal-ranking 40`, and the backtest takes no trades. The bands are calibrated at the strategy's default 15% SMA distance: lowering it (`--trading-param sma_thresh=0.05`) below 0.10 admits signals that score 0 of the 35 available points on that dimension, leaving a ceiling of 65 against that same gate. Raising it has the opposite problem — at `sma_thresh=0.20` only the top two SMA50 bands remain reachable (31 and 35 points), so the dimension spreads signals by at most 4 points and the ranking has little left to say. This is why the re-weighting gains clearly at s12 and s16 but is mixed at s20, where CAGR is within noise and risk-adjusted metrics are slightly worse at the tightest selectivity. Note: per `result-qullamaggie-cohorts-ranking.md`, this score separates 366d outcomes monotonically and the default `>=40` gate lifts both pool Sortino and median return, though far less at s20 where the low bands are already unreachable; `result-qullamaggie-ranking-validation.md` walk-forward validates the earlier six-dimension weighting. This ranking orders surviving signals, it is not a substitute for the entry filters.

---

### Ranking Strategy Comparison

| | Momentum | Volume Momentum | Breakout Quality | Qullamaggie |
| -- | ---------- | ---------------- | ----------------- | ------------- |
| **Primary focus** | EMA(200) trend strength | Risk-adjusted momentum + liquidity | Breakout event conviction | Cohort Sortino mimicry |
| **Lookback** | 1/3/6 months | 20–60 days | At signal bar | At signal bar (shift-1 indicators) |
| **Volume factor** | No | Yes (30 pts) | Yes (30 pts) | No |
| **Quality gates** | No | Yes (returns 1 if below thresholds) | No | No |
| **Best paired with** | Trend-following strategies | High-volume momentum setups | Darvas Box, Mars breakouts | Qullamaggie breakouts |

---

## Exit Strategies

Exit strategies implement `ExitStrategy` (ABC in `turtlex/strategy/exit/base.py`). They receive the entry signal and the subsequent price history, and return a `Trade` with the exact exit date, price, and reason.

All strategies fetch additional historical data before the signal date to warm up their indicators.

### Buy and Hold (`buy_and_hold`)

**File**: `turtlex/strategy/exit/buy_and_hold.py`

Holds the position for a fixed number of calendar days, selling at the first bar on/after the cutoff. Use as a baseline to measure what active exits add or cost.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `holding_days` | 30 | Calendar days to hold before selling (sell at first bar on/after the cutoff) |

**Exit reasons**: `holding_period` (cutoff reached), `period_end` (data ended before the cutoff)

---

### Profit / Loss Target (`profit_loss`)

**File**: `turtlex/strategy/exit/profit_loss.py`

Exits as soon as either a profit target or a stop loss is hit. Whichever triggers first wins.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `profit_target` | `10.0` | % gain at which to exit (e.g. 10 = +10%) |
| `stop_loss` | `5.0` | % loss at which to exit (e.g. 5 = −5%) |

**Exit reasons**: `profit_target`, `stop_loss`, `period_end`

---

### EMA Exit (`ema`)

**File**: `turtlex/strategy/exit/ema.py`

Exits when the close price drops below the EMA. Useful for trend-following exits that let winners run while cutting losses on trend breaks.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ema_period` | `20` | Period for EMA calculation |

Fetches 40 days of pre-signal data to seed the EMA. **Exit reasons**: `stop_loss`, `period_end`

---

### MACD Exit (`macd`)

**File**: `turtlex/strategy/exit/macd.py`

Exits when the MACD line crosses below the signal line (bearish crossover). Captures the bulk of the move while exiting on momentum deterioration.

| Parameter | Default | Description |
| ----------- | --------- | ------------- |
| `fastperiod` | `12` | Fast EMA period |
| `slowperiod` | `26` | Slow EMA period |
| `signalperiod` | `9` | Signal line period |

Fetches 40 days of pre-signal data for MACD seeding. **Exit reasons**: `below_signal`, `period_end`

---

### ATR Trailing Stop (`atr`)

**File**: `turtlex/strategy/exit/atr.py`

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

**File**: `turtlex/strategy/exit/trailing_percentage_loss.py`

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
| -- | ----------- | ------------- | ----- | ------ | ----- | ------------ |
| **Stop loss** | None | Fixed % | Dynamic (EMA) | Momentum | Volatility-adjusted | Fixed % trailing |
| **Profit target** | None | Fixed % | None | None | None | None |
| **Adapts to volatility** | — | No | No | No | Yes | No |
| **Trailing** | — | No | Yes | Yes | Yes | Yes |
| **Warm-up data** | None | None | 40 days | 40 days | 60 days | None |
| **Best for** | Baseline | Range-bound | Trending | Momentum | Volatile | Trending |
