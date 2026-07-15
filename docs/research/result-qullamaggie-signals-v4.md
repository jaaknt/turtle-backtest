# bk50d_s12_v1.2_roc100 vs bk50d_s20_v1.2_roc100 — Signal Report

Run date: 2026-07-15

Period: 2026-06-01 – 2026-07-15

Entry $/Curr Price/Change % use raw (unadjusted) close — the real tradeable price. %abv SMA50/ADR%/ADR_CHG/RSI14/TR%/ROC252% are computed on the entry date, using the same split/dividend-adjusted series as scripts/qullamaggie-backtest-v4.py. Last date is the latest date with data available for that symbol in turtle.daily_bars.

```text
Date       │ Symbol │  Entry $ │ Curr Price │ 0.97*Entry │  Change % │ %abv SMA50 │   ADR% │ ADR_CHG │  RSI14 │    TR% │  ROC252% │ In s15? │ In s20? │ Reached? │   Last date
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
2026-06-01 │ DUOL.US│   117.97 │     128.35 │     114.43 │     +8.8% │     +14.7% │   5.7% │    0.90 │   56.0 │   7.7% │   -77.0% │         │         │        ✓ │  2026-07-14
2026-06-01 │ FA.US  │    17.07 │      21.15 │      16.56 │    +23.9% │     +30.8% │   5.4% │    0.83 │   50.5 │   7.4% │    +0.2% │       ✓ │       ✓ │        ✓ │  2026-07-14
2026-06-01 │ RNG.US │    49.10 │      41.30 │      47.63 │    -15.9% │     +21.8% │   6.6% │    0.86 │   43.8 │   6.8% │   +89.0% │       ✓ │       ✓ │        ✓ │  2026-07-14
2026-06-03 │ GEO.US │    23.60 │      29.78 │      22.89 │    +26.2% │     +19.5% │   4.3% │    0.83 │   66.5 │   3.7% │   -12.9% │       ✓ │         │          │  2026-07-14
2026-06-08 │ MOH.US │   198.41 │     241.56 │     192.46 │    +21.7% │     +16.9% │   3.9% │    0.80 │   56.0 │  10.5% │   -32.4% │       ✓ │         │        ✓ │  2026-07-14
2026-06-08 │ PBI.US │    16.94 │      17.77 │      16.43 │     +4.9% │     +18.9% │   3.4% │    0.89 │   62.4 │  10.3% │   +68.3% │       ✓ │         │        ✓ │  2026-07-14
2026-06-08 │ PRKS.US│    42.04 │      46.88 │      40.78 │    +11.5% │     +17.0% │   5.4% │    0.85 │   67.7 │  11.4% │    -2.4% │       ✓ │         │          │  2026-07-14
2026-06-09 │ BAX.US │    20.03 │      21.80 │      19.43 │     +8.8% │     +12.0% │   3.5% │    0.82 │   68.4 │   5.1% │   -33.3% │         │         │        ✓ │  2026-07-14
2026-06-11 │ ALK.US │    46.66 │      46.87 │      45.26 │     +0.5% │     +14.7% │   4.5% │    0.89 │   54.7 │  11.2% │    -9.5% │         │         │          │  2026-07-14
2026-06-11 │ SEZL.US│   128.83 │     182.39 │     124.97 │    +41.6% │     +40.3% │   7.0% │    0.83 │   65.2 │   7.8% │    +4.9% │       ✓ │       ✓ │          │  2026-07-14
2026-06-11 │ VIK.US │    93.18 │      97.65 │      90.38 │     +4.8% │     +12.2% │   3.7% │    0.84 │   64.3 │   4.3% │   +91.1% │         │         │          │  2026-07-14
2026-06-15 │ HUN.US │    15.89 │      11.91 │      15.41 │    -25.0% │     +12.3% │   4.3% │    0.83 │   64.1 │  10.4% │   +43.1% │         │         │        ✓ │  2026-07-14
2026-06-24 │ CRL.US │   202.10 │     231.21 │     196.04 │    +14.4% │     +15.6% │   4.4% │    0.80 │   62.3 │   4.5% │   +37.1% │       ✓ │         │          │  2026-07-14
2026-06-24 │ ICLR.US│   158.17 │     167.97 │     153.42 │     +6.2% │     +25.6% │   5.6% │    0.84 │   54.7 │   7.6% │    +7.4% │       ✓ │       ✓ │          │  2026-07-14
2026-06-24 │ RGEN.US│   138.40 │     147.13 │     134.25 │     +6.3% │     +13.7% │   4.8% │    0.88 │   57.8 │   5.5% │   +15.2% │         │         │        ✓ │  2026-07-14
2026-06-25 │ AVTR.US│    10.08 │      11.29 │       9.78 │    +12.0% │     +17.3% │   4.8% │    0.84 │   59.2 │   3.8% │   -25.1% │       ✓ │         │        ✓ │  2026-07-14
2026-06-25 │ CARR.US│    76.00 │      69.76 │      73.72 │     -8.2% │     +15.8% │   3.3% │    0.90 │   65.2 │   8.6% │    +6.1% │       ✓ │         │        ✓ │  2026-07-14
2026-06-25 │ WSC.US │    29.07 │      26.84 │      28.20 │     -7.7% │     +17.6% │   4.1% │    0.89 │   66.0 │   9.1% │    +5.1% │       ✓ │         │        ✓ │  2026-07-14
2026-06-26 │ YETI.US│    51.21 │      47.34 │      49.67 │     -7.6% │     +16.2% │   4.1% │    0.87 │   57.8 │   7.0% │   +69.0% │       ✓ │         │        ✓ │  2026-07-14
2026-07-01 │ OSCR.US│    31.90 │      31.07 │      30.94 │     -2.6% │     +37.0% │   6.8% │    0.90 │   56.9 │   5.7% │   +48.8% │       ✓ │       ✓ │        ✓ │  2026-07-14
2026-07-01 │ UTI.US │    47.02 │      46.65 │      45.61 │     -0.8% │     +20.7% │   5.2% │    0.85 │   62.4 │  10.7% │   +38.7% │       ✓ │       ✓ │          │  2026-07-14
2026-07-02 │ HRB.US │    40.04 │      40.94 │      38.84 │     +2.2% │     +12.4% │   3.3% │    0.84 │   59.5 │  14.5% │   -25.9% │         │         │        ✓ │  2026-07-14
2026-07-06 │ DRVN.US│    15.08 │      15.48 │      14.63 │     +2.7% │     +13.1% │   4.7% │    0.78 │   57.4 │  16.3% │   -15.8% │         │         │          │  2026-07-14
2026-07-09 │ GTLB.US│    33.86 │      32.98 │      32.84 │     -2.6% │     +23.7% │   5.3% │    0.86 │   66.6 │  17.5% │   -27.3% │       ✓ │       ✓ │        ✓ │  2026-07-14
2026-07-10 │ SN.US  │   152.65 │     149.89 │     148.07 │     -1.8% │     +21.7% │   3.8% │    0.79 │   67.8 │   6.3% │   +40.4% │       ✓ │       ✓ │          │  2026-07-14
2026-07-13 │ KMX.US │    54.87 │      55.73 │      53.22 │     +1.6% │     +21.0% │   4.5% │    0.80 │   49.4 │   6.3% │   -18.0% │       ✓ │       ✓ │          │  2026-07-14
2026-07-14 │ BBY.US │    83.98 │      83.98 │      81.46 │     +0.0% │     +20.9% │   3.0% │    0.85 │   67.5 │   8.8% │   +21.9% │       ✓ │       ✓ │          │  2026-07-14
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Total bk50d_s12_v1.2_roc100 signals in window: 27  |  Also in bk50d_s15_v1.2_roc100: 19  |  Also in bk50d_s20_v1.2_roc100: 10  |  Excluded as suspicious: 1
```

## Signals not in bk50d_s20_v1.2_roc100

```text
=== bk50d_s12_v1.2_roc100 signals NOT in bk50d_s20_v1.2_roc100 (N=17) — what's missing ===

  2026-06-01 DUOL.US %abv SMA50=+14.7% < 20% threshold — short by 5.3pp
  2026-06-03 GEO.US  %abv SMA50=+19.5% < 20% threshold — short by 0.5pp
  2026-06-08 MOH.US  %abv SMA50=+16.9% < 20% threshold — short by 3.1pp
  2026-06-08 PBI.US  %abv SMA50=+18.9% < 20% threshold — short by 1.1pp
  2026-06-08 PRKS.US %abv SMA50=+17.0% < 20% threshold — short by 3.0pp
  2026-06-09 BAX.US  %abv SMA50=+12.0% < 20% threshold — short by 8.0pp
  2026-06-11 ALK.US  %abv SMA50=+14.7% < 20% threshold — short by 5.3pp
  2026-06-11 VIK.US  %abv SMA50=+12.2% < 20% threshold — short by 7.8pp
  2026-06-15 HUN.US  %abv SMA50=+12.3% < 20% threshold — short by 7.7pp
  2026-06-24 CRL.US  %abv SMA50=+15.6% < 20% threshold — short by 4.4pp
  2026-06-24 RGEN.US %abv SMA50=+13.7% < 20% threshold — short by 6.3pp
  2026-06-25 AVTR.US %abv SMA50=+17.3% < 20% threshold — short by 2.7pp
  2026-06-25 CARR.US %abv SMA50=+15.8% < 20% threshold — short by 4.2pp
  2026-06-25 WSC.US  %abv SMA50=+17.6% < 20% threshold — short by 2.4pp
  2026-06-26 YETI.US %abv SMA50=+16.2% < 20% threshold — short by 3.8pp
  2026-07-02 HRB.US  %abv SMA50=+12.4% < 20% threshold — short by 7.6pp
  2026-07-06 DRVN.US %abv SMA50=+13.1% < 20% threshold — short by 6.9pp
```

## Excluded as suspicious data

Signals with a single-day raw-close move exceeding 50% between entry and the latest available date are dropped from the table, cross-check, and cohort analysis above — such a move is not organic price action for this universe (market cap ≥ $1.5B) and most likely reflects a delisting/halt-type event or a data anomaly.

```text
=== Excluded as suspicious data — single-day |Δraw_close| > 50% between entry and latest available date (N=1) ===

  2026-06-01 LC.US   max 1-day move 99.0% — likely a data anomaly or delisting/halt-type event, not organic price action
```

## Cohort Analysis — bk50d_s12_v1.2_roc100 by %abv SMA50 at entry

Med%/Mean%/Win%/PF/Sortino are computed on the mark-to-latest-price Change % (same as the Change % column above) grouped by each signal's %abv SMA50 value at entry. Unlike the backtest's Sortino, these are **not annualized** (positions have no fixed holding period here — each is still open, marked at whatever elapsed time has passed since entry), but downside_dev keeps the backtest's convention (RMS of negative returns over all N, positives count as 0). MaxDD% is the mean of each signal's own peak-to-trough decline (raw close) from entry through its latest available date.

```text
Cohort        N     Med%    Mean%    Win%     PF  Sortino  MaxDD%
-----------------------------------------------------------------
[12-15)       8    +3.7%    +1.1%   87.5%   1.36     0.13   10.8%
[15-17.5)     6   +11.8%    +7.3%   66.7%   3.78     1.61    6.6%
[17.5-20)     3    +4.9%    +7.8%   66.7%   4.05     1.76    8.4%
[>=20)       10    -0.4%    +5.0%   40.0%   3.09     0.95    7.6%
```

### mean(Mean%) vs benchmarks

`mean(Mean%)` is the unweighted average of the four cohort Mean% values above (not weighted by N per cohort). SPY.US/QQQ.US are raw-close buy-and-hold over the same window, no dividend reinvestment — same convention as Entry $/Curr Price/Change %.

```text
mean(Mean%) across cohorts:     +5.3%
SPY.US buy-and-hold:            -0.9%   (2026-06-01 → 2026-07-14)
QQQ.US buy-and-hold:            -3.1%   (2026-06-01 → 2026-07-14)
```
