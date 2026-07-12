# bk50d_s12_tr20_v1.2_roc100 vs bk50d_s20_tr20_v1.2_roc100 — Signal Report

Run date: 2026-07-09

Period: 2026-06-01 – 2026-07-09

Entry $/Curr Price/Change % use raw (unadjusted) close — the real tradeable price. %abv SMA50/ADR%/ADR_CHG/RSI14/TR%/ROC252% are computed on the entry date, using the same split/dividend-adjusted series as scripts/qullamaggie-backtest-v4.py. Last date is the latest date with data available for that symbol in turtle.daily_bars.

```
Date       │ Symbol │  Entry $ │ Curr Price │  Change % │ %abv SMA50 │   ADR% │ ADR_CHG │  RSI14 │    TR% │  ROC252% │ In s20? │   Last date
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
2026-06-01 │ DUOL.US│   117.97 │     127.57 │     +8.1% │     +14.7% │   5.7% │    0.90 │   56.0 │   7.7% │   -77.0% │         │  2026-07-08
2026-06-01 │ FA.US  │    17.07 │      19.70 │    +15.4% │     +30.8% │   5.4% │    0.83 │   50.5 │   7.4% │    +0.2% │       ✓ │  2026-07-08
2026-06-01 │ LC.US  │    18.39 │       0.17 │    -99.1% │     +15.7% │   3.7% │    0.89 │   60.7 │  16.1% │   +81.5% │         │  2026-07-01
2026-06-08 │ PBI.US │    16.94 │      17.31 │     +2.2% │     +18.9% │   3.4% │    0.89 │   62.4 │  10.3% │   +68.3% │         │  2026-07-08
2026-06-11 │ SEZL.US│   128.83 │     167.32 │    +29.9% │     +40.3% │   7.0% │    0.83 │   65.2 │   7.8% │    +4.9% │       ✓ │  2026-07-08
2026-06-11 │ VIK.US │    93.18 │      97.97 │     +5.1% │     +12.2% │   3.7% │    0.84 │   64.3 │   4.3% │   +91.1% │         │  2026-07-08
2026-06-15 │ HUN.US │    15.89 │      11.30 │    -28.9% │     +12.3% │   4.3% │    0.83 │   64.1 │  10.4% │   +43.1% │         │  2026-07-08
2026-06-24 │ ICLR.US│   158.17 │     165.47 │     +4.6% │     +25.6% │   5.6% │    0.84 │   54.7 │   7.6% │    +7.4% │       ✓ │  2026-07-08
2026-06-25 │ AVTR.US│    10.08 │       9.76 │     -3.2% │     +17.3% │   4.8% │    0.84 │   59.2 │   3.8% │   -25.1% │         │  2026-07-08
2026-06-25 │ WSC.US │    29.07 │      25.13 │    -13.6% │     +17.6% │   4.1% │    0.89 │   66.0 │   9.1% │    +5.1% │         │  2026-07-08
2026-07-01 │ UTI.US │    47.02 │      49.43 │     +5.1% │     +20.7% │   5.2% │    0.85 │   62.4 │  10.7% │   +38.7% │       ✓ │  2026-07-08
2026-07-06 │ DRVN.US│    15.08 │      14.82 │     -1.7% │     +13.1% │   4.7% │    0.78 │   57.4 │  16.3% │   -15.8% │         │  2026-07-08
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Total bk50d_s12_tr20_v1.2_roc100 signals in window: 12  |  Also in bk50d_s20_tr20_v1.2_roc100: 4
```

## Signals not in bk50d_s20_tr20_v1.2_roc100

```
=== bk50d_s12_tr20_v1.2_roc100 signals NOT in bk50d_s20_tr20_v1.2_roc100 (N=8) — what's missing ===

  2026-06-01 DUOL.US %abv SMA50=+14.7% < 20% threshold — short by 5.3pp
  2026-06-01 LC.US   %abv SMA50=+15.7% < 20% threshold — short by 4.3pp
  2026-06-08 PBI.US  %abv SMA50=+18.9% < 20% threshold — short by 1.1pp
  2026-06-11 VIK.US  %abv SMA50=+12.2% < 20% threshold — short by 7.8pp
  2026-06-15 HUN.US  %abv SMA50=+12.3% < 20% threshold — short by 7.7pp
  2026-06-25 AVTR.US %abv SMA50=+17.3% < 20% threshold — short by 2.7pp
  2026-06-25 WSC.US  %abv SMA50=+17.6% < 20% threshold — short by 2.4pp
  2026-07-06 DRVN.US %abv SMA50=+13.1% < 20% threshold — short by 6.9pp
```

## Cohort Analysis — bk50d_s12_tr20_v1.2_roc100 by %abv SMA50 at entry

Med%/Mean%/Win%/PF/Sortino are computed on the mark-to-latest-price Change % (same as the Change % column above) grouped by each signal's %abv SMA50 value at entry. Unlike the backtest's Sortino, these are **not annualized** (positions have no fixed holding period here — each is still open, marked at whatever elapsed time has passed since entry), but downside_dev keeps the backtest's convention (RMS of negative returns over all N, positives count as 0). MaxDD% is the mean of each signal's own peak-to-trough decline (raw close) from entry through its latest available date.

```
Cohort        N     Med%    Mean%    Win%     PF  Sortino  MaxDD%
-----------------------------------------------------------------
[12-15)       4    +1.7%    -4.3%   50.0%   0.43    -0.30   13.8%
[15-17.5)     2   -51.1%   -51.1%    0.0%   0.00    -0.73   52.5%
[17.5-20)     2    -5.7%    -5.7%   50.0%   0.16    -0.59   10.4%
[>=20)        4   +10.3%   +13.8%  100.0%    inf      n/a    6.6%
```

### mean(Mean%) vs benchmarks

`mean(Mean%)` is the unweighted average of the four cohort Mean% values above (not weighted by N per cohort). SPY.US/QQQ.US are raw-close buy-and-hold over the same window, no dividend reinvestment — same convention as Entry $/Curr Price/Change %.

```
mean(Mean%) across cohorts:    -11.8%
SPY.US buy-and-hold:            -1.7%   (2026-06-01 → 2026-07-08)
QQQ.US buy-and-hold:            -4.2%   (2026-06-01 → 2026-07-08)
```
