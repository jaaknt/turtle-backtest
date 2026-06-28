# s15_tr15 Ranking-Feature Discovery

Run date: 2026-06-27
Trade set: bk50d_s15_tr15_v1.2_roc100 / 366d  |  N=279
Baseline (all trades): Win%=65.2  Med%=+15.57  Mean%=+34.05  Sortino=0.988

## Per-feature predictive power
IC = Spearman rank corr(feature, 366d return). Top/Bot = top vs bottom
tercile sorted ascending by feature.

feature                 IC |  TopMed%  TopWin%  TopSR |  BotMed%  BotWin%  BotSR | dir
--------------------------------------------------------------------------------------
adr_pct             +0.039 |   +23.32     66.7   1.14 |   +10.66     68.8   0.70 | +
pct_vs_sma50        +0.057 |   +10.32     61.3   1.25 |    +8.62     64.5   0.92 | +
tight_range_ratio   -0.057 |    +5.10     61.3   0.74 |   +19.00     69.9   0.98 | -
rsi14               +0.017 |   +22.69     71.0   1.17 |   +11.42     63.4   1.08 | +
roc_252d            -0.132 |    +6.15     59.1   0.87 |   +19.36     71.0   1.10 | +
roc_126d            -0.043 |   +19.00     72.0   1.06 |   +24.19     71.0   1.52 | +
roc_63d             -0.001 |   +19.00     68.8   0.93 |   +17.09     66.7   1.27 | +
ext_sma10           -0.090 |    +9.86     61.3   0.54 |   +22.69     69.9   1.60 | -
ext_sma20           -0.062 |    +9.96     60.2   0.52 |   +18.61     66.7   1.34 | -
ext_sma150          -0.049 |   +14.24     67.7   0.79 |   +24.19     71.0   1.57 | +
breakout_margin     -0.109 |    +9.17     59.1   0.44 |   +18.96     67.7   0.96 | +
ext_in_adr          +0.030 |   +19.03     62.4   1.05 |   +14.24     61.3   0.86 | -
sma10_20_spread     +0.054 |   +22.69     66.7   1.18 |    +2.85     58.1   0.57 | +
sma10_slope         +0.054 |   +22.69     66.7   1.18 |    +2.85     58.1   0.57 | +
vol_surge_ratio     -0.104 |    +7.99     59.1   0.59 |   +19.03     68.8   1.29 | +
vol_dryup_ratio     -0.069 |   +18.96     66.7   0.73 |   +17.09     68.8   1.69 | -
pos_52w             -0.121 |    +6.77     59.1   0.41 |   +20.95     69.9   1.15 | +

## Composite ranking scores

(A) Data-driven (|IC|>=0.05, empirical sign): pct_vs_sma50+, tight_range_ratio-, roc_252d-, ext_sma10-, ext_sma20-, breakout_margin-, sma10_20_spread+, vol_surge_ratio-, vol_dryup_ratio-, pos_52w-

(A) Data-driven composite
select            N   Win%     Med%    Mean%  Sortino   F/mo
----------------------------------------------------------
all             279   65.2   +15.57   +34.05    0.988   4.29
top 75%         209   70.3   +21.20   +44.34    1.337   3.22
top 50%         140   74.3   +26.76   +56.29    1.787   2.15
top 33%          92   73.9   +25.62   +52.72    1.543   1.42
top 25%          70   71.4   +24.84   +57.32    1.676   1.08

(B) Freshness + quality composite (8 features, equal weight)
select            N   Win%     Med%    Mean%  Sortino   F/mo
----------------------------------------------------------
all             279   65.2   +15.57   +34.05    0.988   4.29
top 75%         209   67.5   +19.03   +42.56    1.278   3.22
top 50%         140   75.0   +26.76   +50.27    1.504   2.15
top 33%          92   75.0   +27.69   +54.03    1.582   1.42
top 25%          70   78.6   +28.43   +53.10    1.344   1.08

---

## Findings & Proposed Ranking Algorithm

### What actually predicts the 366d return (N=279)

The single strongest, most coherent theme is **"freshness" — penalise already-extended
setups**. The four strongest predictors are all negative-signed:

| Feature | IC | Reading |
|---|---:|---|
| `roc_252d` (12m momentum) | **−0.132** | The *less* a name has already run over 12m, the better. Early-stage > late-stage. |
| `pos_52w` (position in 52w range) | **−0.121** | Lower in its yearly range beats names pinned at the highs. |
| `breakout_margin` (close vs 50d high) | **−0.109** | Don't chase gaps far past the pivot; small, clean clears win. |
| `vol_surge_ratio` (breakout-day rel. volume) | **−0.104** | Within the 1.1–2.0× band, *moderate* volume beats the loudest spikes. |
| `ext_sma10` / `ext_sma20` (short-term extension) | −0.090 / −0.062 | Enter near the pivot, not stretched above the fast MAs. |

Secondary, weaker signals:
- `adr_pct` **+0.039** — higher ADR does help (Top-tercile Med +23% vs +11%), but the
  effect is weaker than the user's hypothesis assumed.
- `sma10_20_spread` / `sma10_slope` **+0.054** — a steeper short-term trend helps
  (these two are numerically identical; keep one).
- `tight_range_ratio` **−0.057** — tighter base is mildly better.

**Surprises vs the prior hypothesis:** ADR is only weakly predictive; SMA10/20 matter via
*low extension* (entering near the pivot), not via being far above them; and the dominant
edge is `roc_252d` / `pos_52w` — i.e. *not-yet-extended* names, even though `roc_252d` is
already capped at 100% by the entry filter.

### Proposed score

Equal-weight z-score composite (rank descending, keep the top slice):

```
score =  z(adr_pct) + z(sma10_20_spread)
       − z(roc_252d) − z(pos_52w) − z(ext_sma10) − z(breakout_margin)
       − z(tight_range_ratio) − z(vol_surge_ratio)
```

Each `z(x) = (x − mean) / std` over the candidate pool. Signs follow the empirical IC.

### Selection result (in-sample)

| Composite | Slice | N | Win% | Med% | Sortino | F/mo |
|---|---|--:|--:|--:|--:|--:|
| baseline (no ranking) | all | 279 | 65.2 | +15.6 | 0.99 | 4.3 |
| Data-driven (10 feat) | top 50% | 140 | 74.3 | +26.8 | **1.79** | 2.15 |
| Freshness+quality (8 feat) | top 50% | 140 | 75.0 | +26.8 | 1.50 | 2.15 |
| Freshness+quality (8 feat) | top 33% | 92 | 75.0 | +27.7 | 1.58 | 1.42 |
| Freshness+quality (8 feat) | top 25% | 70 | **78.6** | +28.4 | 1.34 | 1.08 |

Ranking lifts Sortino from 0.99 → ~1.5–1.8 and Med from +15.6% → ~+27% while halving the
trade count. To stay near the **~3 signals/month** target, take the **top ~70%** slice
(SR ≈ 1.3–1.34, ~3.2/mo) rather than the more aggressive top-50%.

### ⚠️ Caveat — this is in-sample

IC and the composite are measured on the same 279 trades, so the lift is an optimistic
upper bound. Before trusting it, validate out-of-sample: rank within each calendar month
using only data available up to that month, or train the signs/weights on 2021–2023 and
test on 2024–2026. The individual feature signs are economically sensible and unlikely to
flip, but the magnitude will shrink.
