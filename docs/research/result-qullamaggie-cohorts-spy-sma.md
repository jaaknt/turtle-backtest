# Qullamaggie SPY Regime (market SMA) Cohort Analysis

Run date: 2026-08-02 15:04:48 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Periods | **2006-01-01 – 2010-12-31, 2018-01-01 – 2023-12-31** — each straddles a bear market |
| Hold | 366d (calendar) |
| Cohorts | bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d) |
| Cohort variable | **the regime lookback N in `spy_close > mean(spy_close[-(N+1):-1])`** |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **SPY > 200d SMA — swept over N = 150/200/250/300/350 and switched off entirely; `SMA200 *` is the production setting and `regime off` the dropped-filter reference** |
| Rows overlap | **variant sweep, not a partition — rows do not sum to `regime off`** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range) |
| Ranking gate | QullamaggieRanking >= 40 |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 500K |
| Cooldown | 30 calendar days, applied after the regime gate as in production |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

Each row is the **whole** signal population under that regime setting, so the rows overlap and do not sum to `regime off` — a signal clearing SMA150 usually clears SMA350 too. `SMA200 *` is the production setting; `regime off` applies no market filter at all. The gate runs before the 30-day cooldown, as in production, so a different lookback also changes which triggers win the cooldown slot — the row counts are not a pure subset relationship either.

Both windows deliberately straddle a bear market, since that is the only condition under which a regime filter can pay for itself: 2006-2010 covers the 2008 crash, 2018-2023 covers 2018 Q4, the 2020 Covid crash and 2022. They are **not** comparable with the other cohort studies, which all run 2015-2026.

```text
### 2006-01-01 – 2010-12-31 — bk50d_s20_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          407   +26.15   +33.22    76.9     2.993    9.12    -40.11
SMA200 *        240   +14.85   +24.07    68.3     1.839    5.23    -43.90
SMA250          131    +9.60   +17.67    61.1     1.106    3.28    -51.53
SMA300          116    +5.98   +15.24    58.6     0.914    2.84    -54.43
SMA350           74    +7.32   +16.76    60.8     0.931    2.91    -62.01
regime off      765   +31.28   +40.73    78.4     3.214   10.05    -46.85

### 2006-01-01 – 2010-12-31 — bk50d_s16_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          437   +27.32   +33.43    76.2     3.173    9.26    -37.52
SMA200 *        264   +15.81   +24.21    68.2     1.959    5.35    -39.94
SMA250          149   +10.00   +18.77    62.4     1.313    3.62    -42.52
SMA300          129    +7.33   +15.57    58.9     1.031    2.97    -43.46
SMA350           83    +5.77   +15.59    59.0     0.971    2.85    -46.18
regime off      854   +30.04   +38.87    76.8     3.003    9.06    -46.87

### 2006-01-01 – 2010-12-31 — bk50d_s12_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          468   +25.45   +31.76    75.6     2.427    7.53    -46.85
SMA200 *        295   +15.33   +22.68    68.1     1.561    4.59    -49.00
SMA250          183   +10.55   +16.68    62.8     0.978    3.04    -54.58
SMA300          157    +7.45   +12.77    58.6     0.701    2.39    -57.87
SMA350          110    +6.61   +11.22    58.2     0.561    2.09    -63.09
regime off      978   +27.35   +35.59    75.5     2.331    7.14    -55.01

### 2018-01-01 – 2023-12-31 — bk50d_s20_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          740   +49.63   +59.69    78.2     3.703   10.89    -57.75
SMA200 *        714   +51.75   +60.89    79.1     3.799   11.35    -58.51
SMA250          702   +54.69   +64.27    81.2     4.108   12.65    -57.85
SMA300          723   +57.31   +65.83    82.3     4.346   13.75    -57.31
SMA350          740   +57.98   +67.11    83.2     4.438   14.32    -57.63
regime off      945   +46.36   +56.09    76.1     3.245    9.13    -60.30

### 2018-01-01 – 2023-12-31 — bk50d_s16_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          823   +45.12   +56.60    75.6     3.353    9.39    -57.89
SMA200 *        792   +47.26   +58.15    76.6     3.486    9.93    -58.58
SMA250          769   +50.63   +61.18    78.3     3.710   10.79    -58.36
SMA300          789   +53.03   +62.76    79.5     3.927   11.69    -57.92
SMA350          802   +55.41   +64.73    80.7     4.092   12.45    -57.92
regime off     1040   +41.76   +52.88    73.3     2.903    7.87    -61.06

### 2018-01-01 – 2023-12-31 — bk50d_s12_v2.0

Regime            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
SMA150          921   +43.79   +55.22    74.3     3.140    8.62    -59.98
SMA200 *        890   +44.78   +56.78    74.9     3.268    9.07    -60.38
SMA250          864   +48.28   +59.70    76.6     3.461    9.79    -60.23
SMA300          881   +49.76   +60.89    77.9     3.665   10.59    -59.13
SMA350          892   +52.48   +62.62    78.9     3.799   11.16    -59.40
regime off     1166   +39.45   +50.86    71.9     2.708    7.23    -62.36

```
