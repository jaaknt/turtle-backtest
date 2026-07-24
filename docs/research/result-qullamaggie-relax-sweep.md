# Qullamaggie Relax Sweep — bk50d_s20_v1.3_roc100 / 366d

Run date: 2026-07-23

## Configuration

| Parameter | Value |
|---|---|
| Eval period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar); entries without 366d of forward data skipped |
| Baseline | bk50d_s20_v1.3_roc100: 50d-high breakout, close >20% above SMA50 |
| Baseline fixed filters | vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x, RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown 30d, mcap>=1.5B excl Comm/RE |
| Variants | each relaxes exactly one dimension (see table) |
| Combo selection | variants with Sortino AND Mean% >= 95% of baseline, ranked by F/mo; top-2 and top-3 combined (qualified: cd15, p3) |
| Universe load | mcap >= 1.0B, all sectors (variant filters applied per run) |

Variant key: `cd15` cooldown 30→15d; `p3` min price $5→$3; `mcap1.0B` market-cap floor $1.5B→$1.0B; `sect+CommRE` re-admit Communication Services/Real Estate.

## Results

```text
Variant                                   N   F/mo   Win%    Mean%     Med%  Sortino      PF   MaxDD%
─────────────────────────────────────────────────────────────────────────────────────────────────────
baseline (bk50d_s20_v1.3_roc100)        990    7.2   75.8   +56.09   +39.85    3.415    9.70    35.99
cd15                                   1048    7.6   75.5   +55.60   +38.30    3.379    9.53    36.05
p3                                     1048    7.6   76.0   +57.06   +39.80    3.334    9.56    36.54
sect+CommRE                            1075    7.8   75.3   +54.62   +38.01    3.198    9.06    36.36
mcap1.0B                               1074    7.8   73.6   +54.15   +36.84    3.071    8.42    36.92
combo(cd15+p3)                         1108    8.1   75.7   +56.68   +38.64    3.316    9.45    36.55
```

## F/mo gain per unit of Sortino given up

- `cd15` — ΔF/mo +0.4, ΔSortino -0.036, ΔMean% -0.48pp → F/mo gain per unit Sortino lost: 11.6
- `p3` — ΔF/mo +0.4, ΔSortino -0.081, ΔMean% +0.97pp → F/mo gain per unit Sortino lost: 5.2
- `sect+CommRE` — ΔF/mo +0.6, ΔSortino -0.217, ΔMean% -1.46pp → F/mo gain per unit Sortino lost: 2.9
- `mcap1.0B` — ΔF/mo +0.6, ΔSortino -0.344, ΔMean% -1.93pp → F/mo gain per unit Sortino lost: 1.8

## Caveats

- Same survivorship/static-market-cap caveats as the v4 backtest (see docs/research/result-qullamaggie-backtest-v4.md Findings). The `mcap1.0B` and `p3` variants lean harder on the static market-cap snapshot: smaller/cheaper names that later grew into the snapshot are over-represented, so treat their gains as a ceiling.
- The 2015-2026 window differs from the headline 2021-2026 eval; absolute Sortino/Mean% levels are not directly comparable across the two docs — compare variants against the baseline row of THIS table.
- Single 366d hold only; relaxations may rank differently at 91d/184d.
