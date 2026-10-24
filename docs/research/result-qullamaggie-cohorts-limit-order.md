# Qullamaggie Limit-Order Fill Sensitivity — 366d Cohorts

Run date: 2026-10-24 18:10:00 Tallinn time

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
next-open (v2.0)   94.6%  1517   +41.2%   +56.7%   75.1%    3.447    9.54   -57.41
EOD (legacy)       94.6%  1517   +41.0%   +57.1%   75.3%    3.474    9.63   -57.20
----------------------------------------------------------------------------------
0%                 97.8%  1485   +41.6%   +56.3%   75.1%    3.406    9.40   -57.43
1%                 94.8%  1440   +43.3%   +57.9%   75.5%    3.526    9.79   -57.26
2%                 89.6%  1364   +44.5%   +59.3%   76.1%    3.649   10.17   -57.09
3%                 84.8%  1294   +45.9%   +60.8%   76.4%    3.727   10.43   -57.67
4%                 79.7%  1214   +46.6%   +61.4%   76.4%    3.709   10.39   -58.40
5%                 74.5%  1136   +48.8%   +63.4%   76.8%    3.789   10.64   -58.95
```

### bk50d_s16_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   94.1%  1702   +39.2%   +56.2%   73.6%    3.321    9.03   -58.26
EOD (legacy)       94.1%  1702   +38.9%   +56.8%   73.7%    3.359    9.14   -58.04
----------------------------------------------------------------------------------
0%                 97.7%  1664   +38.9%   +55.2%   73.6%    3.247    8.83   -58.43
1%                 94.9%  1620   +40.4%   +57.2%   74.4%    3.405    9.34   -58.05
2%                 89.7%  1535   +42.0%   +59.0%   75.2%    3.542    9.78   -58.12
3%                 84.8%  1455   +43.4%   +60.0%   75.3%    3.589    9.92   -58.56
4%                 79.6%  1365   +43.9%   +59.9%   75.5%    3.514    9.70   -59.21
5%                 74.6%  1279   +44.9%   +60.7%   75.6%    3.525    9.73   -59.86
```

### bk50d_s12_v2.0 — 366d

```text
Cohort             Fill%     N     Med%    Mean%    Win%  Sortino      PF  CVaR95%
----------------------------------------------------------------------------------
next-open (v2.0)   94.2%  1772   +37.8%   +55.3%   73.1%    3.154    8.53   -60.18
EOD (legacy)       94.2%  1772   +38.0%   +55.9%   73.1%    3.192    8.67   -60.24
----------------------------------------------------------------------------------
0%                 97.5%  1730   +38.0%   +54.5%   73.1%    3.078    8.34   -60.59
1%                 95.1%  1689   +39.6%   +56.5%   73.8%    3.223    8.79   -60.31
2%                 89.9%  1601   +41.1%   +58.0%   74.6%    3.333    9.16   -60.33
3%                 84.5%  1505   +42.3%   +58.6%   74.8%    3.351    9.25   -61.10
4%                 79.2%  1410   +43.2%   +58.8%   75.0%    3.305    9.12   -61.95
5%                 74.0%  1322   +44.1%   +59.1%   75.3%    3.266    9.03   -62.70
```

## Monthly Seasonality (EOD baseline)

Each cell is `Mean%|N` for trades entered in that calendar month (entry = signal day), using the EOD baseline (buy at signal-day close, hold 366 calendar days). `·` = no trades that month. The Mean%/N columns on the right are the year's aggregate across all its months.

### bk50d_s20_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -35.6|6 -18.5|6 -20.6|4  +1.2|3 +27.5|2 -31.4|1 -57.3|2       ·       ·       · +11.9|4 +47.2|2 |  -11.8%   30
 2016 |       ·       ·+46.9|32+29.6|50+11.0|10 -6.5|17 +7.9|12+43.7|11 +77.5|9  -1.0|4       ·+29.8|11 |  +29.4%  156
 2017 |  +0.3|4 +54.8|2+102.4|2       · +57.4|3 +47.6|1 +24.8|3 +20.8|4 +50.0|2 +18.9|6+200.7|2 +60.9|4 |  +47.0%   33
 2018 | +21.1|7       · +17.8|2 -22.1|2 -25.1|9  -3.4|2 +41.9|1 +41.3|1 -31.4|1       ·       ·       · |   -1.6%   25
 2019 |       ·+11.0|16+13.9|10 -12.2|4 +65.1|2  +7.4|4-13.3|10 +23.7|3       · +45.3|6 +65.2|4+86.7|12 |  +27.3%   71
 2020 | +17.7|6+375.4|4       ·       ·+93.1|219+69.2|168+58.3|45+85.7|35+203.8|5 +77.9|6+45.6|46+32.6|92 |  +73.2%  626
 2021 |+55.5|69+49.9|21  -2.3|2  +1.2|1       ·+88.8|10 -40.2|2 +28.6|2 +18.7|1  +0.9|3 +36.1|1       · |  +51.7%  112
 2022 | -50.7|1 +24.2|2 +1.9|17 -16.8|7       ·       ·       ·       ·       ·       · +4.1|20+27.4|16 |   +6.8%   63
 2023 |+18.8|16+29.0|23 +3.9|10 +26.7|5 +46.1|9+40.2|17+25.3|24 -12.9|2 +94.8|3       · +67.0|8+37.5|31 |  +32.5%  148
 2024 |+40.6|23+51.4|11  -1.7|5  +1.7|4+44.3|10+147.4|5+139.7|7+33.8|13 +68.9|7+92.3|11 +19.5|7  +6.5|8 |  +52.1%  111
 2025 | +44.5|3+107.5|3+1222.2|1       ·+90.8|10+137.8|59+123.8|20+133.5|10+63.7|22+21.9|14       ·       · | +114.3%  142
```

### bk50d_s16_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -37.9|7 -15.5|8  -9.4|5  -7.8|4 +35.7|2 +18.6|2 -60.9|3       ·       · -34.5|1  +4.6|5 +49.3|1 |  -13.3%   38
 2016 |       ·       ·+46.8|40+31.5|58+11.7|11 -5.5|17+55.7|14+45.1|12 +96.6|8 -16.9|3  -3.3|1+27.8|12 |  +34.7%  176
 2017 |  -6.4|5 +33.5|5 +99.6|2       · +43.0|4 +26.1|2 +15.7|4 +20.8|4 +82.5|4 +20.2|7+401.7|1 +31.8|5 |  +40.4%   43
 2018 | +20.9|7       · +17.8|2 +52.7|3 -25.2|9 -10.7|3 +41.9|1+107.2|1 -31.4|1       ·       ·       · |   +7.3%   27
 2019 |       ·+11.8|18+14.1|10 -29.9|4 +64.8|3  -6.6|5  +2.3|9 +51.1|5 +80.9|1 +39.3|8 +65.2|4+95.2|11 |  +30.5%   78
 2020 | +16.2|7+319.5|5       ·       ·+95.4|233+66.5|174+60.1|40+86.7|32+158.5|11+77.3|12+40.7|49+31.3|97 |  +73.3%  660
 2021 |+56.1|68+45.0|26  -2.3|2  +7.4|3       ·+86.5|11 -40.2|2 +28.6|2 +18.7|1  -8.5|5 -25.0|3       · |  +47.4%  123
 2022 | +11.6|2 +21.6|4 -0.1|20 -4.8|10       ·       ·       ·       ·       ·       ·+13.7|22+18.0|22 |   +9.5%   80
 2023 |+16.9|24+23.9|28 +5.6|11  +9.2|7+30.6|12+34.3|20+10.0|33  +2.4|3 +94.8|3       ·+64.5|11+40.0|36 |  +26.7%  188
 2024 |+61.3|27+39.8|11 -11.2|9 +20.4|3 +53.5|9+126.1|6+117.5|10+25.8|18 +68.0|9+85.0|15  +7.4|9 +13.7|7 |  +52.5%  133
 2025 | +78.1|4 +83.4|4+1222.2|1       ·+94.9|14+164.5|57+135.9|24+124.0|13+76.2|26+20.5|13       ·       · | +126.2%  156
```

### bk50d_s12_v2.0 — Monthly Mean% / N (EOD, entry month/year)

```text
 Year |     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec |   Mean%     N
-----------------------------------------------------------------------------------------------------------------------
 2015 | -37.9|7-16.8|11 -11.0|4  -7.8|4 +36.8|2 +10.4|2 -56.4|5       ·       · +13.5|1  +4.2|6 -10.3|3 |  -15.7%   45
 2016 |       ·       ·+47.9|41+29.8|61+26.7|13 -3.5|20+59.1|13+37.6|13+101.2|9 -16.9|3  -9.9|3+27.3|12 |  +34.4%  188
 2017 |  -9.4|6 +42.3|4 +99.6|2       · +43.0|4 +26.1|2 +15.9|4 +20.6|5 +82.5|4 +13.9|8+401.7|1 +28.7|5 |  +37.5%   45
 2018 | +17.9|7       · +17.8|2 +52.7|3 -19.4|9  -9.7|4 +41.9|1+107.2|1 -31.4|1       ·       · -34.6|1 |   +6.5%   29
 2019 |       ·+22.1|17-16.1|10  -7.7|5 +64.8|3  +8.5|4 -9.3|12 +51.1|5 +86.6|1+23.4|10 +65.2|4+62.4|11 |  +22.2%   82
 2020 |  +5.7|8+375.4|4       ·       ·+94.9|238+65.9|168+54.8|45+93.7|33+179.0|7+68.5|16+40.7|49+32.1|96 |  +72.6%  664
 2021 |+55.0|69+45.6|28  -2.3|2  +8.3|3 +52.3|1+73.9|16 -40.2|2 +28.6|2 -22.5|2  -8.5|5 -25.0|3       · |  +46.2%  133
 2022 | +13.1|2 +77.2|5 +6.8|23 +9.9|11       ·       ·       ·       ·       ·       ·+13.7|22+19.2|23 |  +16.5%   86
 2023 |+16.3|26+28.5|25 +5.6|11  +9.2|7+64.6|14+36.3|21+10.4|34  +2.4|3 +94.8|3       ·+53.2|13+46.6|35 |  +30.7%  192
 2024 |+60.4|28+39.6|12 -17.5|8 +20.4|3 +55.2|9+109.3|7+109.4|11+26.7|19+67.3|10+95.4|15 +3.5|10 +13.7|7 |  +52.5%  139
 2025 | +78.1|4 +75.6|7+1222.2|1       ·+89.3|15+159.7|59+134.7|28+118.0|16+74.2|25+16.8|14       ·       · | +121.7%  169
```

## Findings & Caveats

- **30-day resting window**: unlike a single next-day-only attempt, the order stays live for 30 calendar days and fills on the *first* day the low touches the limit price. This raises fill rates substantially versus a next-day-only rule, but it also means higher-X% fills are increasingly dominated by trades that took most of the window to retrace that far — those signals have effectively already spent part of their 366d hold going nowhere (or down) before the position even opens, which the raw per-trade return doesn't capture (it's measured from the fill day, not the signal day).

- **Selection effect**: a limit fill at a deep discount means the stock pulled back after triggering the breakout signal — this is not a neutral resampling of the same trade population as the EOD baseline; it systematically selects for breakouts that gave back some of the signal-day gain before continuing (or failing), which can bias mean/median returns in either direction depending on regime.

- **Fill% still drops with X%, just more slowly than a next-day-only rule**: rows with N well under 30 are not statistically reliable, even if the ratios look attractive.

- **Fill/exit price convention**: consistent with qullamaggie-backtest-v4.py, all prices are split/dividend-adjusted close/high/low; entry is exactly the limit price (no slippage beyond the modeled discount), and hold length is measured in calendar days from the fill day, not the original signal day.

- **No execution costs**: no commissions, spread, or partial fills are modeled; a real resting limit order also carries queue-priority and gap risk not captured here (e.g. a gap-down open below the limit price would fill better than modeled).
