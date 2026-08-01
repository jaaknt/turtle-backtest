# Qullamaggie Limit-Order Fill Sensitivity — 366d Cohorts

Run date: 2026-08-01 10:20:18 Tallinn time

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
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x (no tight_range) |
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
next-open (v2.0)   89.0%  1033   +44.5%   +60.3%   75.9%    3.591    9.95   -58.16
EOD (legacy)       89.0%  1033   +44.6%   +60.7%   76.0%    3.627   10.03   -57.89
----------------------------------------------------------------------------------
0%                 97.5%  1009   +44.5%   +59.7%   75.7%    3.517    9.68   -58.41
1%                 94.9%   983   +46.0%   +60.8%   75.6%    3.593    9.91   -58.23
2%                 90.9%   946   +46.7%   +62.2%   76.4%    3.728   10.37   -58.10
3%                 85.9%   894   +47.8%   +63.7%   76.8%    3.851   10.84   -58.28
4%                 81.5%   849   +48.6%   +63.7%   77.1%    3.812   10.83   -58.90
5%                 75.8%   793   +50.4%   +64.9%   77.4%    3.820   10.84   -59.87
```

### bk50d_s16_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   88.7%  1159   +41.4%   +58.0%   74.0%    3.360    9.10   -58.69
EOD (legacy)       88.7%  1159   +41.0%   +58.4%   73.9%    3.401    9.18   -58.29
----------------------------------------------------------------------------------
0%                 97.5%  1132   +40.5%   +57.3%   73.9%    3.304    8.91   -58.58
1%                 94.7%  1104   +42.2%   +58.8%   74.3%    3.427    9.28   -58.16
2%                 90.4%  1059   +43.9%   +60.6%   75.0%    3.565    9.73   -58.26
3%                 85.3%   998   +45.0%   +61.4%   75.3%    3.633    9.98   -58.31
4%                 80.9%   944   +45.1%   +60.6%   75.4%    3.531    9.71   -58.84
5%                 75.4%   885   +46.5%   +61.4%   75.5%    3.497    9.60   -60.02
```

### bk50d_s12_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   88.1%  1334   +38.4%   +56.2%   72.7%    3.180    8.44   -59.17
EOD (legacy)       88.1%  1334   +38.8%   +56.6%   72.6%    3.219    8.56   -59.03
----------------------------------------------------------------------------------
0%                 97.3%  1299   +38.2%   +55.6%   72.7%    3.114    8.25   -59.57
1%                 94.6%  1267   +39.6%   +56.9%   72.8%    3.213    8.52   -59.17
2%                 90.4%  1213   +41.0%   +58.3%   73.4%    3.325    8.88   -59.29
3%                 84.8%  1136   +42.0%   +58.7%   73.5%    3.370    9.07   -59.50
4%                 79.9%  1070   +43.2%   +58.6%   74.0%    3.298    8.94   -60.49
5%                 74.2%  1001   +44.1%   +59.0%   74.2%    3.236    8.76   -61.75
```

## Monthly Seasonality (EOD baseline)

Each cell is `Mean%|N` for trades entered in that calendar month (entry = signal day), using the EOD baseline (buy at signal-day close, hold 366 calendar days). `·` = no trades that month. The Mean%/N columns on the right are the year's aggregate across all its months.

### bk50d_s20_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -33.3|5 -25.3|5 -52.6|2  +1.2|3       · -31.4|1 -57.3|2       ·       ·       · +40.7|2       · |  -23.0%   20
 2016 |       ·       ·+48.7|25+30.8|43  -3.5|6 -4.2|14 +14.9|9 +67.8|6 +86.1|5 -16.9|3       · +43.3|5 |  +31.0%  116
 2017 | +10.5|3+134.2|1+102.4|2       · +62.6|2 +43.6|2 +52.2|3  +3.0|3 +71.6|1 +24.1|2       · +75.5|3 |  +49.8%   22
 2018 | +22.7|6       · +21.2|2 -74.2|1 -46.6|1 -18.7|1       · +41.3|1       ·       ·       ·       · |   +6.7%   12
 2019 |       · +10.8|8 +10.4|5  -3.3|2  -5.5|1  +2.7|2 -16.1|6 +46.5|2       · +80.9|4 +87.2|3 +53.3|4 |  +25.0%   37
 2020 | +26.5|2+406.6|4       ·       ·+98.5|163+71.4|139+47.3|27+80.9|21+225.2|4 +68.7|7+51.5|28+28.8|52 |  +78.2%  447
 2021 |+72.7|38+49.6|16  -2.3|2  +1.2|1       ·+114.9|7 -40.2|2 +53.8|1 +18.7|1 -80.3|1 +36.1|1       · |  +61.5%   70
 2022 | -50.7|1 +24.2|2-20.2|16  +6.0|2       ·       ·       ·       ·       ·       ·+19.9|16+16.5|15 |   +4.9%   52
 2023 |+22.0|13+25.7|11 +46.1|6 +20.4|3 +36.7|7 +23.3|9+28.5|16       · +68.4|3       · +86.3|4+11.5|18 |  +28.7%   90
 2024 |+44.5|17 +40.0|8 -31.7|3 +38.6|4 +23.9|9+147.4|5+128.1|6 +18.5|8+102.1|7+94.1|11  +9.6|7  -7.2|3 |  +54.5%   88
 2025 |  +3.5|2+141.6|2       ·       ·+92.1|10+150.4|47+127.6|18       ·       ·       ·       ·       · | +133.9%   79
```

### bk50d_s16_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -33.3|5 -17.1|7  -9.3|3  -4.8|5  -9.3|1 +18.6|2 -60.9|3       ·       · -34.5|1  +2.2|4       · |  -16.7%   31
 2016 |       ·       ·+46.0|28+34.3|46  +3.1|7 -5.0|14+12.5|10 +61.7|8+108.5|4 -16.9|3       · +36.4|6 |  +32.1%  126
 2017 | +10.5|3+124.1|2 +84.0|3       · +41.7|3 +43.6|2 +59.8|4  +3.0|3 +71.6|1 +24.1|2       · +70.3|3 |  +50.9%   26
 2018 | +31.0|5       · +21.2|2 +64.0|2 -48.2|1 -18.7|1       ·+107.2|1       ·       ·       · -41.5|1 |  +24.9%   13
 2019 |       ·  +9.9|8  +3.4|6 +27.8|1  -5.5|1 -20.6|3  -5.5|6 +62.1|3 +80.9|1 +56.0|6 +87.2|3 +54.2|4 |  +26.4%   42
 2020 | +26.5|2+406.6|4       ·       ·+99.9|172+68.1|135+48.6|28+87.1|21+174.8|9+66.4|12+47.3|30+27.5|54 |  +78.2%  467
 2021 |+70.8|39+44.1|21  -2.3|2 +11.9|4       · +99.9|9 -40.2|2 +53.8|1 +18.7|1 -30.0|2  +1.4|2       · |  +55.0%   83
 2022 | +11.6|2 +27.6|3-20.1|16  +0.6|6       ·       ·       ·       ·       ·       ·+19.9|16+17.2|19 |   +7.0%   62
 2023 |+14.9|18+18.9|13 +34.7|7  +6.5|4 +21.2|9+20.8|11+15.0|23 +33.0|1 +68.4|3       · +71.2|9+19.5|22 |  +23.8%  120
 2024 |+48.4|15 +39.8|8 -25.1|5 +38.6|4+23.3|10+126.1|6 +91.5|8 +9.1|14 +88.4|7+98.3|11  +0.7|8  -7.2|3 |  +46.5%   99
 2025 |  +3.5|2+117.4|3       ·       ·+106.3|15+157.1|47+132.1|23       ·       ·       ·       ·       · | +137.5%   90
```

### bk50d_s12_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -33.3|5-23.8|11  -8.3|3  -4.8|5  -7.1|1 +31.3|3 -60.2|3       ·       ·  -9.7|2  +3.6|4       · |  -15.6%   37
 2016 |       ·       ·+44.3|34+34.6|48  +3.1|7 -8.2|17+26.3|13 +50.4|9+114.6|5 -16.9|3  +7.6|1 +43.9|8 |  +32.6%  145
 2017 | +29.8|6 +68.8|3 +63.1|4 +11.6|1 +22.7|4 +43.6|2 +60.0|4  -3.5|5 +71.6|1  +1.5|3       · +70.3|3 |  +37.1%   36
 2018 | +25.5|6       · +21.2|2 +31.7|4 -17.2|3 -22.7|2 -14.0|1 +37.3|2       ·       ·       · -38.0|2 |   +9.5%   22
 2019 |       ·+23.0|12 -46.3|6 +10.7|3  -5.5|1 -17.7|3  -2.6|7 +62.1|3 +86.6|1 +42.2|7 +69.0|4 +28.1|7 |  +18.4%   54
 2020 | +26.5|2+406.6|4       ·       ·+98.9|176+67.8|136+48.9|35+100.6|27+189.1|6+61.6|14+46.1|32+27.6|56 |  +77.4%  488
 2021 |+70.8|39+54.0|26  -2.3|2 +11.2|5 +48.1|3+93.9|14 -40.2|2 +53.8|1 +18.7|1  -9.9|3  +1.4|2       · |  +57.6%   98
 2022 | +13.1|2 +43.3|7 +0.8|22  +6.9|9       ·       ·       ·       ·       ·       ·+15.7|19+18.7|20 |  +13.7%   79
 2023 |+14.1|20+28.1|15 +34.7|7 +70.9|5+66.2|11+20.9|14+16.0|29 +50.5|2 +68.4|3       ·+62.7|16+30.7|22 |  +33.1%  144
 2024 |+61.8|17 +39.5|9  -6.0|6 +28.9|5+20.8|12+109.3|7+83.9|10+14.8|17+107.8|9+92.3|17  -2.9|9  -7.2|3 |  +50.5%  121
 2025 |  +3.5|2 +91.4|6       ·       ·+101.7|18+139.1|54+116.3|30       ·       ·       ·       ·       · | +121.7%  110
```

## Findings & Caveats

- **30-day resting window**: unlike a single next-day-only attempt, the order stays live for 30 calendar days and fills on the *first* day the low touches the limit price. This raises fill rates substantially versus a next-day-only rule, but it also means higher-X% fills are increasingly dominated by trades that took most of the window to retrace that far — those signals have effectively already spent part of their 366d hold going nowhere (or down) before the position even opens, which the raw per-trade return doesn't capture (it's measured from the fill day, not the signal day).

- **Selection effect**: a limit fill at a deep discount means the stock pulled back after triggering the breakout signal — this is not a neutral resampling of the same trade population as the EOD baseline; it systematically selects for breakouts that gave back some of the signal-day gain before continuing (or failing), which can bias mean/median returns in either direction depending on regime.

- **Fill% still drops with X%, just more slowly than a next-day-only rule**: rows with N well under 30 are not statistically reliable, even if the ratios look attractive.

- **Fill/exit price convention**: consistent with qullamaggie-backtest-v4.py, all prices are split/dividend-adjusted close/high/low; entry is exactly the limit price (no slippage beyond the modeled discount), and hold length is measured in calendar days from the fill day, not the original signal day.

- **No execution costs**: no commissions, spread, or partial fills are modeled; a real resting limit order also carries queue-priority and gap risk not captured here (e.g. a gap-down open below the limit price would fill better than modeled).
