# Qullamaggie Backtest v4 — Results

Run date: 2026-06-30

## Configuration

| Parameter | Value |
|---|---|
| Breakout | 50d high |
| SMA thresh sweep | 15%, 20%, 25% |
| Tight range sweep | 10%, 15%, 20% |
| Hold sweep | 184d, 366d (calendar) |
| vol_dry_up | avg_vol_10 < 80% × avg_vol_50 |
| vol_surge | volume/avg_vol_50 < 2.0× (no lower bound) |
| roc_12m_cap | 12m ROC < 100% |
| RSI | RSI(14) < 80 |
| ADR | ≥ 2.5% |
| SMA alignment | disabled (commented out) |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | ≥ 500K |
| Min history | ≥ 300 trading days |
| Cooldown | 30 calendar days |
| Eval period | 2021-01-01 – 2026-06-30 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings

```
Period: 2021-01-01 – 2026-06-30  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<80%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<80, ADR>=2.5%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K

   #  Entry Signal                      Exit     N   Win%    Mean%     Med%     PF  Sortino    CVaR%   F/mo   Yrs+  C
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_tr10_v1.2_roc100       366d   320   62.5   +40.04   +14.76   5.77    1.411   -53.80    4.9    5/5  ✓
   2  bk50d_s25_tr10_v1.2_roc100       366d   127   59.1   +40.52   +10.32   5.15    1.312   -62.40    2.0    5/5  ✓
   3  bk50d_s25_tr15_v1.2_roc100       366d   195   61.5   +43.21   +15.24   5.23    1.280   -67.10    3.0    5/5  ✓
   4  bk50d_s25_tr20_v1.2_roc100       366d   221   61.1   +42.06   +11.30   5.02    1.249   -64.46    3.4    5/5  ✓
   5  bk50d_s15_tr10_v1.2_roc100       366d   766   62.5   +31.83   +12.73   4.64    1.083   -56.20   11.8    5/5  ✓
   6  bk50d_s20_tr20_v1.2_roc100       366d   491   61.7   +36.04   +11.47   4.48    1.066   -65.57    7.6    5/5  ✓
   7  bk50d_s20_tr15_v1.2_roc100       366d   447   62.4   +35.14   +13.98   4.53    1.055   -64.67    6.9    5/5  ✓
   8  bk50d_s15_tr15_v1.2_roc100       366d   962   62.4   +30.30   +12.02   4.23    0.970   -60.11   14.8    5/5  ✓
   9  bk50d_s15_tr20_v1.2_roc100       366d  1008   61.9   +30.18   +11.20   4.13    0.953   -61.00   15.5    5/5  ✓
  10  bk50d_s20_tr10_v1.2_roc100       184d   320   59.7   +14.82    +8.07   2.99    0.907   -44.47    4.9    5/5  ✓
  11  bk50d_s25_tr15_v1.2_roc100       184d   195   56.9   +16.65    +6.09   2.79    0.884   -51.10    3.0    4/4  ✓
  12  bk50d_s25_tr20_v1.2_roc100       184d   221   57.0   +15.86    +6.09   2.65    0.813   -53.49    3.4    4/4  ✓
  13  bk50d_s25_tr10_v1.2_roc100       184d   127   56.7   +14.32    +6.13   2.65    0.808   -48.99    2.0    4/4  ✓
  14  bk50d_s20_tr15_v1.2_roc100       184d   447   56.8   +13.21    +7.55   2.52    0.723   -52.07    6.9    5/5  ✓
  15  bk50d_s20_tr20_v1.2_roc100       184d   491   57.2   +13.18    +7.76   2.48    0.702   -53.65    7.6    5/5  ✓
  16  bk50d_s15_tr10_v1.2_roc100       184d   766   57.2   +10.27    +4.92   2.28    0.618   -46.13   11.8    5/5  ✓
  17  bk50d_s15_tr15_v1.2_roc100       184d   962   55.5   +10.17    +4.44   2.17    0.584   -48.86   14.8    5/5  ✓
  18  bk50d_s15_tr20_v1.2_roc100       184d  1008   55.9   +10.18    +4.87   2.15    0.570   -50.57   15.5    5/5  ✓

Valid combinations: 18  |  Consistent: 18
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥5 negative trades, and ≥3 valid years.

- `bk50d_s20_tr10_v1.2_roc100` | `366d` — SR=1.411, Win%=62.5, Med%=+14.76, CVaR%=-53.80, Yrs+=5/5, N=320
- `bk50d_s25_tr10_v1.2_roc100` | `366d` — SR=1.312, Win%=59.1, Med%=+10.32, CVaR%=-62.40, Yrs+=5/5, N=127
- `bk50d_s25_tr15_v1.2_roc100` | `366d` — SR=1.280, Win%=61.5, Med%=+15.24, CVaR%=-67.10, Yrs+=5/5, N=195
- `bk50d_s25_tr20_v1.2_roc100` | `366d` — SR=1.249, Win%=61.1, Med%=+11.30, CVaR%=-64.46, Yrs+=5/5, N=221
- `bk50d_s15_tr10_v1.2_roc100` | `366d` — SR=1.083, Win%=62.5, Med%=+12.73, CVaR%=-56.20, Yrs+=5/5, N=766
- `bk50d_s20_tr20_v1.2_roc100` | `366d` — SR=1.066, Win%=61.7, Med%=+11.47, CVaR%=-65.57, Yrs+=5/5, N=491
- `bk50d_s20_tr15_v1.2_roc100` | `366d` — SR=1.055, Win%=62.4, Med%=+13.98, CVaR%=-64.67, Yrs+=5/5, N=447
- `bk50d_s15_tr15_v1.2_roc100` | `366d` — SR=0.970, Win%=62.4, Med%=+12.02, CVaR%=-60.11, Yrs+=5/5, N=962
- `bk50d_s15_tr20_v1.2_roc100` | `366d` — SR=0.953, Win%=61.9, Med%=+11.20, CVaR%=-61.00, Yrs+=5/5, N=1008
- `bk50d_s20_tr10_v1.2_roc100` | `184d` — SR=0.907, Win%=59.7, Med%=+8.07, CVaR%=-44.47, Yrs+=5/5, N=320
- `bk50d_s25_tr15_v1.2_roc100` | `184d` — SR=0.884, Win%=56.9, Med%=+6.09, CVaR%=-51.10, Yrs+=4/4, N=195
- `bk50d_s25_tr20_v1.2_roc100` | `184d` — SR=0.813, Win%=57.0, Med%=+6.09, CVaR%=-53.49, Yrs+=4/4, N=221
- `bk50d_s25_tr10_v1.2_roc100` | `184d` — SR=0.808, Win%=56.7, Med%=+6.13, CVaR%=-48.99, Yrs+=4/4, N=127
- `bk50d_s20_tr15_v1.2_roc100` | `184d` — SR=0.723, Win%=56.8, Med%=+7.55, CVaR%=-52.07, Yrs+=5/5, N=447
- `bk50d_s20_tr20_v1.2_roc100` | `184d` — SR=0.702, Win%=57.2, Med%=+7.76, CVaR%=-53.65, Yrs+=5/5, N=491
- `bk50d_s15_tr10_v1.2_roc100` | `184d` — SR=0.618, Win%=57.2, Med%=+4.92, CVaR%=-46.13, Yrs+=5/5, N=766
- `bk50d_s15_tr15_v1.2_roc100` | `184d` — SR=0.584, Win%=55.5, Med%=+4.44, CVaR%=-48.86, Yrs+=5/5, N=962
- `bk50d_s15_tr20_v1.2_roc100` | `184d` — SR=0.570, Win%=55.9, Med%=+4.87, CVaR%=-50.57, Yrs+=5/5, N=1008
