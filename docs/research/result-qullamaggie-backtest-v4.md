# Qullamaggie Backtest v4 — Results

Run date: 2026-06-29

## Configuration

| Parameter | Value |
|---|---|
| Breakout | 50d high |
| SMA thresh sweep | 15%, 20%, 25% |
| Tight range sweep | 10%, 15%, 20% |
| Hold sweep | 184d, 366d (calendar) |
| vol_dry_up | avg_vol_10 < 80% × avg_vol_50 |
| vol_surge | 1.0× < volume/avg_vol_50 < 2.0× |
| roc_12m_cap | 12m ROC < 100% |
| RSI | RSI(14) < 80 |
| ADR | ≥ 2.5% |
| SMA alignment | disabled (commented out) |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | ≥ 500K |
| Min history | ≥ 300 trading days |
| Cooldown | 30 calendar days |
| Eval period | 2021-01-01 – 2026-06-29 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings

```
Period: 2021-01-01 – 2026-06-29  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<80%, roc_12m<100%, 1.0x<vol_surge<2.0x, RSI<80, ADR>=2.5%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K

   #  Entry Signal                      Exit     N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s25_tr15_v1.2_roc100       366d   106   69.8   +57.73   +25.76  10.05    2.163   -48.96    1.6    3/3  ✓
   2  bk50d_s25_tr20_v1.2_roc100       366d   124   67.7   +52.73   +19.66   8.00    1.806   -55.86    1.9    4/4  ✓
   3  bk50d_s25_tr10_v1.2_roc100       366d    59   66.1   +49.16   +19.84   7.78    1.805   -57.43    0.9    1/1   
   4  bk50d_s20_tr10_v1.2_roc100       366d   177   62.7   +41.43   +14.24   6.44    1.646   -48.27    2.7    4/4  ✓
   5  bk50d_s20_tr15_v1.2_roc100       366d   264   65.9   +39.71   +16.30   6.03    1.383   -53.46    4.1    4/4  ✓
   6  bk50d_s20_tr20_v1.2_roc100       366d   292   64.4   +37.35   +14.30   5.23    1.233   -57.05    4.5    4/4  ✓
   7  bk50d_s15_tr10_v1.2_roc100       366d   400   64.2   +32.61   +13.79   4.97    1.134   -54.47    6.2    5/5  ✓
   8  bk50d_s15_tr15_v1.2_roc100       366d   543   65.0   +33.31   +13.68   4.96    1.107   -56.90    8.4    5/5  ✓
   9  bk50d_s25_tr15_v1.2_roc100       184d   106   59.4   +19.09    +8.32   3.31    1.083   -45.39    1.6    3/4  ✓
  10  bk50d_s15_tr20_v1.2_roc100       366d   576   64.4   +33.20   +13.16   4.71    1.066   -59.09    8.9    5/5  ✓
  11  bk50d_s25_tr10_v1.2_roc100       184d    59   61.0   +17.11   +10.58   3.33    1.061   -43.91    0.9    2/2   
  12  bk50d_s25_tr20_v1.2_roc100       184d   124   61.3   +19.62   +11.78   3.38    1.056   -47.97    1.9    4/4  ✓
  13  bk50d_s20_tr10_v1.2_roc100       184d   177   58.8   +14.94    +7.99   3.14    1.006   -43.10    2.7    4/4  ✓
  14  bk50d_s20_tr15_v1.2_roc100       184d   264   58.0   +14.30    +6.82   2.82    0.855   -47.94    4.1    4/4  ✓
  15  bk50d_s20_tr20_v1.2_roc100       184d   292   58.9   +14.12    +7.67   2.77    0.804   -49.83    4.5    4/4  ✓
  16  bk50d_s15_tr15_v1.2_roc100       184d   543   56.9   +11.45    +5.46   2.39    0.665   -48.83    8.4    5/5  ✓
  17  bk50d_s15_tr20_v1.2_roc100       184d   576   57.5   +11.51    +5.99   2.38    0.647   -51.15    8.9    5/5  ✓
  18  bk50d_s15_tr10_v1.2_roc100       184d   400   57.5   +10.27    +5.51   2.31    0.627   -45.48    6.2    5/5  ✓

Valid combinations: 18  |  Consistent: 16
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥5 negative trades, and ≥3 valid years.

- `bk50d_s25_tr15_v1.2_roc100` | `366d` — SR=2.163, Win%=69.8, Med%=+25.76, CVaR%=-48.96, Yrs+=3/3, N=106
- `bk50d_s25_tr20_v1.2_roc100` | `366d` — SR=1.806, Win%=67.7, Med%=+19.66, CVaR%=-55.86, Yrs+=4/4, N=124
- `bk50d_s20_tr10_v1.2_roc100` | `366d` — SR=1.646, Win%=62.7, Med%=+14.24, CVaR%=-48.27, Yrs+=4/4, N=177
- `bk50d_s20_tr15_v1.2_roc100` | `366d` — SR=1.383, Win%=65.9, Med%=+16.30, CVaR%=-53.46, Yrs+=4/4, N=264
- `bk50d_s20_tr20_v1.2_roc100` | `366d` — SR=1.233, Win%=64.4, Med%=+14.30, CVaR%=-57.05, Yrs+=4/4, N=292
- `bk50d_s15_tr10_v1.2_roc100` | `366d` — SR=1.134, Win%=64.2, Med%=+13.79, CVaR%=-54.47, Yrs+=5/5, N=400
- `bk50d_s15_tr15_v1.2_roc100` | `366d` — SR=1.107, Win%=65.0, Med%=+13.68, CVaR%=-56.90, Yrs+=5/5, N=543
- `bk50d_s25_tr15_v1.2_roc100` | `184d` — SR=1.083, Win%=59.4, Med%=+8.32, CVaR%=-45.39, Yrs+=3/4, N=106
- `bk50d_s15_tr20_v1.2_roc100` | `366d` — SR=1.066, Win%=64.4, Med%=+13.16, CVaR%=-59.09, Yrs+=5/5, N=576
- `bk50d_s25_tr20_v1.2_roc100` | `184d` — SR=1.056, Win%=61.3, Med%=+11.78, CVaR%=-47.97, Yrs+=4/4, N=124
- `bk50d_s20_tr10_v1.2_roc100` | `184d` — SR=1.006, Win%=58.8, Med%=+7.99, CVaR%=-43.10, Yrs+=4/4, N=177
- `bk50d_s20_tr15_v1.2_roc100` | `184d` — SR=0.855, Win%=58.0, Med%=+6.82, CVaR%=-47.94, Yrs+=4/4, N=264
- `bk50d_s20_tr20_v1.2_roc100` | `184d` — SR=0.804, Win%=58.9, Med%=+7.67, CVaR%=-49.83, Yrs+=4/4, N=292
- `bk50d_s15_tr15_v1.2_roc100` | `184d` — SR=0.665, Win%=56.9, Med%=+5.46, CVaR%=-48.83, Yrs+=5/5, N=543
- `bk50d_s15_tr20_v1.2_roc100` | `184d` — SR=0.647, Win%=57.5, Med%=+5.99, CVaR%=-51.15, Yrs+=5/5, N=576
- `bk50d_s15_tr10_v1.2_roc100` | `184d` — SR=0.627, Win%=57.5, Med%=+5.51, CVaR%=-45.48, Yrs+=5/5, N=400
