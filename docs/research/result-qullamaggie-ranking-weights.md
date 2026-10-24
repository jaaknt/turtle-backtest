# Ranking Weights — recalibrated 40/35/25 bands vs the two weightings they replaced

Period 2021-01-01 .. 2026-06-26, $30,000 initial equity, 4% positions, 366d calendar hold, next-day-open entries.

`production` is the shipped QullamaggieRanking — 40/35/25 with bands re-derived on 2026-08-07 from the bk50d_s12_v2.0 cohort tables, each dimension's floor anchored outside its entry filter so no qualifying cohort scores 0. `prev-bands` is the same 40/35/25 split with the superseded bands it replaces (fitted to an s15_v1.3_roc100 run; ADR < 4.5% scored 0, which was 49.6% of the s12 pool). `legacy` is the six-dimension weighting dropped on 2026-07-29 (SMA50 50, price 13, ADR 12, compression 12, ROC252 10, RSI 3). Ties are broken at random over 20 redraws; `null` is 30 random subsets of the same size.

## s20 (%abv_SMA50 > 20%) — 839 fillable signals (839 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  >=44 kept%
-------------------------------------------------------
legacy        45   56   63   69   97   63.5      100.0%
prev-bands    31   39   56   66  100   54.7       62.8%
production    34   44   54   65  100   56.7       78.9%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +57.91  0.64   -25.89    2.467    119 |      +37.50  6.60   30/30
  35% prev-bands    +54.51  0.28   -25.45    2.352    117 |      +40.31  5.83   30/30
  35% production    +58.80  2.74   -27.08    2.349    118 |      +34.56  5.97   30/30
  25% legacy        +53.84  0.67   -26.28    2.436    109 |      +36.45  6.22   30/30
  25% prev-bands    +55.82  2.76   -22.89    2.407    110 |      +38.00  6.66   30/30
  25% production    +58.56  2.65   -23.29    2.378    109 |      +36.72  7.03   30/30
  15% legacy        +55.34  3.58   -30.96    2.503     98 |      +32.87  5.34   30/30
  15% prev-bands    +58.38  0.78   -32.47    2.577     94 |      +33.49  7.12   30/30
  15% production    +50.65  1.71   -30.61    2.182     97 |      +34.20  6.72   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +42.78 (sd  0.1)     +81.65 (sd  2.3)
  35% prev-bands      +33.12 (sd  0.0)     +84.85 (sd  3.8)
  35% production      +33.21 (sd  2.7)     +81.32 (sd  2.2)
  25% legacy          +45.01 (sd  1.0)     +79.97 (sd  2.4)
  25% prev-bands      +35.93 (sd  0.6)     +89.90 (sd  4.0)
  25% production      +39.16 (sd  1.7)     +81.92 (sd  7.8)
  15% legacy          +39.12 (sd  0.0)     +63.90 (sd  7.6)
  15% prev-bands      +34.10 (sd  1.3)     +86.76 (sd  0.7)
  15% production      +43.89 (sd  1.9)     +68.53 (sd  1.8)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0    839 100.0%   +42.34   -27.12    1.874    145 |           —     —     n/a
legacy         20    839 100.0%   +42.34   -27.12    1.874    145 |           —     —     n/a
legacy         30    839 100.0%   +42.34   -27.12    1.874    145 |           —     —     n/a
legacy         40    839 100.0%   +42.34   -27.12    1.874    145 |           —     —     n/a
legacy         42    839 100.0%   +42.34   -27.12    1.874    145 |           —     —     n/a
legacy         44    839 100.0%   +42.34   -27.12    1.874    145 |           —     —     n/a
legacy         46    835  99.5%   +42.34   -27.12    1.874    145 |      +42.71  1.00    7/30
legacy         50    812  96.8%   +42.90   -27.12    1.885    144 |      +44.02  2.56   10/30
legacy         60    521  62.1%   +44.43   -32.31    1.822    131 |      +40.25  5.58   20/30
prev-bands      0    839 100.0%   +43.19   -27.12    1.890    145 |           —     —     n/a
prev-bands     20    839 100.0%   +43.19   -27.12    1.890    145 |           —     —     n/a
prev-bands     30    839 100.0%   +43.19   -27.12    1.890    145 |           —     —     n/a
prev-bands     40    604  72.0%   +56.24   -30.23    2.194    135 |      +41.77  6.05   30/30
prev-bands     42    587  70.0%   +55.89   -30.23    2.179    135 |      +43.13  5.74   30/30
prev-bands     44    527  62.8%   +51.33   -31.54    1.993    133 |      +37.95  7.57   28/30
prev-bands     46    517  61.6%   +51.33   -31.54    1.993    133 |      +39.34  6.34   30/30
prev-bands     50    449  53.5%   +53.80   -30.35    2.061    132 |      +39.33  5.74   30/30
prev-bands     60    400  47.7%   +55.28   -31.83    2.153    133 |      +37.29  6.82   30/30
production      0    839 100.0%   +43.06   -27.12    1.880    145 |           —     —     n/a
production     20    839 100.0%   +43.06   -27.12    1.880    145 |           —     —     n/a
production     30    839 100.0%   +43.06   -27.12    1.880    145 |           —     —     n/a
production     40    735  87.6%   +49.96   -29.95    2.041    139 |      +45.49  5.88   23/30
production     42    704  83.9%   +50.47   -29.94    2.057    139 |      +48.04  5.34   19/30
production     44    662  78.9%   +49.75   -29.94    2.025    139 |      +44.80  6.01   24/30
production     46    607  72.3%   +56.53   -30.84    2.221    137 |      +42.25  6.46   30/30
production     50    531  63.3%   +49.55   -32.17    1.974    133 |      +40.81  6.99   24/30
production     60    323  38.5%   +55.07   -28.47    2.219    122 |      +38.29  6.21   30/30
```

## s16 (%abv_SMA50 > 16%) — 1440 fillable signals (1440 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  >=44 kept%
-------------------------------------------------------
legacy        17   37   52   64   97   50.8       61.6%
prev-bands    12   24   39   60  100   42.8       41.6%
production    24   36   46   57  100   48.2       54.6%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +43.13  1.55   -31.48    1.799    132 |      +35.02  5.57   27/30
  35% prev-bands    +54.83  0.61   -32.83    2.126    135 |      +32.90  5.39   30/30
  35% production    +53.59  1.75   -31.58    2.098    136 |      +36.17  7.03   29/30
  25% legacy        +53.40  0.71   -28.00    2.261    127 |      +35.98  4.90   30/30
  25% prev-bands    +55.60  3.29   -29.83    2.198    131 |      +35.76  7.11   30/30
  25% production    +52.55  1.09   -28.61    2.147    126 |      +34.00  6.25   30/30
  15% legacy        +52.57  1.06   -26.51    2.418    109 |      +32.61  5.43   30/30
  15% prev-bands    +55.45  2.48   -23.98    2.393    113 |      +35.18  5.87   30/30
  15% production    +60.39  2.37   -24.39    2.417    112 |      +32.96  6.78   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +27.75 (sd  1.6)     +52.64 (sd  4.8)
  35% prev-bands      +32.47 (sd  0.4)     +63.02 (sd  0.0)
  35% production      +33.44 (sd  1.6)     +64.79 (sd  6.5)
  25% legacy          +32.02 (sd  0.7)     +68.01 (sd  3.0)
  25% prev-bands      +34.54 (sd  2.6)     +76.27 (sd  3.3)
  25% production      +31.50 (sd  0.7)     +77.81 (sd  1.9)
  15% legacy          +44.71 (sd  1.1)     +67.56 (sd  1.9)
  15% prev-bands      +36.31 (sd  1.9)     +90.18 (sd  2.1)
  15% production      +35.45 (sd  1.4)     +66.34 (sd  6.1)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   1440 100.0%   +35.23   -27.56    1.629    145 |           —     —     n/a
legacy         20   1426  99.0%   +34.90   -27.56    1.618    145 |      +36.22  1.27    2/30
legacy         30   1260  87.5%   +38.76   -26.79    1.728    144 |      +36.90  2.24   26/30
legacy         40   1012  70.3%   +40.08   -26.59    1.777    144 |      +34.64  3.85   27/30
legacy         42    952  66.1%   +40.93   -26.59    1.817    146 |      +35.71  3.67   28/30
legacy         44    887  61.6%   +44.27   -27.41    1.908    146 |      +34.44  5.13   30/30
legacy         46    840  58.3%   +40.91   -26.55    1.846    146 |      +34.04  6.36   26/30
legacy         50    785  54.5%   +44.84   -27.91    1.957    146 |      +35.45  4.90   30/30
legacy         60    498  34.6%   +42.85   -31.44    1.803    132 |      +33.36  5.93   28/30
prev-bands      0   1440 100.0%   +35.73   -27.56    1.654    144 |           —     —     n/a
prev-bands     20   1270  88.2%   +38.36   -25.81    1.720    144 |      +36.18  2.88   23/30
prev-bands     30   1020  70.8%   +39.16   -26.61    1.737    145 |      +33.60  3.34   30/30
prev-bands     40    718  49.9%   +41.11   -27.15    1.791    144 |      +35.48  4.73   27/30
prev-bands     42    651  45.2%   +41.35   -28.41    1.764    143 |      +34.66  6.86   24/30
prev-bands     44    599  41.6%   +47.41   -30.42    1.934    141 |      +36.67  6.73   29/30
prev-bands     46    590  41.0%   +47.41   -30.42    1.934    141 |      +32.92  5.77   30/30
prev-bands     50    487  33.8%   +57.03   -32.83    2.164    136 |      +33.88  6.76   30/30
prev-bands     60    403  28.0%   +61.70   -33.93    2.261    133 |      +35.97  7.03   30/30
production      0   1440 100.0%   +35.55   -26.20    1.644    144 |           —     —     n/a
production     20   1440 100.0%   +35.55   -26.20    1.644    144 |           —     —     n/a
production     30   1299  90.2%   +38.16   -24.24    1.744    142 |      +36.13  3.10   22/30
production     40    920  63.9%   +43.64   -28.13    1.876    144 |      +35.68  6.12   29/30
production     42    867  60.2%   +43.82   -27.39    1.883    144 |      +34.29  6.51   28/30
production     44    786  54.6%   +44.86   -27.40    1.920    145 |      +37.09  4.84   28/30
production     46    720  50.0%   +45.41   -27.64    1.922    144 |      +34.21  5.45   30/30
production     50    575  39.9%   +48.25   -31.31    1.967    139 |      +35.38  6.17   29/30
production     60    321  22.3%   +54.54   -26.72    2.222    122 |      +34.80  5.99   30/30
```

## s12 (%abv_SMA50 > 12%) — 2307 fillable signals (2307 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  >=44 kept%
-------------------------------------------------------
legacy        17   32   41   57   97   45.2       44.5%
prev-bands    12   17   30   47  100   36.2       30.0%
production    20   29   37   50  100   41.2       35.9%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +46.24  0.93   -28.39    2.002    145 |      +34.72  6.92   29/30
  35% prev-bands    +45.96  0.37   -28.59    1.940    144 |      +34.81  5.32   29/30
  35% production    +49.09  0.94   -28.56    2.041    145 |      +33.40  5.97   30/30
  25% legacy        +51.53  2.36   -31.90    2.048    135 |      +36.94  7.34   29/30
  25% prev-bands    +49.04  1.16   -27.23    1.999    140 |      +35.91  6.98   29/30
  25% production    +48.85  1.67   -31.39    2.006    142 |      +36.25  6.97   28/30
  15% legacy        +52.31  2.02   -26.39    2.271    125 |      +32.95  5.62   30/30
  15% prev-bands    +60.20  3.07   -31.33    2.323    130 |      +34.24  6.51   30/30
  15% production    +54.94  1.15   -29.01    2.212    126 |      +33.28  5.33   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +34.24 (sd  1.2)     +54.32 (sd  3.0)
  35% prev-bands      +40.31 (sd  0.0)     +51.12 (sd  0.3)
  35% production      +37.78 (sd  0.3)     +49.05 (sd  1.3)
  25% legacy          +33.24 (sd  0.3)     +55.63 (sd  1.2)
  25% prev-bands      +35.21 (sd  0.3)     +63.54 (sd  1.0)
  25% production      +37.22 (sd  0.1)     +57.59 (sd  0.3)
  15% legacy          +34.31 (sd  1.7)     +66.82 (sd  1.8)
  15% prev-bands      +41.43 (sd  1.9)     +74.86 (sd  1.9)
  15% production      +32.44 (sd  1.6)     +78.27 (sd  1.4)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   2307 100.0%   +39.84   -22.89    2.017    144 |           —     —     n/a
legacy         20   2295  99.5%   +39.28   -22.89    1.997    143 |      +39.65  0.47    6/30
legacy         30   1986  86.1%   +42.34   -22.89    2.102    144 |      +36.01  3.84   30/30
legacy         40   1270  55.0%   +37.05   -25.55    1.739    145 |      +32.80  4.96   23/30
legacy         42   1144  49.6%   +37.36   -25.56    1.716    145 |      +30.95  5.91   27/30
legacy         44   1026  44.5%   +41.50   -25.30    1.851    145 |      +33.73  5.67   26/30
legacy         46    933  40.4%   +42.81   -28.49    1.900    146 |      +33.62  5.86   27/30
legacy         50    811  35.2%   +45.57   -28.63    1.973    145 |      +34.06  5.94   28/30
legacy         60    497  21.5%   +41.81   -32.69    1.766    132 |      +35.72  6.72   25/30
prev-bands      0   2307 100.0%   +35.14   -22.89    1.840    145 |           —     —     n/a
prev-bands     20   1714  74.3%   +36.56   -24.49    1.800    144 |      +33.00  4.79   21/30
prev-bands     30   1234  53.5%   +36.62   -25.34    1.700    143 |      +29.92  4.95   28/30
prev-bands     40    866  37.5%   +42.32   -28.18    1.864    143 |      +33.28  5.61   27/30
prev-bands     42    749  32.5%   +48.78   -28.85    2.043    144 |      +35.35  4.90   30/30
prev-bands     44    692  30.0%   +48.50   -29.32    2.028    143 |      +36.14  5.79   29/30
prev-bands     46    648  28.1%   +48.25   -27.23    1.989    142 |      +34.08  6.66   29/30
prev-bands     50    551  23.9%   +55.00   -27.74    2.145    138 |      +35.76  6.83   30/30
prev-bands     60    415  18.0%   +61.93   -31.92    2.277    135 |      +33.95  6.59   30/30
production      0   2307 100.0%   +34.54   -22.08    1.810    145 |           —     —     n/a
production     20   2307 100.0%   +34.54   -22.08    1.810    145 |           —     —     n/a
production     30   1701  73.7%   +35.93   -26.53    1.755    144 |      +35.21  4.70   12/30
production     40   1052  45.6%   +39.09   -28.49    1.753    143 |      +30.67  4.61   29/30
production     42    915  39.7%   +46.35   -28.52    1.962    145 |      +33.55  4.91   30/30
production     44    829  35.9%   +48.15   -28.53    2.014    145 |      +33.14  7.09   30/30
production     46    742  32.2%   +50.45   -28.61    2.089    142 |      +34.17  5.21   30/30
production     50    586  25.4%   +48.20   -30.91    1.985    143 |      +34.65  7.49   29/30
production     60    320  13.9%   +55.18   -27.58    2.232    124 |      +31.95  5.85   30/30
```
