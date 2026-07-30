# Qullamaggie Backtest v4 — Results

Run date: 2026-07-30

## Configuration

| Parameter | Value |
|---|---|
| Algorithm version | 2.0 (encoded as `_v2.0` in the names below) |
| Breakout | 50d high |
| Entry | next trading day's adjusted open (within 7 cal days of the signal) |
| Exit | close of the first bar at or after entry + hold |
| SMA thresh sweep | 12%, 16%, 20% |
| Tight range | disabled (commented out) |
| Hold sweep | 366d (calendar) |
| Ranking | QullamaggieRanking (ADR 40 / SMA50 35 / price 25) |
| Ranking gate sweep | ungated, ≥ 40 |
| vol_dry_up | avg_vol_10 < 90% × avg_vol_50 |
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
| Eval period | 2021-01-01 – 2026-07-30 |
| Burn-in (indicators only) | 2019-01-02 – 2021-01-01 |
| Universe | US common stocks, market_cap ≥ 1.5B, excl. Comm/RE |

## Rankings — No Ranking Condition

```text
Period: 2021-01-01 – 2026-07-30  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s20_v2.0                   366d   388   64.9   +54.43    +54.25   +24.26   +76.23   6.62    2.721    41.25   -63.32    5.9   54.8     56    5/5  ✓
   2  bk50d_s16_v2.0                   366d   634   63.1   +44.32    +44.17   +17.71   +66.34   5.37    2.181    39.89   -62.56    9.6   44.1     41    5/5  ✓
   3  bk50d_s12_v2.0                   366d   988   61.6   +37.01    +36.89   +13.85   +56.61   4.67    1.848    38.77   -61.21   15.0   37.6     33    5/5  ✓

Valid combinations: 3  |  Consistent: 3
```

## Consistent Combinations

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s20_v2.0` | `366d` — SR=2.721, Win%=64.9, Med%=+24.26, AnnMean%=+54.25, Q75%=+76.23, MaxDD%=41.25, CVaR%=-63.32, Yrs+=5/5, N=388
- `bk50d_s16_v2.0` | `366d` — SR=2.181, Win%=63.1, Med%=+17.71, AnnMean%=+44.17, Q75%=+66.34, MaxDD%=39.89, CVaR%=-62.56, Yrs+=5/5, N=634
- `bk50d_s12_v2.0` | `366d` — SR=1.848, Win%=61.6, Med%=+13.85, AnnMean%=+36.89, Q75%=+56.61, MaxDD%=38.77, CVaR%=-61.21, Yrs+=5/5, N=988

## Rankings — Ranking Gate Sweep (R ≥ 40)

Same signals, but a trade is taken only if its `QullamaggieRanking` score (`turtlex/strategy/ranking/qullamaggie.py`) is ≥ R, swept over 40 (40 is the `--min-signal-ranking` default). The score is computed from the same shift-1 indicators the entry filter used (`adr_pct`, `pct_vs_sma50`) plus the raw signal-date close, so it adds no look-ahead.

```text
Period: 2021-01-01 – 2026-07-30  |  HOLD_MAX_CAL=366d
Fixed: vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x (no lower bound), RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K
Sortino: mean / RMS(min(r,0)) over all N × sqrt(365/hold), min 10 losers (turtlex/backtest/metrics.py)
Ranking gate sweep: QullamaggieRanking ≥ 40

   #  Entry Signal                      Exit     N   Win%    Mean%  AnnMean%     Med%     Q75%     PF  Sortino   MaxDD%    CVaR%   F/mo  RkAvg  RkMed   Yrs+  C
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1  bk50d_s12_v2.0 R≥40              366d   398   62.3   +51.04    +50.87   +21.90   +72.66   5.78    2.424    42.87   -64.25    6.0   58.6     57    5/5  ✓
   2  bk50d_s20_v2.0 R≥40              366d   276   62.7   +52.76    +52.58   +20.82   +76.49   5.73    2.380    44.34   -68.16    4.2   63.3     63    4/4  ✓
   3  bk50d_s16_v2.0 R≥40              366d   328   61.3   +49.81    +49.65   +18.83   +73.19   5.30    2.225    44.15   -66.21    5.0   61.2     60    4/4  ✓

Valid combinations: 3  |  Consistent: 3
```

## Consistent Combinations (Ranking ≥ 40)

Sortino > 0 in ≥70% of complete calendar years with ≥10 negative trades, and ≥3 valid years.

- `bk50d_s12_v2.0 R≥40` | `366d` — SR=2.424, Win%=62.3, Med%=+21.90, AnnMean%=+50.87, Q75%=+72.66, MaxDD%=42.87, CVaR%=-64.25, Yrs+=5/5, N=398
- `bk50d_s20_v2.0 R≥40` | `366d` — SR=2.380, Win%=62.7, Med%=+20.82, AnnMean%=+52.58, Q75%=+76.49, MaxDD%=44.34, CVaR%=-68.16, Yrs+=4/4, N=276
- `bk50d_s16_v2.0 R≥40` | `366d` — SR=2.225, Win%=61.3, Med%=+18.83, AnnMean%=+49.65, Q75%=+73.19, MaxDD%=44.15, CVaR%=-66.21, Yrs+=4/4, N=328

## Ranking Gate Selectivity

How many signals each gate removes, at signal level.

```text
Entry Signal               Gate   Signals   Passing   Rejected   Reject%
────────────────────────────────────────────────────────────────────────
bk50d_s12_v2.0               40      1364       547        817     59.9%
bk50d_s16_v2.0               40       875       457        418     47.8%
bk50d_s20_v2.0               40       527       388        139     26.4%
```

## Findings & Caveats

### Ideas to improve

- source point-in-time market cap (or shares outstanding × price at entry) instead of a static snapshot
- source a delisted-ticker history if available to address survivorship
- add a slippage/commission assumption on top of the next-day-open fill
- widen the gate sweep past 40 to find where the score stops separating outcomes
- report the ranking's own decile spread within a fixed X so the gate's effect can be read independently of the SMA threshold
- account for trade overlap (e.g. block-bootstrap or effective-sample-size adjustment) when judging Sortino confidence
- re-run all three windows (2010-2015, 2016-2020, 2021-present) before accepting any parameter change — a change that only improves the window it was chosen on is fitted to that window
- pick the ranking gate per SMA threshold rather than one R≥40 across s12/s16/s20; the same score rejects a very different share of each, so it is not the same filter at each
- report each year's negative-trade count next to its Sortino — under the gate a thin window can fall below the 10-loser bar and silently drop out of the Yrs+ denominator

### Cross-window read (hand-written after the 2026-07-30 run of all three windows)

The same three algorithms, run over the two cross-check windows
(`result-qullamaggie-backtest-v4-2010-2015.md`, `result-qullamaggie-backtest-v4-2016-2020.md`):

```text
                 ungated Sortino          R≥40 Sortino            Win%  (ungated)        N (ungated)
Window          s20    s16    s12       s20    s16    s12       s20   s16   s12       s20   s16    s12
─────────────────────────────────────────────────────────────────────────────────────────────────────
2010-2015     0.706  0.847  0.613     0.716  0.799  0.670      57.9  60.5  57.1       107   233    450
2016-2020     4.597  3.733  3.234     5.685  5.619  4.839      84.8  80.9  79.5       584   868   1235
2021-2026     2.721  2.181  1.848     2.380  2.225  2.424      64.9  63.1  61.6       388   634    988
```

- **The level is regime-dependent; the ordering mostly is not.** Ungated Sortino spans 0.61-4.60 across
  the three windows — a 7x range on identical rules. Within a window, s20 > s16 > s12 holds in
  2016-2020 and 2021-2026; 2010-2015 inverts s20 and s16 on a 107-trade sample. Quote the ordering,
  never the level, and never a single window's level as "the" performance of this strategy.
- **The R≥40 gate pays at s12 and costs at s20.** Gated-minus-ungated Sortino: s12 +0.06 / +1.61 /
  +0.58, s16 −0.05 / +1.89 / +0.04, s20 +0.01 / +1.09 / −0.34 (2010-2015 / 2016-2020 / 2021-2026).
  The gate rejects 74% / 58% / 60% of s12 signals but only 34% / 24% / 26% of s20's. At s20 the entry
  filter has already selected on the same dimension the score's 35-point SMA50 term measures, so the
  gate largely re-states the filter; at s12 it is doing independent work.
- **Under the gate, the consistency flag stops being readable.** Gated 2010-2015 flags 0 of 3
  combinations and gated 2016-2020 flags 1 of 3 — not because annual Sortino turned negative, but
  because the gate leaves fewer than 10 losing trades in most years, so those years drop out of the
  denominator entirely (`Yrs+` falls to `0/0`, `2/2`). Read the `Yrs+` denominator before the ✓.
- **Survivorship is the largest unquantified bias, and it grows with age.** 2,499 US common stocks
  traded in 2010; 227 are removed by the sector rule and a further 1,000 by a market-cap snapshot
  taken in 2026 — 44% of the sector-eligible 2010 tape. The universe is effectively "companies that
  had reached $1.5B by 2026", applied retroactively to a 2010 signal. Delisted names are largely
  absent from `turtle.daily_bars` to begin with, so the 2,499 is itself already survivor-filtered.
  Every window is inflated by this; the older two most of all.
- **2016-2020's headline is partly borrowed from 2021.** A 366-day hold on a 2020 signal exits in
  2021 (SPY +30.5%, QQQ +29.2%) — a year outside the window being reported. QQQ averaged +24.7%/yr
  over 2016-2020 against +16.4%/yr over 2010-2015. Win rates of 79-85% and profit factors of 10-21
  are properties of that tape, not of the entry rule.
