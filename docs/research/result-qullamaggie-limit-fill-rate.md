# Limit-Order Fill Rate — bk50d_s12_v1.3_roc100

Run date: 2026-07-23

Period: 2010-06-01 – 2026-07-23

## Configuration

| Parameter | Value |
|---|---|
| Signal | bk50d_s12_v1.3_roc100: 50d-high breakout, close >12% above SMA50, 12m ROC < 100% |
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

N signals: 3011  |  N attempted (>=1 bar after signal): 3008  |  N with full 90d window of data: 2914

Fill% = n_filled / N attempted. MedD/MeanD = median/mean trading days from the signal day to the fill day, filled orders only (1 = fills on the first trading day after the signal).

```text
  X%  |         Y=30d          |         Y=60d          |         Y=90d         
      |   Fill%   MedD  MeanD |   Fill%   MedD  MeanD |   Fill%   MedD  MeanD
-----------------------------------------------------------------------------
  0%  |   97.0%    1.0    1.5 |   97.7%    1.0    1.7 |   97.9%    1.0    1.8
  1%  |   93.0%    1.0    2.2 |   94.6%    1.0    2.6 |   95.4%    1.0    3.0
  2%  |   86.9%    1.0    3.2 |   89.9%    2.0    4.0 |   91.3%    2.0    4.7
  3%  |   80.7%    2.0    4.2 |   85.1%    2.0    5.5 |   87.0%    3.0    6.5
  4%  |   74.5%    3.0    5.1 |   80.6%    4.0    6.9 |   83.2%    4.0    8.3
  5%  |   68.5%    4.0    6.1 |   75.3%    5.0    8.2 |   78.8%    5.0   10.1
```

### n_filled per cell

```text
  X%  | n_filled Y=30d | n_filled Y=60d | n_filled Y=90d
--------------------------------------------------------
  0%  |           2919 |           2938 |           2945
  1%  |           2797 |           2845 |           2869
  2%  |           2613 |           2704 |           2745
  3%  |           2426 |           2559 |           2616
  4%  |           2241 |           2423 |           2504
  5%  |           2059 |           2265 |           2369
```

## Findings & Caveats

- **Truncated windows near the end of data**: signals in the last 90 calendar days of the period have fewer forward bars than the window nominally allows, so Fill% for the longer windows is slightly understated for those signals (denominator counts every signal with at least one following bar, matching scripts/qullamaggie-cohorts-limit-order.py).

- **First-touch convention**: a fill is the first day the low touches the limit; MedD/MeanD therefore measure time to the *first* touch, not how long the price stayed below the limit.

- **No execution costs or queue effects**: touching the limit is assumed to fill in full; a real resting order carries queue-priority risk at exactly-touched prices, and a gap-down open below the limit would fill at the open (better than modeled).
