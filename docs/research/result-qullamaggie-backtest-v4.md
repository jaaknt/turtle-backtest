# Qullamaggie Backtest v4 — Results

Run date: 2026-07-05

## Configuration

| Parameter | Value |
|---|---|
| Breakout | 50d high |
| SMA thresh sweep | 12%, 15%, 17%, 20% |
| Tight range | 20% (fixed) |
| Hold sweep | 184d, 366d (calendar) |
| vol_dry_up | avg_vol_10 < 80% × avg_vol_50 |
| vol_surge | volume/avg_vol_50 < 2.0× (no lower bound) |
| roc_12m_cap | 12m ROC < 100% |
| RSI | RSI(14) < 70 |
| ADR | mean((high-low)/low, last 20d, shift-1) ≥ 3.0% |
| ADR change | ADR%(10d) / ADR%(50d) < 90% |
| SMA alignment | disabled (commented out) |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | ≥ 500K |
| Min history | ≥ 300 trading days |
| Cooldown | 30 calendar days |
| Eval period | 2021-01-01 – 2026-07-05 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings

```
Period: 2021-01-01 – 2026-07-05  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<80%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K

   #  Entry Signal                      Exit     N   Win%    Mean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_tr20_v1.2_roc100       366d   240   66.2   +51.12   +18.65   +67.63   6.59    1.552    40.14   -60.61    3.6    4/4  ✓
   2  bk50d_s15_tr20_v1.2_roc100       366d   449   64.6   +40.42   +16.85   +55.08   5.41    1.259    38.31   -61.50    6.8    5/5  ✓
   3  bk50d_s17_tr20_v1.2_roc100       366d   346   63.3   +40.74   +15.42   +59.03   5.18    1.249    39.55   -62.04    5.2    5/5  ✓
   4  bk50d_s20_tr20_v1.2_roc100       184d   240   63.7   +21.14   +13.04   +41.00   3.83    1.150    30.42   -48.94    3.6    4/4  ✓
   5  bk50d_s12_tr20_v1.2_roc100       366d   616   63.6   +35.82   +13.98   +50.88   4.88    1.141    37.63   -59.62    9.3    5/5  ✓
   6  bk50d_s17_tr20_v1.2_roc100       184d   346   60.4   +15.60    +9.06   +32.46   2.90    0.853    30.25   -50.01    5.2    4/4  ✓
   7  bk50d_s15_tr20_v1.2_roc100       184d   449   59.9   +14.66    +7.39   +28.97   2.77    0.811    29.40   -48.94    6.8    5/5  ✓
   8  bk50d_s12_tr20_v1.2_roc100       184d   616   58.4   +12.41    +6.20   +26.50   2.46    0.700    29.02   -48.15    9.3    5/5  ✓

Valid combinations: 8  |  Consistent: 8
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_tr20_v1.2_roc100` | `366d` — SR=1.552, Win%=66.2, Med%=+18.65, Q75%=+67.63, MaxDD%=40.14, CVaR%=-60.61, Yrs+=4/4, N=240
- `bk50d_s15_tr20_v1.2_roc100` | `366d` — SR=1.259, Win%=64.6, Med%=+16.85, Q75%=+55.08, MaxDD%=38.31, CVaR%=-61.50, Yrs+=5/5, N=449
- `bk50d_s17_tr20_v1.2_roc100` | `366d` — SR=1.249, Win%=63.3, Med%=+15.42, Q75%=+59.03, MaxDD%=39.55, CVaR%=-62.04, Yrs+=5/5, N=346
- `bk50d_s20_tr20_v1.2_roc100` | `184d` — SR=1.150, Win%=63.7, Med%=+13.04, Q75%=+41.00, MaxDD%=30.42, CVaR%=-48.94, Yrs+=4/4, N=240
- `bk50d_s12_tr20_v1.2_roc100` | `366d` — SR=1.141, Win%=63.6, Med%=+13.98, Q75%=+50.88, MaxDD%=37.63, CVaR%=-59.62, Yrs+=5/5, N=616
- `bk50d_s17_tr20_v1.2_roc100` | `184d` — SR=0.853, Win%=60.4, Med%=+9.06, Q75%=+32.46, MaxDD%=30.25, CVaR%=-50.01, Yrs+=4/4, N=346
- `bk50d_s15_tr20_v1.2_roc100` | `184d` — SR=0.811, Win%=59.9, Med%=+7.39, Q75%=+28.97, MaxDD%=29.40, CVaR%=-48.94, Yrs+=5/5, N=449
- `bk50d_s12_tr20_v1.2_roc100` | `184d` — SR=0.700, Win%=58.4, Med%=+6.20, Q75%=+26.50, MaxDD%=29.02, CVaR%=-48.15, Yrs+=5/5, N=616
