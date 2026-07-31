# Qullamaggie Relax Sweep — bk50d_s20_v2.0 / 366d

Run date: 2026-08-01 00:51:02 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Eval period | 2015-01-01 – 2026-06-26 |
| Hold | 366d (calendar); entries without 366d of forward data skipped |
| Baseline | bk50d_s20_v2.0: 50d-high breakout, close >20% above SMA50, next-day adjusted-open entry |
| Baseline fixed filters | vol_dry_up<90%, roc_12m<100%, vol_surge<2.0x, RSI<70, ADR>=3.0%, ADR_change<90%, SPY>200d SMA, close>$5&<$250, avg_vol>=500K, cooldown 30d, mcap>=1.5B excl Comm/RE |
| Ranking gate | QullamaggieRanking >= 40, applied to every variant including baseline |
| Signal layer | turtlex/research/qullamaggie.py (parity-tested against QullamaggieStrategy) |
| Universe note | companies with a NULL sector are excluded from every variant, matching the production universe; the pre-migration run of this study admitted them, so the baseline row is not comparable with earlier versions of this document |
| Variants | each relaxes exactly one dimension (see table) |
| Combo selection | variants with Sortino AND Mean% >= 95% of baseline, ranked by F/mo; top-2 and top-3 combined (qualified: vdu1.0, p2, p3, cd15, adr2.5) |
| Universe load | mcap >= 1.0B, all sectors (variant filters applied per run) |

Variant key: `cd15` cooldown 30→15d; `p3` min price $5→$3; `mcap1.0B` market-cap floor $1.5B→$1.0B; `sect+CommRE` re-admit Communication Services/Real Estate; `p2` min price $5→$2; `sma16`/`sma12` close-above-SMA50 threshold 20%→16%/12%; `adr2.5` ADR%(20) floor 3.0%→2.5%; `vdu1.0` vol_dry_up avg_vol_10 < 90%→100% of avg_vol_50 (i.e. filter effectively off).

## Results

```text
Variant                                   N   F/mo   Win%    Mean%     Med%  Sortino      PF   MaxDD%
─────────────────────────────────────────────────────────────────────────────────────────────────────
baseline (bk50d_s20_v2.0)               737    5.4   76.5   +60.43   +45.00    3.562   10.08    37.71
p2                                      819    6.0   76.9   +66.05   +44.65    3.717   10.53    38.67
vdu1.0                                  873    6.4   76.6   +61.13   +44.44    3.655   10.24    37.92
adr2.5                                  741    5.4   76.7   +60.26   +44.64    3.562   10.10    37.69
cd15                                    778    5.7   76.1   +59.39   +43.64    3.465    9.73    37.79
p3                                      795    5.8   76.9   +61.44   +44.44    3.447    9.87    38.31
sect+CommRE                             802    5.9   76.3   +59.05   +44.26    3.370    9.56    37.89
sma16                                   828    6.0   74.0   +58.06   +42.39    3.327    9.07    38.28
sma12                                   946    6.9   73.2   +56.51   +40.24    3.230    8.65    38.25
mcap1.0B                                813    5.9   74.3   +58.09   +42.51    3.179    8.70    38.63
combo(vdu1.0+p2)                        972    7.1   76.9   +67.93   +44.49    3.931   11.05    38.71
combo(vdu1.0+p2+p3)                     944    6.9   76.8   +62.26   +43.74    3.590   10.20    38.40
combo(vdu1.0+p2+adr2.5)                 976    7.1   76.9   +67.77   +44.26    3.929   11.07    38.69
```

## F/mo gain per unit of Sortino given up

- `vdu1.0` — ΔF/mo +1.0, ΔSortino +0.093, ΔMean% +0.70pp → Sortino cost: none (improved)
- `p2` — ΔF/mo +0.6, ΔSortino +0.154, ΔMean% +5.62pp → Sortino cost: none (improved)
- `adr2.5` — ΔF/mo +0.0, ΔSortino -0.001, ΔMean% -0.17pp → F/mo gain per unit Sortino lost: 42.5
- `sma12` — ΔF/mo +1.5, ΔSortino -0.332, ΔMean% -3.93pp → F/mo gain per unit Sortino lost: 4.6
- `p3` — ΔF/mo +0.4, ΔSortino -0.115, ΔMean% +1.01pp → F/mo gain per unit Sortino lost: 3.7
- `cd15` — ΔF/mo +0.3, ΔSortino -0.097, ΔMean% -1.05pp → F/mo gain per unit Sortino lost: 3.1
- `sma16` — ΔF/mo +0.7, ΔSortino -0.235, ΔMean% -2.37pp → F/mo gain per unit Sortino lost: 2.8
- `sect+CommRE` — ΔF/mo +0.5, ΔSortino -0.192, ΔMean% -1.38pp → F/mo gain per unit Sortino lost: 2.5
- `mcap1.0B` — ΔF/mo +0.6, ΔSortino -0.383, ΔMean% -2.35pp → F/mo gain per unit Sortino lost: 1.4

## Caveats

- Same survivorship/static-market-cap caveats as the v4 backtest (see docs/research/result-qullamaggie-backtest-v4.md Findings). The `mcap1.0B` and `p3` variants lean harder on the static market-cap snapshot: smaller/cheaper names that later grew into the snapshot are over-represented, so treat their gains as a ceiling.
- The 2015-2026 window differs from the headline 2021-2026 eval; absolute Sortino/Mean% levels are not directly comparable across the two docs — compare variants against the baseline row of THIS table.
- Single 366d hold only; relaxations may rank differently at 91d/184d.
