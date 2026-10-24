# Limit-Order Fill Rate — bk50d_s12_v2.0

Run date: 2026-10-24 18:13:03 Tallinn time

Period: 2010-06-01 – 2026-10-24

## Configuration

| Parameter | Value |
|---|---|
| Signal | bk50d_s12_v2.0: 50d-high breakout, close >12% above SMA50, 12m ROC < 100% |
| Limit sweep | X% = 0%, 1%, 2%, 3%, 4%, 5% |
| Window sweep | Y = 30d, 60d, 90d (calendar days after the signal day) |
| Fill rule | resting limit at signal_day_close x (1 - X%), eligible from the day after the signal; fills on the first trading day whose low <= limit price within Y calendar days, else expires unfilled (adjusted prices, same convention as scripts/qullamaggie-cohorts-limit-order.py) |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, no tight_range |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Ranking gate | QullamaggieRanking >= 44 |

## Results

N signals: 2216  |  N attempted (>=1 bar after signal): 2216  |  N with full 90d window of data: 2141

Fill% = n_filled / N attempted. MedD/MeanD = median/mean trading days from the signal day to the fill day, filled orders only (1 = fills on the first trading day after the signal).

```text
  X%  |         Y=30d          |         Y=60d          |         Y=90d         
      |   Fill%   MedD  MeanD |   Fill%   MedD  MeanD |   Fill%   MedD  MeanD
-----------------------------------------------------------------------------
  0%  |   97.3%    1.0    1.4 |   98.0%    1.0    1.6 |   98.2%    1.0    1.7
  1%  |   94.8%    1.0    2.0 |   95.9%    1.0    2.3 |   96.4%    1.0    2.6
  2%  |   89.4%    1.0    2.7 |   92.1%    1.0    3.4 |   93.1%    1.0    3.9
  3%  |   84.1%    2.0    3.5 |   87.9%    2.0    4.6 |   89.2%    2.0    5.3
  4%  |   79.0%    2.0    4.4 |   83.7%    3.0    5.8 |   86.0%    3.0    7.0
  5%  |   73.6%    3.0    5.3 |   79.2%    4.0    7.0 |   82.1%    4.0    8.5
```

### n_filled per cell

```text
  X%  | n_filled Y=30d | n_filled Y=60d | n_filled Y=90d
--------------------------------------------------------
  0%  |           2157 |           2172 |           2176
  1%  |           2100 |           2126 |           2137
  2%  |           1982 |           2040 |           2062
  3%  |           1864 |           1948 |           1976
  4%  |           1751 |           1855 |           1905
  5%  |           1631 |           1754 |           1819
```

## Findings & Caveats

- **Truncated windows near the end of data**: signals in the last 90 calendar days of the period have fewer forward bars than the window nominally allows, so Fill% for the longer windows is slightly understated for those signals (denominator counts every signal with at least one following bar, matching scripts/qullamaggie-cohorts-limit-order.py).

- **First-touch convention**: a fill is the first day the low touches the limit; MedD/MeanD therefore measure time to the *first* touch, not how long the price stayed below the limit.

- **No execution costs or queue effects**: touching the limit is assumed to fill in full; a real resting order carries queue-priority risk at exactly-touched prices, and a gap-down open below the limit would fill at the open (better than modeled).
