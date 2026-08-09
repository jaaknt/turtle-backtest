# Qullamaggie Relax Sweep — bk50d_s20_v2.0 / 366d

Run date: 2026-08-09 18:57:51 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Eval period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar); entries without 366d of forward data skipped |
| Baseline | bk50d_s20_v2.0: 50d-high breakout, close >20% above SMA50, next-day adjusted-open entry |
| Baseline fixed filters | roc_12m<100%, vol_surge<2.0x, RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=100K, cooldown 30d, mcap>=1.5B excl Comm/RE |
| Ranking gate | QullamaggieRanking >= 44, applied to every variant including baseline |
| Signal layer | turtlex/research/qullamaggie.py (parity-tested against QullamaggieStrategy) |
| Universe note | companies with a NULL sector are excluded from every variant, matching the production universe; the pre-migration run of this study admitted them, so the baseline row is not comparable with earlier versions of this document |
| Variants | each relaxes exactly one dimension (see table) |
| Combo selection | variants with Sortino AND Mean% >= 95% of baseline, ranked by F/mo; top-2 and top-3 combined (qualified: sma16, p2, cd15, sect+CommRE, p3, adr2.5) |
| Universe load | mcap >= 1.0B, all sectors (variant filters applied per run) |

Variant key: `cd15` cooldown 30→15d; `p3` min price $5→$3; `mcap1.0B` market-cap floor $1.5B→$1.0B; `sect+CommRE` re-admit Communication Services/Real Estate; `p2` min price $5→$2; `sma16`/`sma12` close-above-SMA50 threshold 20%→16%/12%; `adr2.5` ADR%(20) floor 3.0%→2.5%.

## Results

```text
Variant                                   N   F/mo   Win%    Mean%     Med%  Sortino      PF   MaxDD%
─────────────────────────────────────────────────────────────────────────────────────────────────────
baseline (bk50d_s20_v2.0)              1541   11.2   74.9   +57.76   +41.49    3.454    9.41    37.58
p2                                     1694   12.4   75.1   +64.53   +42.31    3.773   10.28    38.48
p3                                     1654   12.1   74.9   +59.80   +41.23    3.495    9.58    38.22
cd15                                   1658   12.1   75.0   +58.08   +41.04    3.471    9.46    37.64
adr2.5                                 1548   11.3   74.9   +57.66   +41.29    3.454    9.41    37.57
sect+CommRE                            1657   12.1   74.9   +56.87   +41.00    3.348    9.17    37.60
sma16                                  1723   12.6   73.4   +57.22   +39.80    3.323    8.89    38.11
sma12                                  1786   13.0   73.2   +56.78   +38.61    3.234    8.64    38.43
mcap1.0B                               1747   12.8   72.6   +54.13   +38.18    2.962    7.91    38.56
combo(sma16+p2)                        1922   14.0   73.5   +63.39   +39.95    3.593    9.59    39.07
combo(sma16+p2+cd15)                   2092   15.3   73.4   +63.06   +39.35    3.574    9.51    39.20
combo(p2+cd15)                         1826   13.3   75.3   +64.60   +41.35    3.791   10.35    38.51
combo(p2+cd15+p3)                      1782   13.0   75.1   +60.23   +40.94    3.531    9.70    38.23
```

## F/mo gain per unit of Sortino given up

- `p2` — ΔF/mo +1.1, ΔSortino +0.319, ΔMean% +6.77pp → Sortino cost: none (improved)
- `cd15` — ΔF/mo +0.9, ΔSortino +0.017, ΔMean% +0.32pp → Sortino cost: none (improved)
- `p3` — ΔF/mo +0.8, ΔSortino +0.041, ΔMean% +2.05pp → Sortino cost: none (improved)
- `adr2.5` — ΔF/mo +0.1, ΔSortino +0.000, ΔMean% -0.10pp → Sortino cost: none (improved)
- `sma16` — ΔF/mo +1.3, ΔSortino -0.132, ΔMean% -0.53pp → F/mo gain per unit Sortino lost: 10.1
- `sma12` — ΔF/mo +1.8, ΔSortino -0.220, ΔMean% -0.98pp → F/mo gain per unit Sortino lost: 8.1
- `sect+CommRE` — ΔF/mo +0.8, ΔSortino -0.106, ΔMean% -0.88pp → F/mo gain per unit Sortino lost: 8.0
- `mcap1.0B` — ΔF/mo +1.5, ΔSortino -0.493, ΔMean% -3.63pp → F/mo gain per unit Sortino lost: 3.1

## Caveats

- Same survivorship/static-market-cap caveats as the v4 backtest (see docs/research/result-qullamaggie-backtest-v4.md Findings). The `mcap1.0B` and `p3` variants lean harder on the static market-cap snapshot: smaller/cheaper names that later grew into the snapshot are over-represented, so treat their gains as a ceiling.
- The 2015-2026 window differs from the headline 2021-2026 eval; absolute Sortino/Mean% levels are not directly comparable across the two docs — compare variants against the baseline row of THIS table.
- Single 366d hold only; relaxations may rank differently at 91d/184d.
