# Qullamaggie Limit-Order Fill Sensitivity — 366d Cohorts

Run date: 2026-08-09 18:56:38 Tallinn time

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
| Ranking gate | QullamaggieRanking >= 44 |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min **10** losers (turtlex/backtest/metrics.py) |

## Results

### bk50d_s20_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   91.5%  1541   +41.5%   +57.8%   74.9%    3.454    9.41   -57.40
EOD (legacy)       91.5%  1541   +41.2%   +58.1%   75.0%    3.479    9.50   -57.39
----------------------------------------------------------------------------------
0%                 97.9%  1511   +41.6%   +57.3%   74.7%    3.410    9.23   -57.48
1%                 94.8%  1466   +43.4%   +58.2%   75.0%    3.487    9.49   -57.31
2%                 89.5%  1387   +44.5%   +59.8%   75.5%    3.610    9.88   -57.29
3%                 84.7%  1315   +45.9%   +60.5%   75.7%    3.628    9.98   -57.92
4%                 79.6%  1237   +46.4%   +61.3%   75.7%    3.646   10.01   -58.06
5%                 74.3%  1158   +48.8%   +63.2%   76.2%    3.724   10.25   -58.55
```

### bk50d_s16_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   90.9%  1723   +39.8%   +57.2%   73.4%    3.323    8.89   -58.39
EOD (legacy)       90.9%  1723   +38.9%   +57.7%   73.5%    3.356    9.00   -58.39
----------------------------------------------------------------------------------
0%                 97.8%  1688   +39.0%   +56.1%   73.3%    3.246    8.67   -58.47
1%                 95.0%  1645   +40.5%   +57.5%   74.0%    3.364    9.05   -58.10
2%                 89.6%  1554   +41.9%   +59.2%   74.5%    3.484    9.44   -58.29
3%                 84.7%  1472   +43.3%   +59.6%   74.6%    3.485    9.45   -58.77
4%                 79.5%  1383   +43.9%   +59.5%   74.7%    3.439    9.29   -58.88
5%                 74.4%  1299   +45.4%   +60.4%   74.9%    3.458    9.35   -59.49
```

### bk50d_s12_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   90.8%  1786   +38.6%   +56.8%   73.2%    3.234    8.64   -59.55
EOD (legacy)       90.8%  1786   +38.3%   +57.3%   73.2%    3.268    8.77   -59.69
----------------------------------------------------------------------------------
0%                 97.6%  1747   +38.3%   +55.9%   73.2%    3.154    8.42   -59.86
1%                 95.2%  1707   +39.8%   +57.3%   73.8%    3.266    8.79   -59.57
2%                 89.8%  1615   +41.2%   +58.8%   74.3%    3.372    9.13   -59.84
3%                 84.5%  1519   +42.5%   +58.7%   74.4%    3.350    9.12   -60.62
4%                 79.1%  1426   +43.8%   +59.1%   74.6%    3.332    9.05   -60.67
5%                 73.8%  1340   +44.8%   +59.4%   74.9%    3.302    8.99   -61.31
```

## Monthly Seasonality (EOD baseline)

Each cell is `Mean%|N` for trades entered in that calendar month (entry = signal day), using the EOD baseline (buy at signal-day close, hold 366 calendar days). `·` = no trades that month. The Mean%/N columns on the right are the year's aggregate across all its months.

### bk50d_s20_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -35.6|6 -21.5|7 -20.6|4  +1.2|3 +27.5|2 -31.4|1 -57.3|2       ·       ·       · +11.9|4 +47.2|2 |  -12.7%   31
 2016 |       ·       ·+46.7|33+30.7|50+11.0|10 +0.8|15 +7.9|12+37.9|12 +77.5|9  -1.0|4       ·+25.0|12 |  +30.2%  157
 2017 |  +0.3|4 +54.8|2+102.4|2       · +57.4|3 +47.6|1 +24.8|3 +76.7|5 +50.0|2 +18.9|6+139.2|3 +60.9|4 |  +53.4%   35
 2018 | +17.6|8       · +54.6|3 +11.9|3 +58.3|9  -8.5|3 +41.9|1 +41.3|1 -31.4|1       ·       ·       · |  +30.8%   29
 2019 |       ·+14.7|15+12.9|12 +22.5|5 +65.1|2  +7.4|4-13.3|10 +23.7|3       · +45.3|6 +65.2|4+78.5|15 |  +30.2%   76
 2020 | +17.7|6+333.2|5       ·       ·+96.5|228+68.8|172+58.3|44+82.5|35+178.1|6 +68.7|7+46.1|46+32.1|95 |  +74.2%  644
 2021 |+57.4|69+48.1|23  -2.3|2  +1.2|1       ·+88.8|10 -40.2|2 +28.6|2 +18.7|1  +0.9|3 +36.1|1       · |  +52.5%  114
 2022 | -50.7|1 +24.2|2 +3.5|19 -16.8|7       ·       ·       ·       ·       ·       · +7.7|19+28.3|17 |   +8.8%   65
 2023 |+12.7|17+44.4|22+10.7|10 +26.7|5+48.6|11+39.4|18+29.0|23 -12.9|2 +94.8|3       · +67.0|8+33.7|32 |  +34.6%  151
 2024 |+36.3|26+35.2|15 -11.3|7  +4.2|7+26.2|11 +93.8|8+124.9|8+33.8|13 +98.9|9+92.3|11  +3.6|7  +6.5|8 |  +45.2%  130
 2025 | +10.7|5+107.5|3+1222.2|1       ·+99.1|10+133.8|65+120.3|22+274.5|3       ·       ·       ·       · | +135.4%  109
```

### bk50d_s16_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -37.9|7 -18.2|9  -0.3|4  -7.8|4 +35.7|2 +18.6|2 -60.9|3       ·       · -34.5|1  +4.6|5 +49.3|1 |  -13.1%   38
 2016 |       ·       ·+46.5|41+32.4|58+11.7|11 +1.9|15+55.7|14+39.6|13 +96.6|8 -16.9|3  -3.3|1+23.6|13 |  +35.4%  177
 2017 |  -6.4|5 +33.5|5 +99.6|2       · +43.0|4 +26.1|2 +15.7|4 +76.7|5+101.1|3 +20.2|7+208.9|2 +31.8|5 |  +46.1%   44
 2018 | +17.4|8       · +68.7|3 +63.0|4 +58.1|9  -7.5|5 +41.9|1+107.2|1 -31.4|1       ·       ·       · |  +37.5%   32
 2019 |       ·+15.1|17+13.1|12  +8.3|5 +64.8|3  -6.6|5 +8.4|10 +51.1|5 +80.9|1 +39.3|8 +65.2|4+84.5|14 |  +33.3%   84
 2020 | +16.2|7+293.6|6       ·       ·+98.8|242+66.2|178+60.7|40+85.0|31+149.4|12+72.4|13+41.1|49+31.3|99 |  +74.6%  677
 2021 |+57.4|67+43.9|28  -2.3|2  +7.4|3       ·+77.2|12 -40.2|2 +28.6|2 +18.7|1  -8.5|5 -25.0|3       · |  +47.2%  125
 2022 | +11.6|2 +21.6|4 +0.6|23 -4.8|10       ·       ·       ·       ·       ·       ·+18.6|22+18.0|22 |  +10.6%   83
 2023 |+14.8|26+36.3|27+11.7|11  +9.2|7+34.8|14+35.5|22+12.2|32  +2.4|3 +94.8|3       ·+64.5|11+36.7|37 |  +28.9%  193
 2024 |+57.8|29+26.7|15-15.6|11 +13.9|6+32.7|10 +85.6|9+108.8|11+18.5|20+96.7|10+85.0|15  -4.9|9 +13.7|7 |  +45.7%  152
 2025 | +28.0|7+107.5|3+1222.2|1       ·+111.0|15+159.9|62+137.7|27+274.5|3       ·       ·       ·       · | +151.3%  118
```

### bk50d_s12_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -37.9|7-18.7|12  +0.6|3  -7.8|4 +36.8|2 +10.4|2 -56.4|5       ·       · +13.5|1  +4.2|6 -10.3|3 |  -15.5%   45
 2016 |       ·       ·+47.7|42+33.1|59+26.7|13 +2.8|18+59.1|13+33.1|14+101.2|9 -16.9|3  +2.1|2+23.1|13 |  +36.3%  186
 2017 |  -9.4|6 +42.3|4 +99.6|2       · +43.0|4 +26.1|2 +15.9|4 +67.3|6+101.1|3 +13.9|8+208.9|2 +28.7|5 |  +43.0%   46
 2018 | +14.8|8       · +68.7|3 +63.0|4 +63.9|9  -3.5|5 +41.9|1+107.2|1 -31.4|1       ·       · -34.6|1 |  +36.9%   33
 2019 |       ·+26.3|16 -6.0|11 +20.5|6 +64.8|3  +8.5|4 +8.0|11 +51.1|5 +86.6|1+23.4|10 +65.2|4+58.8|14 |  +28.9%   85
 2020 |  +5.7|8+333.2|5       ·       ·+98.3|247+65.5|172+55.3|45+87.6|34+156.8|8+65.3|17+41.1|49+32.1|98 |  +73.6%  683
 2021 |+58.0|67+44.5|30  -2.3|2  +8.3|3 +52.3|1+64.8|17 -40.2|2 +28.6|2 -22.5|2  -8.5|5 -25.0|3       · |  +46.4%  134
 2022 | +13.1|2 +77.2|5 +6.1|26 +9.9|11       ·       ·       ·       ·       ·       ·+18.6|22+19.2|23 |  +17.2%   89
 2023 |+13.3|27+37.8|25+11.7|11  +9.2|7+64.0|16+37.2|23+12.5|33  +2.4|3 +94.8|3       ·+53.2|13+42.9|36 |  +32.1%  197
 2024 |+57.2|30+27.3|16-21.1|10 +13.9|6+34.3|10+77.9|10+99.5|13+19.7|21+93.5|11+95.4|15 -7.6|10 +13.7|7 |  +46.1%  159
 2025 | +28.0|7 +86.4|6+1222.2|1       ·+104.7|16+155.6|64+142.1|31+239.7|4       ·       ·       ·       · | +146.8%  129
```

## Findings & Caveats

- **30-day resting window**: unlike a single next-day-only attempt, the order stays live for 30 calendar days and fills on the *first* day the low touches the limit price. This raises fill rates substantially versus a next-day-only rule, but it also means higher-X% fills are increasingly dominated by trades that took most of the window to retrace that far — those signals have effectively already spent part of their 366d hold going nowhere (or down) before the position even opens, which the raw per-trade return doesn't capture (it's measured from the fill day, not the signal day).

- **Selection effect**: a limit fill at a deep discount means the stock pulled back after triggering the breakout signal — this is not a neutral resampling of the same trade population as the EOD baseline; it systematically selects for breakouts that gave back some of the signal-day gain before continuing (or failing), which can bias mean/median returns in either direction depending on regime.

- **Fill% still drops with X%, just more slowly than a next-day-only rule**: rows with N well under 30 are not statistically reliable, even if the ratios look attractive.

- **Fill/exit price convention**: consistent with qullamaggie-backtest-v4.py, all prices are split/dividend-adjusted close/high/low; entry is exactly the limit price (no slippage beyond the modeled discount), and hold length is measured in calendar days from the fill day, not the original signal day.

- **No execution costs**: no commissions, spread, or partial fills are modeled; a real resting limit order also carries queue-priority and gap risk not captured here (e.g. a gap-down open below the limit price would fill better than modeled).
