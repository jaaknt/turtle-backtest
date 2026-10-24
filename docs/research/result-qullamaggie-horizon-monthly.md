# Qullamaggie Marginal Monthly Performance by Signal Year (2015-2025)

Run date: 2026-10-24 17:25:40 Tallinn time

## Configuration

| Parameter | Value |
|---|---|
| Period | 2015-01-01 – 2025-12-31 (signal dates) |
| Algorithm | `bk50d_s12_v2.0` — 50d breakout, close >= 12% above 50d SMA |
| Horizon | **marginal months 1–18 after entry** (not the 366d fixed hold) |
| Entry | next trading day's split/dividend-adjusted open |
| Monthly mark | adjusted close of the first bar on or after entry + M calendar months |
| Cohort | **per cell — every signal with a mark at both ends of the month; see `N@M18` above** |
| Ranking gate | **all reported** — QullamaggieRanking >= 44, >= 60, >= 70, >= 80, and ungated |
| Fixed filters | RSI<70, ADR>=3.0%, ADR_change<90%, roc_12m<100%, vol_surge<2.0x |
| Market regime | SPY close > 200d SMA |
| Price range | > $5 and < $250 |
| Min avg vol (20d) | >= 100K |
| Cooldown | 30 calendar days |
| Universe | US common stocks, market_cap >= 1.5B, excl. Comm/RE |
| Signals | 4662 with an entry bar; 1814 at R>=44, 711 at R>=60, 315 at R>=70, 181 at R>=80 |

## Gate comparison

| Gate | Signals | % of universe | N@M18 | M1–12 | M13–18 | Rebuy (M1) | Crossover | Thinnest years |
|---|---|---|---|---|---|---|---|---|
| ungated | 4662 | 100% | 4141 | +2.91% | +1.49% | +1.6% | M13 | 2018: 117, 2017: 157 |
| `R>=44` (live) | 1814 | 39% | 1613 | +3.96% | +1.59% | +2.1% | M12 | 2018: 29, 2015: 45 |
| `R>=60` | 711 | 15% | 634 | +4.90% | +1.73% | +1.9% | M13 | 2018: 7, 2015: 13 |
| `R>=70` | 315 | 7% | 285 | +5.68% | +1.56% | +2.9% | M4 | 2018: 2, 2017: 5 |
| `R>=80` | 181 | 4% | 167 | +6.42% | +1.35% | +0.9% | M4 | 2017: 1, 2019: 2 |

## Results

```text
──────────────────────────────────────────────────────────────────────────────────────────────
R>=44 — bk50d_s12_v2.0, QullamaggieRanking >= 44  (the live configuration)
──────────────────────────────────────────────────────────────────────────────────────────────

Mean% — return earned during month M

 Year |     M1     M2     M3     M4     M5     M6     M7     M8     M9    M10    M11    M12    M13    M14    M15    M16    M17    M18 |    Sig
----------------------------------------------------------------------------------------------------------------------------------------------
 2015 |   -0.7   -2.8   -1.1   +2.8   -0.5   -6.5   -5.9   +2.6   +5.7   -0.1   -5.2   +5.7  +11.7  +11.7   +4.1   +8.4   +3.1   +5.2 |     45
 2016 |   +4.9   +4.7   +4.1   +4.8   +0.7   +4.0   +0.9   +4.9   +1.6   +2.7   -1.3   +0.9   +1.2   -0.2   +2.6   +1.8   +4.9   +3.9 |    188
 2017 |   +2.7   -0.4   +2.8   +4.1   +1.7   +2.2   +3.8   +4.8   +3.0   +2.1   +4.2   +0.8   +2.2   -1.9   +2.6   +3.4   -0.5   +9.6 |     45
 2018 |   -1.4   +6.6   +4.7   +0.1   +1.2   -3.7   -4.7   +2.0   +0.4   +4.7   +0.3   -2.8   +2.6   +1.0   -4.1   +2.2   -4.6   +1.1 |     29
 2019 |   -0.8   +0.1   -7.3   +4.8   +5.3   +2.9   +2.5   +5.9   +4.9  +10.9   +7.4   +2.9   +2.4  +13.6  +12.5   +3.4  +13.6   +2.8 |     82
 2020 |   +0.1   +6.1   +7.1   +1.0   +4.2  +17.5   +3.6   +3.5   +7.9   +1.7   +4.1   +1.2   -0.5   -1.0   +2.1   +0.9   +0.4   -3.1 |    664
 2021 |   +4.5   +4.7   +0.4   +8.4   +1.5   -5.8   +1.7   +6.4   +7.9   +4.9   -2.8   +5.9   +0.4   +8.6   +2.5   -4.5   +6.2   -5.7 |    133
 2022 |   -7.5  +10.0   -3.3   +4.3   +6.7   -2.8   +4.7   +2.1   +1.2   +2.5   +0.6   +4.8   +3.4   -3.2   +4.4   +5.2   -1.9   +1.0 |     86
 2023 |   +1.8   +1.5   +1.0   -0.4   +8.0   +2.0   +2.9   +2.3   +1.0   +7.1   +4.2   +1.0   +2.3   +2.4   +0.1   +1.1   +7.0   +5.0 |    192
 2024 |   +2.4   +3.9   +1.2   +0.9   +3.0   +3.0   +2.9   +6.9   +6.0   +5.4   +6.8   +6.4   -0.3   +2.0   +6.0   +1.2   +4.3   +3.7 |    139
 2025 |  +10.7   +9.4   +9.0   +6.6   +7.4   +6.0   +6.0   +6.5   +5.4   +4.9   +8.3   -0.4   +2.1   +1.7   -0.1   -2.6  -10.8   +4.7 |    211
----------------------------------------------------------------------------------------------------------------------------------------------
  All |   +2.1   +5.1   +3.9   +2.9   +4.3   +7.4   +3.0   +4.4   +5.3   +3.7   +3.4   +2.0   +1.0   +1.6   +2.7   +1.1   +2.9   +0.3 |   1814


──────────────────────────────────────────────────────────────────────────────────────────────
R>=60 — bk50d_s12_v2.0, QullamaggieRanking >= 60  (a stricter cut)
──────────────────────────────────────────────────────────────────────────────────────────────

Mean% — return earned during month M

 Year |     M1     M2     M3     M4     M5     M6     M7     M8     M9    M10    M11    M12    M13    M14    M15    M16    M17    M18 |    Sig
----------------------------------------------------------------------------------------------------------------------------------------------
 2015 |   +3.2  -11.0   +6.4   +1.7   -1.5   -4.0  -17.0   -0.6   +4.9   -6.3   -0.3   +7.5  +22.6  +14.2  +10.0  +23.0   +8.4  +19.6 |     13
 2016 |   +7.7   +5.1   +5.1   +6.7   +0.4   +2.1   +2.8   +3.8   -0.2   +2.6   -4.8   -0.2   -0.7   -1.2   +2.4   +1.7   +5.0   +2.7 |     78
 2017 |   +4.3   +1.8   +1.4   +5.3  +11.4   -0.5   -0.3   +4.1   +7.9   +4.5   +4.4   -1.2   -1.3   +3.4   +1.3   +5.8   -3.8  +29.3 |     13
 2018 |  -11.8   +5.5   -1.4   -4.0   +5.9   +9.0   -2.7   -0.4   -3.7   +2.6   -7.9   +2.2   +2.7   +4.7   -2.0   -6.2  -16.4   -1.8 |      7
 2019 |   +0.7   -1.7   -4.5   +3.0   +5.5   +6.7   +7.9   +5.3  +10.8   +5.0  +16.4  +11.3   +2.8   +6.7  +14.6   +3.6  +23.1   +0.6 |     18
 2020 |   -1.6   +7.3   +7.5   -0.4   +3.8  +24.0   +4.9   +4.7  +10.3   +1.3   +5.6   +3.1   -0.9   -1.6   +2.5   +1.8   +1.1   -4.2 |    283
 2021 |   +7.9  +12.3   -1.4   +8.2   +7.6   -5.3   +0.0   +6.4  +12.3   +3.9   -5.3   +9.7   +4.4   +9.1   +1.7   -1.6   +7.2   -8.5 |     49
 2022 |   -9.7  +12.9   -2.7   +6.0  +10.4   -5.9   +1.6   +2.7   -6.6   +6.9   +4.2   +5.7   +3.3   -5.0   +7.0   +7.5   -5.6   +0.1 |     36
 2023 |   +2.3   +5.8   +1.0   -2.3  +10.2   +4.7   +4.2   +6.6   -0.2   +8.4   +7.3   +0.2   +2.3   +2.7   +0.9   +2.1   +5.8   +3.1 |     74
 2024 |   +4.3   +3.1   -0.5   +4.1   +5.2   +0.6   +4.0   +9.1   +7.6   +4.0   +6.4   +9.0   -3.9   +2.9  +10.4   +2.3   +9.8   +5.2 |     62
 2025 |   +8.7   +9.4   +9.4   +7.2  +15.6   +5.6   +5.2   +8.9  +12.6   +5.3   +1.9   +1.9   +5.0   +3.5   -2.2   -2.6      ·      · |     78
----------------------------------------------------------------------------------------------------------------------------------------------
  All |   +1.9   +6.7   +4.4   +2.5   +6.2  +10.5   +3.6   +5.5   +7.1   +3.3   +3.5   +3.7   +0.8   +0.9   +3.4   +2.2   +3.4   -0.3 |    711


──────────────────────────────────────────────────────────────────────────────────────────────
R>=70 — bk50d_s12_v2.0, QullamaggieRanking >= 70  (a stricter cut)
──────────────────────────────────────────────────────────────────────────────────────────────

Mean% — return earned during month M

 Year |     M1     M2     M3     M4     M5     M6     M7     M8     M9    M10    M11    M12    M13    M14    M15    M16    M17    M18 |    Sig
----------------------------------------------------------------------------------------------------------------------------------------------
 2015 |   +7.7   -9.2   +8.0   +1.1   +4.0   -5.1  -12.1   -6.0   +1.8  -13.3   +2.8   +5.7   +8.3  +17.5   +7.4  +20.3  +15.5  +20.4 |      7
 2016 |  +17.2   +5.9   +7.5   +4.8   +2.6   +1.4   +4.5   +8.8   -1.2   +1.9   -4.7   -0.8   -2.1   -4.3   -2.9   +2.7   +4.8   +3.4 |     31
 2017 |   +3.2  +10.8   -0.6   +3.7   +5.8   -1.2  -10.3  +14.1   +5.0   -3.1   -0.9   -5.7  +15.2   +2.1   +4.6   +4.0   +2.5   +0.6 |      5
 2018 |      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      · |      2
 2019 |   +7.3   +3.7  -14.2   +6.0  +11.6   +5.5  +26.3   -5.5  +12.2   +3.2  +14.9   +2.2   -8.8   +6.0  +17.5   -0.2   +6.2   +0.6 |      5
 2020 |   -1.8   +6.4   +9.1   -3.8   +2.6  +30.5   +6.3   +6.0  +11.6   +0.8   +6.1   +4.9   +0.4   -2.7   +3.0   +4.5   +0.9   -4.5 |    129
 2021 |  +12.2  +21.8   -2.9  +11.6  +14.6   -4.1   +1.8   +7.5  +24.1   +4.2   -8.9  +11.1   +4.9  +13.8   -1.3   -1.3   +9.4  -11.9 |     24
 2022 |  -14.7  +11.6   -1.3   +7.3  +22.5   -4.6   +3.0   +1.5   -9.9  +19.8   +8.2   +3.4   +3.9   -7.6  +10.6   +7.8   -6.3   -6.0 |     16
 2023 |   -1.0   +6.8   +8.4   -5.7   +8.8   +6.5   +6.2  +12.0   +0.6   +9.0   +7.2   -5.1   +2.1   +4.6   -0.1   +2.7   +7.2   +4.2 |     33
 2024 |   +5.2   +2.7   -2.1   +6.9   +6.2   -0.5   +7.9  +15.7   +5.1   +6.8   +9.7   +4.9   -8.5   +4.5  +11.5   -0.9   +7.0   +5.2 |     33
 2025 |  +10.5   +5.7   +9.5   +8.6   +6.5   +2.9   +5.1  +10.6   +6.8   +7.0   +2.2   +5.2   +6.4   -2.4   -0.9   -6.9      ·      · |     30
----------------------------------------------------------------------------------------------------------------------------------------------
  All |   +2.9   +7.1   +5.8   +1.3   +6.1  +13.0   +5.3   +7.9   +7.5   +3.9   +4.1   +3.5   +0.6   +0.4   +3.2   +3.1   +3.5   -1.4 |    315


──────────────────────────────────────────────────────────────────────────────────────────────
R>=80 — bk50d_s12_v2.0, QullamaggieRanking >= 80  (a stricter cut)
──────────────────────────────────────────────────────────────────────────────────────────────

Mean% — return earned during month M

 Year |     M1     M2     M3     M4     M5     M6     M7     M8     M9    M10    M11    M12    M13    M14    M15    M16    M17    M18 |    Sig
----------------------------------------------------------------------------------------------------------------------------------------------
 2015 |      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      · |      4
 2016 |  +15.4   +6.9   +7.7   +8.9   +2.9   +1.3   +3.4  +11.0   -2.1   +2.3   -5.3   +0.1   -4.5   -3.8   -5.3   +3.4   +6.7   +2.9 |     17
 2017 |      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      · |      1
 2018 |      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      · |      0
 2019 |      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      ·      · |      2
 2020 |   -5.2   +5.1  +10.9   -6.1   +1.0  +37.3   +6.7   +8.6  +14.8   -0.5   +8.1   +7.1   +0.0   -4.8   +3.6   +7.3   +2.0   -4.0 |     86
 2021 |  +15.7  +15.2   +4.3  +11.8  +13.8   -1.4  +18.0  +15.6  +21.4   -0.5   -8.3  +13.0   +4.0   +4.4   -2.2   -2.8   +0.1   +3.2 |     10
 2022 |  -23.5  +23.3   +3.1   -2.9  +15.4   -3.1   +3.6   +6.0   -4.8  +13.1   -3.2   -0.5   +3.9  -11.2   +7.2   +4.6   -9.0   -2.3 |      9
 2023 |   -0.5  +12.9  +11.7   -6.8   +3.4   +1.4   -2.1   +4.7   +0.1  +13.5  +12.5   -8.5   -0.4   +6.9   -1.8   +2.1   +7.3   +9.0 |     19
 2024 |   +7.8   -0.6   -1.3   +3.2   +5.8   +1.0   +9.0  +13.8   +5.6   +5.4  +12.6   +7.9   -8.7   +2.1   +3.5   +2.9   +5.3   +6.0 |     19
 2025 |  +15.2   +2.2  +12.9  +10.3  +12.3   +7.4   +3.7  +17.4   +7.3  +13.3   +4.3  +10.6   -6.6   +2.6   -1.9      ·      ·      · |     14
----------------------------------------------------------------------------------------------------------------------------------------------
  All |   +0.9   +6.7   +8.1   -0.9   +4.6  +18.4   +6.2   +9.5   +9.0   +3.6   +5.6   +5.3   -0.6   -1.8   +1.9   +5.0   +3.5   +0.1 |    181


──────────────────────────────────────────────────────────────────────────────────────────────
UNGATED — bk50d_s12_v2.0, every signal the filters emit  (no ranking gate)
──────────────────────────────────────────────────────────────────────────────────────────────

Mean% — return earned during month M

 Year |     M1     M2     M3     M4     M5     M6     M7     M8     M9    M10    M11    M12    M13    M14    M15    M16    M17    M18 |    Sig
----------------------------------------------------------------------------------------------------------------------------------------------
 2015 |   -2.6   -3.3   -0.2   +2.3   -0.1   -2.3   -3.2   +3.9   +2.0   -1.7   -3.9   +5.6   +7.0   +5.8   +1.9   +3.4   +4.2   +3.9 |    177
 2016 |   +2.5   +2.3   +3.5   +3.4   +0.2   +2.7   +1.4   +4.8   +1.8   +2.6   +0.3   +0.4   +2.2   +0.8   +2.4   +1.6   +3.1   +3.4 |    457
 2017 |   +2.0   +1.6   +1.1   +3.8   +2.0   +3.8   +3.4   +2.5   +3.9   +0.7   +3.0   +1.9   -0.3   +0.4   +0.5   +2.1   +1.3   +3.0 |    157
 2018 |   -0.7   +2.7   +2.7   -1.4   -0.6   -1.6   -4.2   +3.7   +1.5   +3.7   +0.9   -4.3   +2.5   +0.2   +0.2   -0.3   +0.7   +0.7 |    117
 2019 |   +1.0   +1.5   -5.2   -0.0   +3.0   +1.9   +4.8   +3.7   +4.1   +6.6   +2.0   +4.3   -3.0  +12.1  +10.6   +7.8   +6.8   +5.0 |    318
 2020 |   +1.0   +4.8   +7.2   +2.4   +4.1  +13.0   +2.9   +2.9   +5.7   +1.7   +3.1   +0.7   +0.4   -1.0   +1.6   +0.6   -0.2   -2.7 |   1364
 2021 |   +3.8   +2.3   +0.5   +3.8   -0.0   -4.0   +0.2   +3.6   +5.9   +2.5   -1.6   +3.6   -0.7   +2.2   +1.0   -4.0   +4.9   -2.2 |    382
 2022 |   -6.3   +9.7   -3.8   +2.2   +3.2   -2.6   +6.7   +2.6   -0.5   +0.5   +0.0   +5.0   +3.6   -1.4   +3.7   +4.3   -1.3   +2.3 |    224
 2023 |   +2.0   +0.3   +0.5   +0.4   +6.1   +2.0   +2.1   +2.1   +1.1   +5.2   +3.4   +3.0   +0.8   +2.1   +0.4   +0.9   +3.8   +2.8 |    503
 2024 |   +1.0   +3.0   +1.2   +0.1   +1.5   +1.0   +2.2   +4.7   +3.1   +3.2   +3.5   +5.5   +0.1   +2.1   +5.0   +2.6   +3.4   +2.6 |    408
 2025 |   +6.1   +4.5   +5.7   +5.4   +5.3   +4.6   +5.2   +6.3   +3.2   +3.1   +7.7   +1.3   +1.5   +0.6   +0.4   -0.0   -1.2   +2.7 |    555
----------------------------------------------------------------------------------------------------------------------------------------------
  All |   +1.6   +3.2   +2.9   +2.3   +3.1   +4.6   +2.6   +3.7   +3.6   +2.7   +2.4   +2.2   +0.8   +1.5   +2.4   +1.4   +2.2   +0.7 |   4662
```

## Reading

- Cells are **marginal**: month M is the move from month M-1 to month M, not the run from entry. Chaining a row does not give a buy-and-hold return — each cell is an equal-weighted average over whichever signals had both marks, and that set shrinks as M grows — see `N@M18` in the gate comparison for how much of each sample survives to the far columns.
- **The row is the signal's birth year, the column is its age.** Calendar time drifts rightward along a row: a 2015-vintage M18 cell describes what those positions did in 2016-2017, not what the 2015 market did. Only the left-hand columns sit mostly inside the row's own year.
- **Every block comes from one signal generation**, so the treatments differ only by the threshold applied to the score each signal already carries — same cooldown chain, same entries, same marks. Of 4662 signals, R>=44 keeps 1814 (39%), R>=60 keeps 711 (15%), R>=70 keeps 315 (7%), R>=80 keeps 181 (4%). The gated sets are nested subsets of the ungated one, so a column where two blocks agree is one the gate is not acting on.
- **A Mean% cell drawn from fewer than 5 signals prints `·`**, the floor the cohort studies already use. At the tighter gates a thin year falls to one or two names, where an average is that name's story and reads as a finding. The row's `Sig` column still gives the year's true count, so a `·` beside a non-zero `Sig` means the cell was withheld rather than empty. **Read the gate comparison before the grids** — a rising Mean% next to a collapsing sample is selectivity eating its own evidence, not an improving edge.
- Month 12 lands within a day or two of the 366-day exit the live algorithm uses, so months 13-18 are the part of the curve the current exit gives up.
- **The last rows are truncated by the data, not by the strategy.** Month 18 is only reachable for entries roughly 18 months before the final bar; later vintages fall out of the right-hand columns first. 499 signals stop short for that reason. A rising tail in a short row is a smaller, earlier cohort, not a better one.
- **The `All` row is pooled, not an average of the year rows.** 2020 alone contributes 1364 of 4662 signals (29%), so it dominates every `All` cell. Compare year rows with each other, not with `All`.
- **The universe is survivor-only, and this is the caveat that matters most.** Every symbol in `turtle.daily_bars` still trades today: companies delisted, acquired or wound up during the study window are absent from the price data entirely and never generate a signal. On top of that, the `market_cap >= 1.5B` universe filter reads the *current* `turtle.company` snapshot, so a 2015 signal is admitted only if that company is large today. Both push the same way — every number here is conditioned on survival and on subsequent growth, and the early years are the most affected. This is a property of the data layer that every committed study shares, not of this decomposition, but it means the levels are optimistic even where the shape across months is informative.
- Only 22 signals (0.5%) end early for a reason other than the data cutoff — trailing halted or zero-volume stretches, which `qm.load_bars` drops. That number is small because real delistings cannot appear, not because attrition was low.
- 2025 is reported descriptively. This study fits nothing and selects nothing, so it does not spend the ranking lab's frozen holdout slice (docs/research/prompts.md, "Never touch entries on or after 2025-01-01").
