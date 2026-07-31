# Qullamaggie Limit-Order Fill Sensitivity — 366d Cohorts

Run date: 2026-08-01 01:34:45 Tallinn time

Period: 2010-01-01 – 2026-06-26  |  Hold: 366d (calendar)

## Configuration

| Parameter | Value |
|---|---|
| Cohorts | bk50d_s20_v2.0, bk50d_s16_v2.0, bk50d_s12_v2.0 (366d) |
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
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py) |

## Results

### bk50d_s20_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF
-------------------------------------------------------------------------
next-open (v2.0)   89.3%   794   +43.2%   +57.9%   75.6%    3.334    9.28
EOD (legacy)       89.3%   794   +42.5%   +58.2%   75.7%    3.390    9.45
-------------------------------------------------------------------------
0%                 97.2%   774   +42.6%   +57.4%   75.5%    3.301    9.18
1%                 94.5%   752   +43.7%   +57.6%   75.0%    3.310    9.20
2%                 90.1%   723   +45.1%   +59.7%   75.9%    3.495    9.81
3%                 85.4%   686   +46.8%   +61.1%   75.9%    3.601   10.19
4%                 81.2%   652   +47.7%   +61.0%   75.6%    3.494    9.90
5%                 75.9%   609   +49.1%   +62.0%   76.4%    3.492    9.92
```

### bk50d_s16_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF
-------------------------------------------------------------------------
next-open (v2.0)   89.1%   897   +40.7%   +55.7%   73.2%    3.163    8.54
EOD (legacy)       89.1%   897   +40.4%   +56.0%   73.5%    3.200    8.65
-------------------------------------------------------------------------
0%                 97.1%   874   +39.8%   +54.5%   73.1%    3.073    8.28
1%                 94.3%   849   +41.1%   +55.2%   73.0%    3.134    8.43
2%                 90.1%   815   +41.6%   +56.8%   73.6%    3.270    8.87
3%                 85.2%   772   +43.5%   +57.5%   73.6%    3.325    9.05
4%                 81.3%   735   +43.1%   +57.5%   73.5%    3.253    8.85
5%                 76.6%   692   +44.4%   +58.1%   74.1%    3.228    8.82
```

### bk50d_s12_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF
-------------------------------------------------------------------------
next-open (v2.0)   89.1%  1039   +37.1%   +53.5%   72.2%    3.002    7.98
EOD (legacy)       89.1%  1039   +37.6%   +53.8%   72.2%    3.044    8.10
-------------------------------------------------------------------------
0%                 97.0%  1009   +37.2%   +52.4%   72.0%    2.915    7.73
1%                 94.2%   979   +37.4%   +52.9%   71.7%    2.961    7.84
2%                 89.8%   937   +38.7%   +54.5%   72.3%    3.094    8.22
3%                 84.3%   879   +39.8%   +54.4%   71.9%    3.088    8.24
4%                 80.1%   834   +41.2%   +54.7%   72.1%    3.043    8.15
5%                 75.4%   787   +42.7%   +55.5%   72.9%    3.078    8.26
```

## Monthly Seasonality (EOD baseline)

Each cell is `Mean%|N` for trades entered in that calendar month (entry = signal day), using the EOD baseline (buy at signal-day close, hold 366 calendar days). `·` = no trades that month. The Mean%/N columns on the right are the year's aggregate across all its months.

### bk50d_s20_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2010 | +71.7|2 -33.1|1       ·  -4.9|3       ·       ·       ·       · -25.9|1 +88.6|1       · -11.8|5 |   +7.7%   13
 2011 |       ·       ·       ·       ·       ·       ·       ·       ·       · +12.4|6 +53.0|1 +84.7|1 |  +26.5%    8
 2012 |+174.3|1 -10.4|8 +57.7|1       ·       ·       ·+108.6|1 +23.9|4       ·       ·+106.1|1+101.9|1 |  +33.0%   17
 2013 |+147.4|2       ·       · +17.5|2 +31.4|1       · -23.8|1+100.1|1 +44.9|1       · -47.3|1       · |  +48.4%    9
 2014 |  -2.1|2 -50.1|1 -59.2|1 +68.9|2 -36.9|1 +96.0|1       ·       ·       ·       ·       · +17.2|2 |  +11.8%   10
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
 2010 | +71.7|2 -33.1|1       ·  -5.4|3       ·       ·       ·       · -25.9|1 +27.8|2       ·  -1.0|4 |   +9.2%   13
 2011 | +37.6|1       ·       ·       ·       ·       ·       ·       ·       · +12.6|6 +53.0|1 +84.7|1 |  +27.9%    9
 2012 |+105.4|3 -11.6|9 +87.3|2       ·       ·       · +34.8|3 +40.2|6 +47.1|1       ·+106.1|1       · |  +35.4%   25
 2013 |+147.4|2       ·       · +17.5|2 +42.2|2       · -23.8|1+100.1|1 +44.9|1       · -47.3|1       · |  +48.8%   10
 2014 |  -2.1|2 -30.3|2 -59.2|1 +68.9|2 -36.9|1 +96.0|1       ·       ·       ·       · +63.5|1 +17.2|2 |  +14.2%   12
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
 2010 | +39.5|4 -33.1|1       ·  -3.8|3       ·       ·       ·       · -79.8|1 +23.8|3 -25.8|1  -8.1|6 |   +1.6%   19
 2011 | +37.6|1 -38.8|1       ·       ·       ·       ·       ·       ·       · +10.1|9 +53.0|1 +77.5|3 |  +25.0%   15
 2012 | +56.3|4 -5.1|10 +55.2|3       ·       · -18.1|1 +39.1|4 +40.5|7 +46.1|2       ·+106.1|1 +18.6|1 |  +29.6%   33
 2013 |+147.4|2       ·  -5.0|1 +17.5|2 +42.2|2       · -23.8|1+100.1|1 +44.9|1       · -47.3|1       · |  +43.9%   11
 2014 | -14.6|3 -30.3|2 -47.1|2 +68.9|2 +42.9|2 +96.0|1       ·       ·       ·       · +63.5|1 +17.2|2 |  +14.6%   15
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
