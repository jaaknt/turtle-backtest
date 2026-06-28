# Qullamaggie Backtest v4 — Results

Run date: 2026-06-28

## Configuration

| Parameter | Value |
|---|---|
| Breakout | 50d high |
| SMA thresh sweep | 15%, 20%, 25% |
| Tight range sweep | 10%, 15%, 20% |
| Hold sweep | 62d, 184d, 366d (calendar) |
| vol_dry_up | avg_vol_10 < 75% × avg_vol_50 |
| vol_surge | 1.2× < volume/avg_vol_50 < 2.0× |
| roc_12m_cap | 12m ROC < 100% |
| RSI | RSI(14) < 72 |
| ADR | ≥ 3% |
| SMA alignment | SMA10 > SMA20 > SMA50 |
| Market regime | SPY close > 200d SMA |
| Eval period | 2021-01-01 – 2026-06-28 |
| Universe | US common stocks, market_cap ≥ 2B, excl. Comm/RE |

## Rankings

```
Period: 2021-01-01 – 2026-06-28  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<80%, roc_12m<100%, 1.0x<vol_surge<2.0x, RSI<72, ADR>=2.5%, SPY>200d SMA, close>=$10, avg_vol>=500K

   #  Entry Signal                      Exit     N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s25_tr15_v1.2_roc100       366d    73   68.5   +53.02   +22.87   7.71    1.644   -65.12    1.1    2/2   
   2  bk50d_s25_tr20_v1.2_roc100       366d    81   66.7   +48.38   +15.57   6.70    1.505   -62.10    1.2    3/3  ✓
   3  bk50d_s20_tr10_v1.2_roc100       366d   132   67.4   +42.63   +18.93   6.62    1.455   -54.99    2.0    3/3  ✓
   4  bk50d_s20_tr15_v1.2_roc100       366d   191   67.5   +38.96   +19.48   5.81    1.247   -58.76    2.9    4/4  ✓
   5  bk50d_s20_tr20_v1.2_roc100       366d   204   66.7   +37.62   +17.83   5.42    1.197   -58.19    3.1    4/4  ✓
   6  bk50d_s15_tr10_v1.2_roc100       366d   310   66.1   +33.92   +17.50   5.03    1.074   -61.44    4.8    5/5  ✓
   7  bk50d_s20_tr10_v1.2_roc100       184d   132   60.6   +15.51    +9.95   3.39    1.027   -45.75    2.0    3/4  ✓
   8  bk50d_s15_tr15_v1.2_roc100       366d   402   65.7   +32.26   +14.85   4.70    0.998   -62.59    6.2    5/5  ✓
   9  bk50d_s15_tr20_v1.2_roc100       366d   418   64.8   +31.44   +13.75   4.46    0.968   -63.24    6.4    5/5  ✓
  10  bk50d_s25_tr10_v1.2_roc100       366d    42   69.0   +34.86   +21.17   4.99    0.960   -71.82    0.6    1/1   
  11  bk50d_s25_tr15_v1.2_roc100       184d    73   58.9   +16.27    +5.94   3.02    0.947   -48.09    1.1    3/3  ✓
  12  bk50d_s25_tr20_v1.2_roc100       184d    81   58.0   +15.36   +10.58   2.86    0.893   -47.37    1.2    2/3   
  13  bk50d_s20_tr15_v1.2_roc100       184d   191   60.7   +13.77    +8.29   2.96    0.821   -50.32    2.9    3/4  ✓
  14  bk50d_s25_tr10_v1.2_roc100       184d    42   61.9   +12.71   +11.57   2.82    0.790   -45.43    0.6    1/1   
  15  bk50d_s20_tr20_v1.2_roc100       184d   204   61.3   +13.33    +8.89   2.88    0.782   -49.31    3.1    3/4  ✓
  16  bk50d_s15_tr10_v1.2_roc100       184d   310   58.4   +10.69    +6.62   2.41    0.637   -48.99    4.8    4/5  ✓
  17  bk50d_s15_tr15_v1.2_roc100       184d   402   57.5    +9.63    +5.91   2.20    0.548   -51.70    6.2    4/5  ✓
  18  bk50d_s15_tr20_v1.2_roc100       184d   418   57.7    +9.27    +6.03   2.13    0.513   -53.54    6.4    4/5  ✓

Valid combinations: 18  |  Consistent: 14
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥5 negative trades, and ≥3 valid years.

- `bk50d_s25_tr20_v1.2_roc100` | `366d` — SR=1.505, Win%=66.7, Med%=+15.57, CVaR%=-62.10, Yrs+=3/3, N=81
- `bk50d_s20_tr10_v1.2_roc100` | `366d` — SR=1.455, Win%=67.4, Med%=+18.93, CVaR%=-54.99, Yrs+=3/3, N=132
- `bk50d_s20_tr15_v1.2_roc100` | `366d` — SR=1.247, Win%=67.5, Med%=+19.48, CVaR%=-58.76, Yrs+=4/4, N=191
- `bk50d_s20_tr20_v1.2_roc100` | `366d` — SR=1.197, Win%=66.7, Med%=+17.83, CVaR%=-58.19, Yrs+=4/4, N=204
- `bk50d_s15_tr10_v1.2_roc100` | `366d` — SR=1.074, Win%=66.1, Med%=+17.50, CVaR%=-61.44, Yrs+=5/5, N=310
- `bk50d_s20_tr10_v1.2_roc100` | `184d` — SR=1.027, Win%=60.6, Med%=+9.95, CVaR%=-45.75, Yrs+=3/4, N=132
- `bk50d_s15_tr15_v1.2_roc100` | `366d` — SR=0.998, Win%=65.7, Med%=+14.85, CVaR%=-62.59, Yrs+=5/5, N=402
- `bk50d_s15_tr20_v1.2_roc100` | `366d` — SR=0.968, Win%=64.8, Med%=+13.75, CVaR%=-63.24, Yrs+=5/5, N=418
- `bk50d_s25_tr15_v1.2_roc100` | `184d` — SR=0.947, Win%=58.9, Med%=+5.94, CVaR%=-48.09, Yrs+=3/3, N=73
- `bk50d_s20_tr15_v1.2_roc100` | `184d` — SR=0.821, Win%=60.7, Med%=+8.29, CVaR%=-50.32, Yrs+=3/4, N=191
- `bk50d_s20_tr20_v1.2_roc100` | `184d` — SR=0.782, Win%=61.3, Med%=+8.89, CVaR%=-49.31, Yrs+=3/4, N=204
- `bk50d_s15_tr10_v1.2_roc100` | `184d` — SR=0.637, Win%=58.4, Med%=+6.62, CVaR%=-48.99, Yrs+=4/5, N=310
- `bk50d_s15_tr15_v1.2_roc100` | `184d` — SR=0.548, Win%=57.5, Med%=+5.91, CVaR%=-51.70, Yrs+=4/5, N=402
- `bk50d_s15_tr20_v1.2_roc100` | `184d` — SR=0.513, Win%=57.7, Med%=+6.03, CVaR%=-53.54, Yrs+=4/5, N=418
