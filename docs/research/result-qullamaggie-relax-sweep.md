# Qullamaggie Relax Sweep — bk50d_s20_v1.2_roc100 / 366d

Run date: 2026-07-15

## Configuration

| Parameter | Value |
|---|---|
| Eval period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar); entries without 366d of forward data skipped |
| Baseline | bk50d_s20_v1.2_roc100: 50d-high breakout, close >20% above SMA50 |
| Baseline fixed filters | vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x, RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown 30d, mcap>=1.5B excl Comm/RE |
| Variants | each relaxes exactly one dimension (see table) |
| Combo selection | variants with Sortino AND Mean% >= 95% of baseline, ranked by F/mo; top-2 and top-3 combined (qualified: cd15, p3) |
| Universe load | mcap >= 1.0B, all sectors (variant filters applied per run) |

Variant key: `cd15` cooldown 30→15d; `p3` min price $5→$3; `mcap1.0B` market-cap floor $1.5B→$1.0B; `sect+CommRE` re-admit Communication Services/Real Estate.

## Results

```text
Variant                                   N   F/mo   Win%    Mean%     Med%  Sortino      PF   MaxDD%
─────────────────────────────────────────────────────────────────────────────────────────────────────
baseline (bk50d_s20_v1.2_roc100)        924    6.7   76.2   +56.32   +40.87    3.618   10.34    35.60
cd15                                    979    7.1   75.8   +55.78   +39.87    3.568   10.11    35.67
p3                                      974    7.1   76.4   +56.86   +40.87    3.495   10.11    36.16
sect+CommRE                            1001    7.3   75.8   +54.69   +39.84    3.348    9.57    35.92
mcap1.0B                               1015    7.4   74.7   +54.44   +38.36    3.308    9.23    36.17
combo(cd15+p3)                         1031    7.5   76.0   +56.45   +39.95    3.469    9.95    36.20
```

## F/mo gain per unit of Sortino given up

- `cd15` — ΔF/mo +0.4, ΔSortino -0.049, ΔMean% -0.54pp → F/mo gain per unit Sortino lost: 8.1
- `p3` — ΔF/mo +0.4, ΔSortino -0.122, ΔMean% +0.53pp → F/mo gain per unit Sortino lost: 3.0
- `mcap1.0B` — ΔF/mo +0.7, ΔSortino -0.309, ΔMean% -1.88pp → F/mo gain per unit Sortino lost: 2.1
- `sect+CommRE` — ΔF/mo +0.6, ΔSortino -0.270, ΔMean% -1.63pp → F/mo gain per unit Sortino lost: 2.1

## Caveats

- Same survivorship/static-market-cap caveats as the v4 backtest (see docs/research/result-qullamaggie-backtest-v4.md Findings). The `mcap1.0B` and `p3` variants lean harder on the static market-cap snapshot: smaller/cheaper names that later grew into the snapshot are over-represented, so treat their gains as a ceiling.
- The 2015-2026 window differs from the headline 2021-2026 eval; absolute Sortino/Mean% levels are not directly comparable across the two docs — compare variants against the baseline row of THIS table.
- Single 366d hold only; relaxations may rank differently at 91d/184d.
