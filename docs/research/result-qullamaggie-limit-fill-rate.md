# Limit-Order Fill Rate — bk50d_s12_v1.2_roc100

Run date: 2026-07-14

Period: 2010-06-01 – 2026-07-14

## Configuration

| Parameter | Value |
|---|---|
| Signal | bk50d_s12_v1.2_roc100: 50d-high breakout, close >12% above SMA50, 12m ROC < 100% |
| Limit sweep | X% = 0%, 1%, 2%, 3%, 4%, 5% |
| Window sweep | Y = 30d, 60d, 90d (calendar days after the signal day) |
| Fill rule | resting limit at signal_day_close x (1 - X%), eligible from the day after the signal; fills on the first trading day whose low <= limit price within Y calendar days, else expires unfilled (adjusted prices, same convention as scripts/qullamaggie-cohorts-limit-order.py) |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90%, no tight_range |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 500K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |

## Results

N signals: 2818  |  N attempted (>=1 bar after signal): 2817  |  N with full 90d window of data: 2732

Fill% = n_filled / N attempted. MedD/MeanD = median/mean trading days from the signal day to the fill day, filled orders only (1 = fills on the first trading day after the signal).

```text
  X%  |         Y=30d          |         Y=60d          |         Y=90d         
      |   Fill%   MedD  MeanD |   Fill%   MedD  MeanD |   Fill%   MedD  MeanD
-----------------------------------------------------------------------------
  0%  |   96.9%    1.0    1.5 |   97.7%    1.0    1.7 |   97.9%    1.0    1.9
  1%  |   92.8%    1.0    2.2 |   94.5%    1.0    2.7 |   95.3%    1.0    3.1
  2%  |   86.7%    1.0    3.2 |   89.9%    2.0    4.1 |   91.3%    2.0    4.8
  3%  |   80.3%    2.0    4.2 |   84.8%    3.0    5.6 |   86.8%    3.0    6.6
  4%  |   74.2%    3.0    5.2 |   80.4%    4.0    7.0 |   83.1%    4.0    8.5
  5%  |   68.1%    4.0    6.1 |   75.1%    5.0    8.3 |   78.7%    6.0   10.2
```

### n_filled per cell

```text
  X%  | n_filled Y=30d | n_filled Y=60d | n_filled Y=90d
--------------------------------------------------------
  0%  |           2731 |           2751 |           2758
  1%  |           2614 |           2661 |           2686
  2%  |           2442 |           2532 |           2571
  3%  |           2262 |           2389 |           2445
  4%  |           2091 |           2264 |           2342
  5%  |           1919 |           2116 |           2216
```

## Findings & Caveats

- **Truncated windows near the end of data**: signals in the last 90 calendar days of the period have fewer forward bars than the window nominally allows, so Fill% for the longer windows is slightly understated for those signals (denominator counts every signal with at least one following bar, matching scripts/qullamaggie-cohorts-limit-order.py).

- **First-touch convention**: a fill is the first day the low touches the limit; MedD/MeanD therefore measure time to the *first* touch, not how long the price stayed below the limit.

- **No execution costs or queue effects**: touching the limit is assumed to fill in full; a real resting order carries queue-priority risk at exactly-touched prices, and a gap-down open below the limit would fill at the open (better than modeled).
