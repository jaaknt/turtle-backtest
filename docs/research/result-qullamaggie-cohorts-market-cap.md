# Qullamaggie Market-Cap Cohort Analysis

Run date: 2026-08-09 18:55:19 Tallinn time

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
| Ranking gate | QullamaggieRanking >= 44 |
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
(<300M)         347   -24.06    -6.04    32.0    -0.146    0.80    -86.59
[300M-1B)       488    +8.23   +21.85    55.3     0.822    2.48    -75.10
[1B-1.5B)       206   +11.70   +26.97    55.8     0.991    2.79    -79.54
[1.5-3B)        429   +28.76   +42.99    63.6     2.027    5.03    -65.18
[3-10B)         712   +44.17   +60.97    78.4     3.860   11.05    -56.16
[10-30B)        246   +46.71   +60.04    78.0     4.167   12.25    -54.15
[30-100B)       130   +50.79   +82.59    83.8     9.911   30.04    -32.12
(>100B)          24   +39.08   +68.17    91.7       n/a  148.77     -6.75
─────────────────────────────────────────────────────────────────────────
ALL            2582   +25.70   +39.94    63.9     1.647    4.31    -73.87
>=1.5B (cap)   1541   +41.49   +57.76    74.9     3.454    9.41    -57.40

### bk50d_s16_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         430   -23.18    -5.01    32.3    -0.122    0.83    -86.93
[300M-1B)       600    +8.56   +21.39    56.2     0.780    2.39    -76.75
[1B-1.5B)       247   +13.13   +28.23    56.3     1.050    2.92    -78.49
[1.5-3B)        506   +29.00   +42.90    62.8     1.999    4.96    -64.86
[3-10B)         798   +40.93   +60.23    76.7     3.659   10.22    -58.05
[10-30B)        261   +44.29   +60.29    76.6     4.271   12.19    -51.79
[30-100B)       136   +53.87   +83.82    84.6     9.957   30.83    -32.64
(>100B)          22   +39.08   +76.61    90.9       n/a  153.22     -6.75
─────────────────────────────────────────────────────────────────────────
ALL            3000   +22.90   +38.75    62.7     1.555    4.07    -74.95
>=1.5B (cap)   1723   +39.80   +57.22    73.4     3.323    8.89    -58.39

### bk50d_s12_v2.0

Cohort            N     Med%    Mean%    Win%   Sortino      PF   CVaR95%
─────────────────────────────────────────────────────────────────────────
(<300M)         471   -23.18    -5.73    33.1    -0.141    0.80    -86.43
[300M-1B)       669    +6.74   +20.85    54.9     0.756    2.33    -77.05
[1B-1.5B)       283   +12.26   +24.32    55.8     0.860    2.58    -80.92
[1.5-3B)        539   +26.25   +41.77    63.8     1.940    4.90    -66.48
[3-10B)         817   +41.00   +60.65    76.6     3.636   10.10    -58.36
[10-30B)        270   +44.40   +58.76    75.9     3.849   10.95    -56.27
[30-100B)       138   +50.20   +81.81    81.9     9.391   26.70    -32.30
(>100B)          22   +43.15   +99.68    90.9       n/a  199.07     -6.75
─────────────────────────────────────────────────────────────────────────
ALL            3209   +21.15   +37.25    62.0     1.469    3.87    -75.61
>=1.5B (cap)   1786   +38.61   +56.78    73.2     3.234    8.64    -59.55

```
