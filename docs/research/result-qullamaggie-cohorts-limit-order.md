# Qullamaggie Limit-Order Fill Sensitivity — 366d Cohorts

Run date: 2026-08-02 23:49:05 Tallinn time

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
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Sortino | mean / RMS(min(r,0)) over all N x sqrt(365/hold), min **10** losers (turtlex/backtest/metrics.py) |

## Results

### bk50d_s20_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   90.9%  1381   +44.3%   +60.0%   75.7%    3.635    9.99   -57.09
EOD (legacy)       90.9%  1381   +44.5%   +60.4%   75.8%    3.657   10.04   -56.97
----------------------------------------------------------------------------------
0%                 97.9%  1354   +43.9%   +59.5%   75.6%    3.570    9.76   -57.48
1%                 95.3%  1319   +45.5%   +60.9%   75.7%    3.687   10.12   -57.31
2%                 91.1%  1264   +46.3%   +62.0%   76.2%    3.780   10.41   -57.06
3%                 86.3%  1198   +47.7%   +63.2%   76.5%    3.858   10.73   -57.60
4%                 82.1%  1140   +48.9%   +64.1%   77.0%    3.887   10.91   -57.89
5%                 76.7%  1069   +50.8%   +65.8%   77.5%    3.934   11.05   -58.72
```

### bk50d_s16_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   90.8%  1548   +41.4%   +58.7%   74.0%    3.387    9.10   -58.90
EOD (legacy)       90.8%  1548   +41.1%   +59.1%   73.9%    3.419    9.18   -58.67
----------------------------------------------------------------------------------
0%                 97.8%  1517   +41.0%   +57.7%   73.9%    3.319    8.91   -59.01
1%                 95.2%  1480   +43.0%   +59.5%   74.3%    3.460    9.32   -58.46
2%                 90.7%  1415   +43.4%   +60.9%   74.8%    3.560    9.63   -58.63
3%                 86.0%  1341   +44.7%   +61.9%   74.9%    3.615    9.82   -58.83
4%                 81.8%  1272   +45.8%   +61.5%   75.2%    3.547    9.67   -59.55
5%                 76.2%  1190   +47.2%   +62.6%   75.5%    3.543    9.65   -60.52
```

### bk50d_s12_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   90.2%  1786   +39.2%   +56.6%   72.7%    3.154    8.35   -60.08
EOD (legacy)       90.2%  1786   +38.6%   +57.0%   72.7%    3.187    8.46   -60.00
----------------------------------------------------------------------------------
0%                 97.7%  1747   +39.1%   +55.9%   72.6%    3.087    8.16   -60.43
1%                 95.1%  1705   +40.5%   +57.4%   73.0%    3.201    8.47   -60.10
2%                 90.7%  1628   +41.2%   +58.4%   73.3%    3.267    8.67   -60.27
3%                 85.4%  1531   +42.6%   +58.8%   73.4%    3.293    8.81   -60.80
4%                 80.9%  1452   +43.8%   +59.0%   73.9%    3.266    8.79   -61.40
5%                 75.3%  1358   +44.7%   +59.2%   74.2%    3.205    8.60   -62.55
```

## Monthly Seasonality (EOD baseline)

Each cell is `Mean%|N` for trades entered in that calendar month (entry = signal day), using the EOD baseline (buy at signal-day close, hold 366 calendar days). `·` = no trades that month. The Mean%/N columns on the right are the year's aggregate across all its months.

### bk50d_s20_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -35.6|6 -27.7|6 -26.1|3  +1.2|3 +27.5|2 -31.4|1 -57.3|2       ·       ·       · +31.9|3 +49.3|1 |  -14.9%   27
 2016 |       ·       ·+44.5|30+30.5|47  +3.3|8 +0.8|15 +7.9|12 +49.0|9 +86.1|5  -1.0|4       · +31.4|7 |  +29.1%  137
 2017 |  +0.3|4+134.2|1+102.4|2       · +57.4|3 +43.6|2 +24.7|4 +77.4|4 +71.6|1  +7.4|3+401.7|1 +75.5|3 |  +61.8%   28
 2018 | +17.4|7       · +21.2|2 -74.2|1 -32.0|2  +5.5|2 +41.9|1 +41.3|1 -31.4|1       ·       ·       · |   +5.3%   17
 2019 |       · +6.6|12 +24.7|9 +51.5|3 +65.1|2 +13.2|3  -9.2|8 +23.7|3       · +80.9|4 +87.2|3+108.4|12 |  +42.5%   59
 2020 | +17.7|6+294.4|6       ·       ·+92.3|231+69.0|176+58.4|43+80.4|29+206.5|5 +69.7|8+50.4|38+34.0|76 |  +74.9%  618
 2021 |+59.5|55+49.5|23  -2.3|2  +1.2|1       ·+114.9|7 -46.1|3 +53.8|1 +18.7|1  +0.9|3 +36.1|1       · |  +53.4%   97
 2022 | -50.7|1 +24.2|2 +3.5|19 -16.8|7       ·       ·       ·       ·       ·       ·+22.1|17+28.3|17 |  +12.7%   63
 2023 |+11.9|16+32.8|18+33.5|11 +26.7|5 +39.8|9+42.2|15+44.4|20 -17.2|1 +68.4|3       · +79.5|5+36.6|27 |  +36.4%  130
 2024 |+40.7|24+32.3|13 -27.6|6 +14.0|6 +23.9|9+100.4|7+139.7|7+28.1|11+113.5|9+94.1|11  +6.5|9 +16.3|4 |  +49.1%  116
 2025 |  -9.8|4+141.6|2+1222.2|1       ·+92.1|10+151.6|51+125.4|21       ·       ·       ·       ·       · | +143.3%   89
```

### bk50d_s16_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -37.9|7 -20.7|9  -0.3|4  -3.8|6 +35.7|2 +18.6|2 -60.9|3       ·       · -34.5|1  +4.6|5 +31.3|2 |  -12.2%   41
 2016 |       ·       ·+45.9|35+34.2|51  +5.0|9 -0.9|14+55.7|14+45.6|11 +99.1|5 -16.9|3       · +24.9|9 |  +35.3%  151
 2017 |  +0.3|4 +65.5|3 +84.0|3       · +52.4|5 +43.6|2 +36.3|5 +77.4|4+137.4|2  +7.4|3+401.7|1 +35.5|4 |  +59.2%   36
 2018 | +23.5|6       · +21.2|2 +64.0|2 -32.8|2  +5.5|2 +41.9|1+107.2|1 -31.4|1       ·       · -41.5|1 |  +18.5%   18
 2019 |       · +5.9|12+12.7|11 +33.3|4 +65.1|2  -5.8|4  +8.8|8 +41.1|4 +80.9|1 +50.6|7 +87.2|3+117.1|11 |  +39.9%   67
 2020 | +17.7|6+294.4|6       ·       ·+94.7|245+65.8|175+59.1|40+80.5|30+170.5|10+67.2|13+44.9|40+33.9|82 |  +75.0%  647
 2021 |+59.5|54+42.5|29  -2.3|2 +11.9|4       · +99.9|9 -46.1|3 +53.8|1 +18.7|1  -8.5|5 -25.0|3       · |  +46.9%  111
 2022 | +11.6|2 +21.6|4 +1.3|20 -6.3|11       ·       ·       ·       ·       ·       ·+31.3|19+20.3|21 |  +14.1%   77
 2023 |+10.7|22+27.9|20+27.5|13  +9.2|7+26.5|11+35.3|19+26.9|28  +7.9|2 +68.4|3       ·+63.3|11+39.0|31 |  +30.3%  167
 2024 |+53.1|24+22.6|13-27.4|10 +27.6|5+24.5|11 +90.3|8+104.5|9+13.3|18 +91.8|8+104.6|12 -0.2|10 +16.3|4 |  +42.9%  132
 2025 | -28.4|3+117.4|3+1222.2|1       ·+106.3|15+173.5|54+144.1|25       ·       ·       ·       ·       · | +159.0%  101
```

### bk50d_s12_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -37.9|7-23.2|14  +0.5|4  -8.0|7 +36.8|2 +31.3|3 -56.4|5       ·       ·  -9.7|2  +5.7|5  +4.5|5 |  -13.5%   54
 2016 |       ·       ·+44.5|41+33.5|58+23.9|11 +1.1|19+56.7|18+31.2|14 +95.0|7 -16.9|3  +7.6|1+32.5|11 |  +35.5%  183
 2017 | +21.2|7 +38.7|4 +63.1|4 +11.6|1 +37.9|6 +43.6|2 +36.5|5 +47.2|6+137.4|2 -10.5|6+401.7|1 +31.7|4 |  +43.5%   48
 2018 | +15.5|8       · +21.2|2 +31.7|4 -17.2|4  -4.7|5 +14.0|2 +37.3|2 -31.4|1 -56.4|1       · -38.0|2 |   +4.5%   31
 2019 |       ·+16.0|17-14.4|11 +21.9|6 +65.1|2  -3.6|4 +8.4|10 +41.1|4 +86.6|1 +35.1|9 +69.0|4+71.7|13 |  +27.4%   81
 2020 |  +5.5|7+294.4|6       ·       ·+93.8|252+65.3|178+57.1|50+91.3|36+180.9|7+61.3|17+44.2|42+34.1|85 |  +73.9%  680
 2021 |+59.5|56+50.4|34  -1.3|3 +11.2|5 +48.1|3+83.1|15 -46.1|3 +53.8|1 -22.5|2  -2.0|6 -25.0|3       · |  +47.9%  131
 2022 | +13.1|2 +38.8|8+24.0|27 +3.0|16       ·       ·       ·       ·       ·       ·+26.1|22+19.4|23 |  +21.0%   98
 2023 |+11.2|25+32.1|23+28.6|14 +42.2|9+63.8|13+35.2|21+23.8|36 +28.0|3 +68.4|3       ·+58.8|18+50.9|32 |  +36.5%  197
 2024 |+61.5|26+23.6|14-16.8|11  +9.8|8+35.7|16 +81.2|9+93.1|12+17.4|21+108.6|10+96.8|18 -3.1|11 +16.3|4 |  +46.7%  160
 2025 | -28.4|3 +91.4|6+1222.2|1       ·+96.9|19+165.1|62+140.5|32       ·       ·       ·       ·       · | +148.4%  123
```

## Findings & Caveats

- **30-day resting window**: unlike a single next-day-only attempt, the order stays live for 30 calendar days and fills on the *first* day the low touches the limit price. This raises fill rates substantially versus a next-day-only rule, but it also means higher-X% fills are increasingly dominated by trades that took most of the window to retrace that far — those signals have effectively already spent part of their 366d hold going nowhere (or down) before the position even opens, which the raw per-trade return doesn't capture (it's measured from the fill day, not the signal day).

- **Selection effect**: a limit fill at a deep discount means the stock pulled back after triggering the breakout signal — this is not a neutral resampling of the same trade population as the EOD baseline; it systematically selects for breakouts that gave back some of the signal-day gain before continuing (or failing), which can bias mean/median returns in either direction depending on regime.

- **Fill% still drops with X%, just more slowly than a next-day-only rule**: rows with N well under 30 are not statistically reliable, even if the ratios look attractive.

- **Fill/exit price convention**: consistent with qullamaggie-backtest-v4.py, all prices are split/dividend-adjusted close/high/low; entry is exactly the limit price (no slippage beyond the modeled discount), and hold length is measured in calendar days from the fill day, not the original signal day.

- **No execution costs**: no commissions, spread, or partial fills are modeled; a real resting limit order also carries queue-priority and gap risk not captured here (e.g. a gap-down open below the limit price would fill better than modeled).
