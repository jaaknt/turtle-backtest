# Qullamaggie Relax Sweep — bk50d_s20_v2.0 / 366d

Run date: 2026-10-24 18:16:12 Tallinn time

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
| Combo selection | variants with Sortino AND Mean% >= 95% of baseline, ranked by F/mo; top-2 and top-3 combined (qualified: sma16, p2, p3, sect+CommRE, cd15, adr2.5) |
| Universe load | mcap >= 1.0B, all sectors (variant filters applied per run) |

Variant key: `cd15` cooldown 30→15d; `p3` min price $5→$3; `mcap1.0B` market-cap floor $1.5B→$1.0B; `sect+CommRE` re-admit Communication Services/Real Estate; `p2` min price $5→$2; `sma16`/`sma12` close-above-SMA50 threshold 20%→16%/12%; `adr2.5` ADR%(20) floor 3.0%→2.5%.

## Results

```text
Variant                                   N   F/mo   Win%    Mean%     Med%  Sortino      PF   MaxDD%
─────────────────────────────────────────────────────────────────────────────────────────────────────
baseline (bk50d_s20_v2.0)              1517   11.1   75.1   +56.70   +41.23    3.447    9.54    37.35
p2                                     1679   12.3   75.0   +62.42   +41.23    3.685   10.18    38.34
cd15                                   1629   11.9   75.3   +57.24   +40.82    3.490    9.68    37.38
adr2.5                                 1524   11.1   75.2   +56.61   +41.07    3.447    9.55    37.33
p3                                     1636   11.9   74.9   +58.26   +41.01    3.437    9.56    38.06
sect+CommRE                            1630   11.9   75.2   +56.01   +40.93    3.343    9.30    37.39
sma16                                  1702   12.4   73.6   +56.25   +39.20    3.321    9.03    37.88
sma12                                  1772   12.9   73.1   +55.33   +37.83    3.154    8.53    38.32
mcap1.0B                               1733   12.6   72.8   +54.62   +38.53    3.102    8.29    38.26
combo(sma16+p2)                        1915   14.0   73.4   +61.67   +39.29    3.520    9.53    38.93
combo(sma16+p2+p3)                     1857   13.6   73.4   +58.15   +38.53    3.336    9.09    38.59
combo(p2+cd15)                         1808   13.2   75.3   +62.87   +40.94    3.740   10.36    38.35
combo(p2+cd15+adr2.5)                  1815   13.2   75.4   +62.80   +40.85    3.744   10.39    38.33
```

## F/mo gain per unit of Sortino given up

- `p2` — ΔF/mo +1.2, ΔSortino +0.239, ΔMean% +5.72pp → Sortino cost: none (improved)
- `cd15` — ΔF/mo +0.8, ΔSortino +0.043, ΔMean% +0.54pp → Sortino cost: none (improved)
- `adr2.5` — ΔF/mo +0.1, ΔSortino +0.000, ΔMean% -0.09pp → Sortino cost: none (improved)
- `p3` — ΔF/mo +0.9, ΔSortino -0.010, ΔMean% +1.56pp → F/mo gain per unit Sortino lost: 90.8
- `sma16` — ΔF/mo +1.4, ΔSortino -0.126, ΔMean% -0.45pp → F/mo gain per unit Sortino lost: 10.7
- `sect+CommRE` — ΔF/mo +0.8, ΔSortino -0.104, ΔMean% -0.69pp → F/mo gain per unit Sortino lost: 8.0
- `sma12` — ΔF/mo +1.9, ΔSortino -0.292, ΔMean% -1.37pp → F/mo gain per unit Sortino lost: 6.4
- `mcap1.0B` — ΔF/mo +1.6, ΔSortino -0.345, ΔMean% -2.08pp → F/mo gain per unit Sortino lost: 4.6

## Caveats

- Same survivorship/static-market-cap caveats as the v4 backtest (see docs/research/result-qullamaggie-backtest-v4.md Findings). The `mcap1.0B` and `p3` variants lean harder on the static market-cap snapshot: smaller/cheaper names that later grew into the snapshot are over-represented, so treat their gains as a ceiling.
- The 2015-2026 window differs from the headline 2021-2026 eval; absolute Sortino/Mean% levels are not directly comparable across the two docs — compare variants against the baseline row of THIS table.
- Single 366d hold only; relaxations may rank differently at 91d/184d.
