# Qullamaggie Market-Cap Cohort Analysis

Run date: 2026-08-02 23:47:45 Tallinn time

> **⚠ Descriptive only — this cohort variable carries look-ahead.** `company.market_cap` is a current snapshot with no history, so a 2015 trade is bucketed by its company's market cap *today*. The `(<300M)` bucket is therefore not 'small companies' but 'companies that are small in 2026' — ones that fell or stagnated over the following decade — and `(>100B)` is companies that grew into it. Trades are sorted partly by their own outcome, so a 'large caps did better' reading would be an artifact, not a finding. Every other cohort study measures its variable on the signal date; this one cannot until a point-in-time cap (shares outstanding x close) is available.

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d) |
| Cohort variable | **`company.market_cap` — a current snapshot, NOT a signal-date value** |
| Entry | next trading day's split/dividend-adjusted open |
| Filter under study | **`market_cap >= 1.5B` — removed, otherwise the three sub-floor cohorts would be empty; returns as the `>=1.5B (cap)` row** |
| ⚠ Look-ahead | **market_cap has no history, so a 2015 trade is bucketed by its 2026 cap — trades are sorted partly by their own outcome. Descriptive only; do not read as 'size predicts returns'** |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range) |
| Ranking gate | QullamaggieRanking >= 40 |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, excl. Comm/RE — **no market-cap floor** |
| Universe read | 2 market-cap slabs, lossless vs one wide read (see docstring) |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 5 losers (turtlex/backtest/metrics.py) |

## Results

```text
### bk50d_s20_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         334   -23.18    -3.35    32.9    -0.081    0.89    -86.95
[300M-1B)       469    +8.53   +23.26    54.6     0.852    2.52    -76.16
[1B-1.5B)       190   +11.62   +28.24    55.8     1.048    2.91    -79.66
[1.5-3B)        406   +30.07   +41.43    63.5     1.981    4.92    -62.76
[3-10B)         612   +47.57   +63.62    79.2     4.047   11.80    -56.57
[10-30B)        224   +48.25   +64.28    80.8     4.669   14.47    -53.35
[30-100B)       118   +58.89   +93.12    86.4    14.658   45.67    -24.62
(>100B)          21   +56.32   +80.93    95.2       n/a  252.67     -6.75
─────────────────────────────────────────────────────────────────────────
ALL            2374   +26.91   +41.28    63.9     1.684    4.38    -74.36
>=1.5B (cap)   1381   +44.26   +59.98    75.7     3.635    9.99    -57.09

### bk50d_s16_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         413   -23.18    -2.74    32.7    -0.067    0.91    -87.24
[300M-1B)       572    +8.56   +22.69    55.4     0.814    2.45    -78.09
[1B-1.5B)       229   +13.45   +28.09    55.9     1.053    2.91    -78.50
[1.5-3B)        483   +26.94   +41.81    62.1     1.924    4.77    -64.70
[3-10B)         689   +43.68   +62.89    77.9     3.838   10.89    -58.25
[10-30B)        237   +47.00   +62.28    79.3     4.523   13.65    -53.27
[30-100B)       119   +57.22   +91.86    84.9    11.805   36.38    -31.10
(>100B)          20   +61.13   +83.83    95.0       n/a  249.27     -6.75
─────────────────────────────────────────────────────────────────────────
ALL            2762   +23.69   +39.53    62.5     1.564    4.07    -75.44
>=1.5B (cap)   1548   +41.42   +58.72    74.0     3.387    9.10    -58.90

### bk50d_s12_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         483   -23.19    -4.68    33.5    -0.115    0.84    -86.35
[300M-1B)       693    +6.04   +20.40    53.1     0.726    2.26    -78.63
[1B-1.5B)       286   +10.27   +22.89    54.5     0.809    2.47    -81.13
[1.5-3B)        568   +23.04   +37.87    62.1     1.715    4.37    -66.21
[3-10B)         792   +43.28   +62.57    76.8     3.780   10.43    -57.76
[10-30B)        272   +44.82   +59.44    76.1     3.722   10.63    -58.67
[30-100B)       131   +48.73   +89.06    82.4     9.629   28.40    -34.56
(>100B)          23   +65.94   +92.59    95.7       n/a  316.33     -6.75
─────────────────────────────────────────────────────────────────────────
ALL            3248   +19.49   +36.78    61.1     1.429    3.75    -75.97
>=1.5B (cap)   1786   +39.21   +56.57    72.7     3.154    8.35    -60.08

```
