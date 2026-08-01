# Qullamaggie Limit-Order Fill Sensitivity — 366d Cohorts

Run date: 2026-08-01 08:48:38 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar) |
| Cohorts | bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d) |
| Cohort variable | **entry convention — next-open vs EOD vs a resting limit order** |
| Entry | **three conventions reported side by side; see Baselines and Limit sweep below** |
| Filter under study | none — the entry convention is the variable, so the full production chain applies |
| Limit sweep | X% = 0%, 1%, 2%, 3%, 4%, 5% |
| Limit order rule | resting limit at signal_day_close x (1 - X%), good for 30 calendar days; fills on the first day in that window whose low <= limit price, else expires unfilled |
| Baselines | next-open — buy at the next trading day's adjusted open (canonical v2.0); EOD — buy at signal-day close (pre-v2.0, retained for continuity) |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x, vol_dry_up<90% (no tight_range) |
| Ranking gate | QullamaggieRanking >= 40 |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 500K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min **10** losers (turtlex/backtest/metrics.py) |

## Results

### bk50d_s20_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   88.6%   737   +45.0%   +60.4%   76.5%    3.562   10.08   -59.80
EOD (legacy)       88.6%   737   +45.0%   +60.8%   76.7%    3.619   10.26   -59.39
----------------------------------------------------------------------------------
0%                 97.0%   717   +44.9%   +60.0%   76.6%    3.522    9.97   -60.18
1%                 94.4%   698   +46.4%   +60.7%   76.2%    3.568   10.09   -60.11
2%                 90.5%   676   +47.0%   +62.8%   77.4%    3.770   10.80   -59.94
3%                 85.5%   640   +48.5%   +64.7%   77.3%    3.919   11.31   -59.45
4%                 81.6%   610   +48.8%   +63.5%   77.0%    3.724   10.77   -61.32
5%                 76.4%   571   +50.1%   +64.2%   77.4%    3.693   10.70   -62.46
```

### bk50d_s16_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   88.3%   828   +42.4%   +58.1%   74.0%    3.327    9.07   -59.62
EOD (legacy)       88.3%   828   +41.6%   +58.3%   74.2%    3.366    9.19   -59.25
----------------------------------------------------------------------------------
0%                 97.0%   806   +41.6%   +56.7%   73.8%    3.223    8.76   -59.96
1%                 94.3%   785   +42.5%   +58.0%   73.9%    3.320    9.03   -59.57
2%                 90.4%   758   +44.2%   +59.7%   74.7%    3.475    9.53   -59.69
3%                 85.4%   718   +46.3%   +60.7%   74.7%    3.558    9.79   -59.54
4%                 81.8%   685   +45.6%   +59.7%   74.6%    3.419    9.42   -60.42
5%                 77.2%   647   +45.0%   +60.2%   75.1%    3.376    9.32   -61.86
```

### bk50d_s12_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   88.2%   946   +40.2%   +56.5%   73.2%    3.230    8.65   -58.91
EOD (legacy)       88.2%   946   +40.2%   +56.9%   73.2%    3.278    8.82   -58.61
----------------------------------------------------------------------------------
0%                 96.9%   919   +39.8%   +55.5%   73.0%    3.148    8.41   -59.44
1%                 94.1%   893   +41.1%   +56.5%   72.9%    3.224    8.60   -59.02
2%                 90.2%   861   +41.5%   +58.1%   73.5%    3.377    9.06   -58.74
3%                 84.9%   811   +42.0%   +58.5%   73.2%    3.412    9.21   -58.88
4%                 81.1%   772   +42.6%   +57.5%   73.4%    3.290    8.93   -59.92
5%                 76.3%   729   +44.0%   +58.1%   74.2%    3.259    8.87   -61.18
```

## Monthly Seasonality (EOD baseline)

Each cell is `Mean%|N` for trades entered in that calendar month (entry = signal day), using the EOD baseline (buy at signal-day close, hold 366 calendar days). `·` = no trades that month. The Mean%/N columns on the right are the year's aggregate across all its months.

### bk50d_s20_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -24.3|3 -27.4|4       ·  +1.2|3       · -31.4|1 -32.9|1       ·       ·       · +40.7|2       · |  -11.6%   14
 2016 |       ·       ·+44.1|13+31.6|41  +5.6|3  +5.1|7 +10.5|6 +86.7|4 +60.0|4 +42.9|3       · +33.0|3 |  +33.3%   84
 2017 | +10.5|3+134.2|1+102.4|2       · +62.6|2 +43.6|2 +52.2|3  +3.0|3 +71.6|1 +60.2|1       · +75.5|3 |  +52.7%   21
 2018 | +22.7|6       · +28.9|1 -74.2|1       ·       ·       ·       ·       ·       ·       ·       · |  +11.3%    8
 2019 |       ·  -2.2|6+108.0|2 -34.4|1       · -69.4|1 -28.1|5 +18.4|1       · +77.9|3       · +75.1|3 |  +19.8%   22
 2020 | +26.5|2+446.6|3       ·       ·+95.3|130+72.2|88+55.7|17+74.8|18+225.2|4 +86.8|6+58.8|15+38.4|29 |  +82.8%  312
 2021 |+69.7|35+46.0|13  -2.3|2  +1.2|1       · +51.4|1 -69.8|1 +53.8|1 +18.7|1 -80.3|1 +36.1|1       · |  +53.4%   57
 2022 | -50.7|1 +14.3|1 -46.0|8  -0.2|3       ·       ·       ·       ·       ·       ·+23.3|15+19.1|13 |   +4.7%   41
 2023 | +23.4|9  +9.7|8 -21.0|1 +33.9|2 +39.1|6 +29.5|7+33.7|16       · +68.4|3       · +93.6|3 -2.6|12 |  +26.4%   67
 2024 |+51.2|11 +21.4|7 -31.7|3 +56.7|3 +31.5|7+195.9|1+194.2|4  +9.7|7 +98.2|3 +67.5|7 +17.4|6 -51.4|1 |  +47.8%   60
 2025 |  +3.5|2       ·       ·       · +50.6|4+164.7|29+112.9|16       ·       ·       ·       ·       · | +133.2%   51
```

### bk50d_s16_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -24.3|3 -23.3|5  -3.0|1  -6.5|4  -9.3|1 +18.6|2 -32.9|1       ·       · -34.5|1  +2.2|4       · |  -11.3%   22
 2016 |       ·       ·+40.2|16+36.6|40 +23.6|5  +0.5|8 +11.0|6 +60.8|7 +81.2|3 +42.9|3       · +25.2|4 |  +34.7%   92
 2017 | +10.5|3+124.1|2+101.8|2       · +41.7|3 +43.6|2 +59.8|4  +3.0|3 +71.6|1 +60.2|1       · +70.3|3 |  +53.6%   24
 2018 | +31.0|5       · +28.9|1 +64.0|2       ·       ·       ·+107.2|1       ·       ·       · -41.5|1 |  +37.8%   10
 2019 |       ·  +0.2|7+108.0|2 -33.8|1       ·  +0.1|2 -28.1|5 +55.9|2       · +64.7|4       · +75.1|3 |  +24.6%   26
 2020 | +26.5|2+446.6|3       ·       ·+96.0|137+68.8|86+57.3|18+83.5|16+181.2|7 +61.3|9+48.5|17+35.8|31 |  +81.5%  326
 2021 |+67.7|36+38.4|17  -2.3|2  +7.4|3       · +49.8|3 -69.8|1 +53.8|1 +18.7|1 -30.0|2  +1.4|2       · |  +47.1%   68
 2022 | +11.6|2 +24.4|2 -46.0|8 +10.1|6       ·       ·       ·       ·       ·       ·+23.3|15+11.1|15 |   +5.8%   48
 2023 |+17.1|12 +11.7|8 -27.3|2 +10.9|3 +31.9|7 +25.3|8+19.5|22 +33.0|1 +68.4|3       · +72.7|6 -1.8|13 |  +21.0%   85
 2024 |+57.6|11 +21.3|7 -41.1|4 +56.7|3 +32.2|7+107.8|2+150.8|5 +3.7|13 +86.4|4 +74.1|7  +6.2|7 -51.4|1 |  +40.7%   71
 2025 |  +3.5|2 +69.0|1       ·       · +97.5|7+187.5|29+123.2|17       ·       ·       ·       ·       · | +148.0%   56
```

### bk50d_s12_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -24.3|3 -26.4|7  -0.0|1  -6.5|4  -7.1|1 +31.3|3 -32.9|1       ·       ·  -9.7|2  +3.6|4       · |   -9.1%   26
 2016 |       ·       ·+39.7|21+37.6|41 +23.6|5  -2.2|9 +29.6|7 +60.8|7 +95.6|4 +25.4|4  +7.6|1 +28.8|4 |  +36.0%  103
 2017 | +28.9|6 +68.8|3+101.8|2       · +41.7|3 +43.6|2 +60.0|4  -3.5|5 +71.6|1 +60.2|1       · +70.3|3 |  +45.4%   30
 2018 | +31.0|5       · +28.9|1 +40.9|3  -1.6|2 -28.2|1       · +37.3|2       ·       ·       · -41.5|1 |  +20.6%   15
 2019 |       · +29.1|9  -7.2|1  -9.9|3       ·  +0.1|2 -28.1|5 +55.9|2       · +64.7|4       · +46.1|5 |  +22.1%   31
 2020 | +26.5|2+446.6|3       ·       ·+95.0|140+68.7|83+55.8|25+83.5|21+189.2|5+56.1|11+46.5|19+35.5|33 |  +79.4%  342
 2021 |+67.7|36+49.4|21  -2.3|2 +11.2|5 +48.1|3 +35.0|4 -69.8|1 +53.8|1 +18.7|1  -9.9|3  +1.4|2       · |  +47.9%   79
 2022 | +13.1|2  +6.0|4 -1.2|13  +1.9|8       ·       ·       ·       ·       ·       ·+18.3|18+13.4|16 |   +9.7%   61
 2023 |+18.5|15 +12.2|8 -27.3|2 +10.9|3 +84.5|9 +26.2|8+19.5|30 +50.5|2 +68.4|3       · +86.6|8+10.2|13 |  +30.1%  101
 2024 |+73.7|13 +23.2|8 -41.1|4 +40.0|4 +28.9|8+107.8|2+130.4|6 +9.1|15+116.2|6+79.4|12  +1.4|8 -51.4|1 |  +47.3%   87
 2025 |  +3.5|2+113.2|2       ·       · +79.6|9+161.1|35+117.1|23       ·       ·       ·       ·       · | +130.7%   71
```

## Findings & Caveats

- **30-day resting window**: unlike a single next-day-only attempt, the order stays live for 30 calendar days and fills on the *first* day the low touches the limit price. This raises fill rates substantially versus a next-day-only rule, but it also means higher-X% fills are increasingly dominated by trades that took most of the window to retrace that far — those signals have effectively already spent part of their 366d hold going nowhere (or down) before the position even opens, which the raw per-trade return doesn't capture (it's measured from the fill day, not the signal day).

- **Selection effect**: a limit fill at a deep discount means the stock pulled back after triggering the breakout signal — this is not a neutral resampling of the same trade population as the EOD baseline; it systematically selects for breakouts that gave back some of the signal-day gain before continuing (or failing), which can bias mean/median returns in either direction depending on regime.

- **Fill% still drops with X%, just more slowly than a next-day-only rule**: rows with N well under 30 are not statistically reliable, even if the ratios look attractive.

- **Fill/exit price convention**: consistent with qullamaggie-backtest-v4.py, all prices are split/dividend-adjusted close/high/low; entry is exactly the limit price (no slippage beyond the modeled discount), and hold length is measured in calendar days from the fill day, not the original signal day.

- **No execution costs**: no commissions, spread, or partial fills are modeled; a real resting limit order also carries queue-priority and gap risk not captured here (e.g. a gap-down open below the limit price would fill better than modeled).
