# Limit-Order Fill Rate — bk50d_s12_v2.0

Run date: 2026-08-01 13:00:50 Tallinn time

Period: 2010-06-01 – 2026-08-01

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
| Min avg vol (20d) | >= 500K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Ranking gate | QullamaggieRanking >= 40 |

## Results

N signals: 1691  |  N attempted (>=1 bar after signal): 1691  |  N with full 90d window of data: 1623

Fill% = n_filled / N attempted. MedD/MeanD = median/mean trading days from the signal day to the fill day, filled orders only (1 = fills on the first trading day after the signal).

```text
  X%  |         Y=30d          |         Y=60d          |         Y=90d         
      |   Fill%   MedD  MeanD |   Fill%   MedD  MeanD |   Fill%   MedD  MeanD
-----------------------------------------------------------------------------
  0%  |   97.2%    1.0    1.5 |   97.6%    1.0    1.6 |   97.8%    1.0    1.6
  1%  |   94.3%    1.0    2.0 |   95.3%    1.0    2.2 |   95.7%    1.0    2.4
  2%  |   89.9%    1.0    2.7 |   91.9%    1.0    3.3 |   92.6%    1.0    3.6
  3%  |   84.3%    2.0    3.5 |   87.2%    2.0    4.4 |   88.5%    2.0    5.1
  4%  |   79.3%    2.0    4.4 |   82.7%    3.0    5.5 |   85.0%    3.0    6.6
  5%  |   73.6%    3.0    5.2 |   78.6%    3.0    6.8 |   81.3%    4.0    8.2
```

### n_filled per cell

```text
  X%  | n_filled Y=30d | n_filled Y=60d | n_filled Y=90d
--------------------------------------------------------
  0%  |           1643 |           1651 |           1653
  1%  |           1595 |           1612 |           1618
  2%  |           1521 |           1554 |           1566
  3%  |           1425 |           1475 |           1497
  4%  |           1341 |           1399 |           1437
  5%  |           1245 |           1329 |           1374
```

## Findings & Caveats

- **Truncated windows near the end of data**: signals in the last 90 calendar days of the period have fewer forward bars than the window nominally allows, so Fill% for the longer windows is slightly understated for those signals (denominator counts every signal with at least one following bar, matching scripts/qullamaggie-cohorts-limit-order.py).

- **First-touch convention**: a fill is the first day the low touches the limit; MedD/MeanD therefore measure time to the *first* touch, not how long the price stayed below the limit.

- **No execution costs or queue effects**: touching the limit is assumed to fill in full; a real resting order carries queue-priority risk at exactly-touched prices, and a gap-down open below the limit would fill at the open (better than modeled).
