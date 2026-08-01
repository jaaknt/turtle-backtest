# Qullamaggie Relax Sweep — bk50d_s20_v2.0 / 366d

Run date: 2026-08-01 10:58:58 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Eval period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar); entries without 366d of forward data skipped |
| Baseline | bk50d_s20_v2.0: 50d-high breakout, close >20% above SMA50, next-day adjusted-open entry |
| Baseline fixed filters | roc_12m<100%, vol_surge<2.0x, RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown 30d, mcap>=1.5B excl Comm/RE |
| Ranking gate | QullamaggieRanking >= 40, applied to every variant including baseline |
| Signal layer | turtlex/research/qullamaggie.py (parity-tested against QullamaggieStrategy) |
| Universe note | companies with a NULL sector are excluded from every variant, matching the production universe; the pre-migration run of this study admitted them, so the baseline row is not comparable with earlier versions of this document |
| Variants | each relaxes exactly one dimension (see table) |
| Combo selection | variants with Sortino AND Mean% >= 95% of baseline, ranked by F/mo; top-2 and top-3 combined (qualified: p2, p3, sect+CommRE, cd15, adr2.5) |
| Universe load | mcap >= 1.0B, all sectors (variant filters applied per run) |

Variant key: `cd15` cooldown 30→15d; `p3` min price $5→$3; `mcap1.0B` market-cap floor $1.5B→$1.0B; `sect+CommRE` re-admit Communication Services/Real Estate; `p2` min price $5→$2; `sma16`/`sma12` close-above-SMA50 threshold 20%→16%/12%; `adr2.5` ADR%(20) floor 3.0%→2.5%.

## Results

```text
Variant                                   N   F/mo   Win%    Mean%     Med%  Sortino      PF   MaxDD%
─────────────────────────────────────────────────────────────────────────────────────────────────────
baseline (bk50d_s20_v2.0)              1033    7.5   75.9   +60.27   +44.53    3.591    9.95    38.16
p2                                     1154    8.4   76.3   +68.10   +45.15    3.901   10.87    39.04
cd15                                   1106    8.1   75.9   +60.78   +43.57    3.633   10.06    38.19
p3                                     1121    8.2   76.1   +62.83   +44.44    3.608   10.14    38.76
adr2.5                                 1038    7.6   76.0   +60.24   +44.35    3.598    9.99    38.12
sect+CommRE                            1121    8.2   75.9   +59.33   +44.26    3.475    9.71    38.20
sma16                                  1159    8.5   74.0   +57.97   +41.43    3.360    9.10    38.69
mcap1.0B                               1142    8.3   73.7   +57.40   +41.12    3.187    8.57    38.97
sma12                                  1334    9.7   72.7   +56.18   +38.36    3.180    8.44    38.67
combo(p2+p3)                           1121    8.2   76.1   +62.83   +44.44    3.608   10.14    38.76
combo(p2+p3+sect+CommRE)               1213    8.9   76.1   +61.78   +43.79    3.504    9.90    38.75
combo(p2+p3+cd15)                      1201    8.8   76.2   +63.49   +43.60    3.670   10.29    38.75
```

## F/mo gain per unit of Sortino given up

- `p2` — ΔF/mo +0.9, ΔSortino +0.310, ΔMean% +7.83pp → Sortino cost: none (improved)
- `p3` — ΔF/mo +0.6, ΔSortino +0.016, ΔMean% +2.56pp → Sortino cost: none (improved)
- `cd15` — ΔF/mo +0.5, ΔSortino +0.042, ΔMean% +0.51pp → Sortino cost: none (improved)
- `adr2.5` — ΔF/mo +0.0, ΔSortino +0.007, ΔMean% -0.03pp → Sortino cost: none (improved)
- `sect+CommRE` — ΔF/mo +0.6, ΔSortino -0.116, ΔMean% -0.94pp → F/mo gain per unit Sortino lost: 5.5
- `sma12` — ΔF/mo +2.2, ΔSortino -0.412, ΔMean% -4.10pp → F/mo gain per unit Sortino lost: 5.3
- `sma16` — ΔF/mo +0.9, ΔSortino -0.231, ΔMean% -2.30pp → F/mo gain per unit Sortino lost: 4.0
- `mcap1.0B` — ΔF/mo +0.8, ΔSortino -0.404, ΔMean% -2.87pp → F/mo gain per unit Sortino lost: 2.0

## Caveats

- Same survivorship/static-market-cap caveats as the v4 backtest (see docs/research/result-qullamaggie-backtest-v4.md Findings). The `mcap1.0B` and `p3` variants lean harder on the static market-cap snapshot: smaller/cheaper names that later grew into the snapshot are over-represented, so treat their gains as a ceiling.
- The 2015-2026 window differs from the headline 2021-2026 eval; absolute Sortino/Mean% levels are not directly comparable across the two docs — compare variants against the baseline row of THIS table.
- Single 366d hold only; relaxations may rank differently at 91d/184d.
