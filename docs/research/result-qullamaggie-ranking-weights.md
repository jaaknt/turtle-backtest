# Ranking Weights — recalibrated 40/35/25 bands vs the two weightings they replaced

Period 2021-01-01 .. 2026-06-26, $30,000 initial equity, 4% positions, 366d calendar hold, next-day-open entries.

`production` is the shipped QullamaggieRanking — 40/35/25 with bands re-derived on 2026-08-07 from the bk50d_s12_v2.0 cohort tables, each dimension's floor anchored outside its entry filter so no qualifying cohort scores 0. `prev-bands` is the same 40/35/25 split with the superseded bands it replaces (fitted to an s15_v1.3_roc100 run; ADR < 4.5% scored 0, which was 49.6% of the s12 pool). `legacy` is the six-dimension weighting dropped on 2026-07-29 (SMA50 50, price 13, ADR 12, compression 12, ROC252 10, RSI 3). Ties are broken at random over 20 redraws; `null` is 30 random subsets of the same size.

## s20 (%abv_SMA50 > 20%) — 890 fillable signals (890 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  >=44 kept%
-------------------------------------------------------
legacy        45   56   63   70   97   63.9      100.0%
prev-bands    31   39   58   66  100   55.4       64.2%
production    34   44   54   65  100   57.4       80.1%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +55.94  2.33   -26.87    2.373    121 |      +36.44  7.31   30/30
  35% prev-bands    +51.11  1.43   -25.93    2.203    120 |      +37.10  7.48   29/30
  35% production    +56.25  3.02   -28.29    2.268    121 |      +37.37  5.82   30/30
  25% legacy        +49.95  1.69   -27.43    2.279    110 |      +36.83  5.32   30/30
  25% prev-bands    +52.43  2.25   -22.85    2.257    110 |      +37.33  5.55   30/30
  25% production    +55.17  1.67   -22.43    2.213    110 |      +35.23  6.54   30/30
  15% legacy        +55.11  0.00   -30.54    2.543    101 |      +32.48  5.97   30/30
  15% prev-bands    +57.15  1.56   -33.32    2.438     94 |      +34.10  5.08   30/30
  15% production    +49.35  2.51   -31.89    2.142     96 |      +32.68  5.67   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +46.95 (sd  1.0)     +76.37 (sd  0.1)
  35% prev-bands      +32.29 (sd  1.5)     +89.05 (sd  1.3)
  35% production      +40.40 (sd  1.0)     +83.91 (sd  2.7)
  25% legacy          +48.35 (sd  2.6)     +73.17 (sd  2.7)
  25% prev-bands      +36.69 (sd  1.1)     +85.95 (sd  3.0)
  25% production      +40.44 (sd  0.3)     +60.27 (sd  1.4)
  15% legacy          +43.15 (sd  0.0)     +66.60 (sd  0.0)
  15% prev-bands      +34.32 (sd  0.5)     +83.44 (sd  2.1)
  15% production      +43.12 (sd  4.8)     +70.04 (sd  1.7)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0    890 100.0%   +36.00   -27.27    1.597    145 |           —     —     n/a
legacy         20    890 100.0%   +36.00   -27.27    1.597    145 |           —     —     n/a
legacy         30    890 100.0%   +36.00   -27.27    1.597    145 |           —     —     n/a
legacy         40    890 100.0%   +36.00   -27.27    1.597    145 |           —     —     n/a
legacy         42    890 100.0%   +36.00   -27.27    1.597    145 |           —     —     n/a
legacy         44    890 100.0%   +36.00   -27.27    1.597    145 |           —     —     n/a
legacy         46    886  99.6%   +36.00   -27.27    1.597    145 |      +36.46  1.15    6/30
legacy         50    863  97.0%   +36.93   -27.27    1.628    145 |      +39.21  2.83    6/30
legacy         60    564  63.4%   +40.15   -29.89    1.661    137 |      +38.16  6.08   17/30
prev-bands      0    890 100.0%   +35.99   -27.47    1.603    145 |           —     —     n/a
prev-bands     20    890 100.0%   +35.99   -27.47    1.603    145 |           —     —     n/a
prev-bands     30    890 100.0%   +35.99   -27.47    1.603    145 |           —     —     n/a
prev-bands     40    653  73.4%   +45.53   -27.47    1.854    143 |      +41.95  5.93   24/30
prev-bands     42    636  71.5%   +45.62   -27.47    1.860    143 |      +40.94  7.74   21/30
prev-bands     44    571  64.2%   +46.72   -31.02    1.856    141 |      +39.61  6.63   23/30
prev-bands     46    561  63.0%   +46.69   -31.02    1.855    140 |      +38.48  6.34   26/30
prev-bands     50    487  54.7%   +56.08   -32.19    2.087    138 |      +36.19  6.32   30/30
prev-bands     60    436  49.0%   +52.46   -31.93    1.971    131 |      +34.85  5.91   30/30
production      0    890 100.0%   +35.92   -27.47    1.597    145 |           —     —     n/a
production     20    890 100.0%   +35.92   -27.47    1.597    145 |           —     —     n/a
production     30    890 100.0%   +35.92   -27.47    1.597    145 |           —     —     n/a
production     40    787  88.4%   +36.81   -27.47    1.619    145 |      +39.99  3.84    6/30
production     42    755  84.8%   +36.65   -27.47    1.610    144 |      +40.65  4.34    7/30
production     44    713  80.1%   +37.41   -27.47    1.637    142 |      +41.48  4.29    6/30
production     46    657  73.8%   +36.20   -27.47    1.590    140 |      +38.66  6.00   10/30
production     50    574  64.5%   +42.28   -30.70    1.695    136 |      +39.32  5.74   23/30
production     60    353  39.7%   +50.83   -29.50    2.048    127 |      +38.17  5.99   29/30
```

## s16 (%abv_SMA50 > 16%) — 1518 fillable signals (1518 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  >=44 kept%
-------------------------------------------------------
legacy        17   37   52   64   97   51.1       61.7%
prev-bands    12   24   40   60  100   43.3       42.2%
production    24   36   46   57  100   48.7       55.5%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +44.53  0.93   -31.34    1.804    136 |      +35.13  5.45   29/30
  35% prev-bands    +48.38  0.82   -30.38    1.915    143 |      +35.62  6.21   30/30
  35% production    +46.86  2.68   -30.66    1.838    139 |      +33.40  6.22   30/30
  25% legacy        +50.93  1.22   -28.05    2.158    129 |      +32.59  5.97   29/30
  25% prev-bands    +46.37  1.61   -28.91    1.927    133 |      +35.84  6.30   28/30
  25% production    +47.75  0.90   -29.38    1.998    130 |      +35.29  5.92   30/30
  15% legacy        +51.98  0.91   -27.12    2.374    112 |      +33.45  6.19   30/30
  15% prev-bands    +54.51  1.60   -24.01    2.321    115 |      +33.83  6.96   30/30
  15% production    +54.73  1.59   -24.30    2.180    112 |      +34.88  6.37   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +31.56 (sd  0.6)     +49.80 (sd  4.7)
  35% prev-bands      +38.81 (sd  1.7)     +66.99 (sd  1.5)
  35% production      +36.97 (sd  1.5)     +68.02 (sd  4.6)
  25% legacy          +39.55 (sd  0.8)     +65.66 (sd  2.1)
  25% prev-bands      +36.57 (sd  3.4)     +77.07 (sd  4.1)
  25% production      +31.88 (sd  1.4)     +74.42 (sd  1.6)
  15% legacy          +48.31 (sd  0.0)     +66.32 (sd  0.3)
  15% prev-bands      +36.28 (sd  3.3)     +83.33 (sd  4.2)
  15% production      +39.16 (sd  0.0)     +61.20 (sd  2.1)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   1518 100.0%   +40.84   -24.65    1.815    144 |           —     —     n/a
legacy         20   1504  99.1%   +40.40   -24.65    1.801    144 |      +39.85  1.63   12/30
legacy         30   1331  87.7%   +40.66   -24.18    1.803    143 |      +37.96  3.64   21/30
legacy         40   1067  70.3%   +40.10   -29.34    1.771    144 |      +36.75  4.52   24/30
legacy         42   1004  66.1%   +42.11   -29.26    1.826    144 |      +36.29  4.64   27/30
legacy         44    937  61.7%   +44.43   -27.32    1.917    146 |      +35.22  5.47   29/30
legacy         46    885  58.3%   +46.09   -26.30    1.975    147 |      +35.03  5.38   29/30
legacy         50    827  54.5%   +44.10   -27.99    1.902    145 |      +35.45  4.67   30/30
legacy         60    536  35.3%   +44.84   -31.08    1.812    136 |      +35.04  5.15   28/30
prev-bands      0   1518 100.0%   +41.07   -24.65    1.826    144 |           —     —     n/a
prev-bands     20   1345  88.6%   +40.53   -24.99    1.790    144 |      +37.64  2.55   26/30
prev-bands     30   1084  71.4%   +36.59   -26.61    1.631    145 |      +36.70  5.02   16/30
prev-bands     40    767  50.5%   +43.40   -29.67    1.837    144 |      +36.41  6.71   24/30
prev-bands     42    696  45.8%   +45.18   -29.35    1.893    144 |      +36.02  6.70   28/30
prev-bands     44    641  42.2%   +44.90   -30.72    1.873    145 |      +34.45  4.78   30/30
prev-bands     46    632  41.6%   +44.87   -30.72    1.872    144 |      +35.82  6.39   28/30
prev-bands     50    525  34.6%   +48.71   -29.85    1.908    143 |      +33.40  4.70   30/30
prev-bands     60    438  28.9%   +49.89   -32.67    1.853    136 |      +32.74  8.12   29/30
production      0   1518 100.0%   +38.69   -24.65    1.745    145 |           —     —     n/a
production     20   1518 100.0%   +38.69   -24.65    1.745    145 |           —     —     n/a
production     30   1376  90.6%   +39.46   -24.01    1.763    143 |      +34.53  2.99   30/30
production     40    988  65.1%   +39.39   -30.16    1.696    147 |      +34.30  4.45   26/30
production     42    930  61.3%   +45.11   -29.22    1.889    146 |      +37.24  5.94   29/30
production     44    843  55.5%   +43.56   -29.39    1.849    146 |      +36.33  5.54   27/30
production     46    773  50.9%   +44.02   -29.82    1.866    145 |      +32.84  4.90   29/30
production     50    613  40.4%   +41.52   -30.62    1.781    143 |      +35.67  6.98   25/30
production     60    351  23.1%   +51.44   -29.84    2.086    127 |      +36.03  5.64   30/30
```

## s12 (%abv_SMA50 > 12%) — 2405 fillable signals (2405 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  >=44 kept%
-------------------------------------------------------
legacy        17   33   41   57   97   45.5       44.9%
prev-bands    12   17   31   49  100   36.7       30.6%
production    20   29   38   50  100   41.7       37.0%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +47.23  1.19   -28.92    2.014    145 |      +33.33  5.76   30/30
  35% prev-bands    +48.17  1.78   -25.42    2.013    144 |      +32.88  6.86   29/30
  35% production    +48.29  1.60   -28.35    1.999    145 |      +34.56  6.54   29/30
  25% legacy        +51.57  1.24   -31.88    2.036    140 |      +35.73  6.61   30/30
  25% prev-bands    +51.67  0.74   -28.17    2.101    141 |      +36.32  6.31   30/30
  25% production    +48.87  0.97   -29.38    2.007    143 |      +34.80  7.16   28/30
  15% legacy        +51.63  1.38   -25.79    2.293    126 |      +32.36  7.29   30/30
  15% prev-bands    +52.47  1.61   -29.40    2.115    132 |      +33.24  7.15   30/30
  15% production    +52.29  2.97   -33.83    2.038    130 |      +31.11  6.39   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +36.65 (sd  2.9)     +57.61 (sd  0.7)
  35% prev-bands      +42.39 (sd  0.5)     +62.17 (sd  0.6)
  35% production      +39.83 (sd  0.3)     +59.05 (sd  2.7)
  25% legacy          +38.11 (sd  0.8)     +60.72 (sd  3.3)
  25% prev-bands      +39.36 (sd  1.2)     +76.57 (sd  2.4)
  25% production      +42.38 (sd  0.4)     +69.95 (sd  0.7)
  15% legacy          +40.55 (sd  0.8)     +72.19 (sd  1.7)
  15% prev-bands      +44.04 (sd  0.1)     +79.19 (sd  2.1)
  15% production      +32.48 (sd  1.0)     +76.19 (sd  1.3)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   2405 100.0%   +37.55   -22.41    1.899    145 |           —     —     n/a
legacy         20   2393  99.5%   +37.76   -22.41    1.908    145 |      +37.72  1.25   22/30
legacy         30   2081  86.5%   +41.89   -22.41    2.062    145 |      +35.13  4.54   28/30
legacy         40   1333  55.4%   +34.84   -25.00    1.658    145 |      +32.09  4.75   24/30
legacy         42   1201  49.9%   +36.32   -28.00    1.672    145 |      +33.04  5.80   18/30
legacy         44   1081  44.9%   +40.31   -27.38    1.818    145 |      +32.10  5.74   28/30
legacy         46    982  40.8%   +43.59   -27.21    1.925    145 |      +32.85  4.72   29/30
legacy         50    852  35.4%   +47.95   -27.81    2.051    145 |      +33.19  5.65   30/30
legacy         60    535  22.2%   +44.28   -31.08    1.790    136 |      +36.06  6.49   25/30
prev-bands      0   2405 100.0%   +36.22   -22.41    1.859    146 |           —     —     n/a
prev-bands     20   1801  74.9%   +38.24   -23.59    1.831    145 |      +33.08  5.24   23/30
prev-bands     30   1313  54.6%   +39.60   -24.75    1.796    144 |      +33.45  4.91   28/30
prev-bands     40    922  38.3%   +43.86   -25.34    1.910    144 |      +32.15  5.71   29/30
prev-bands     42    797  33.1%   +48.26   -26.79    1.994    144 |      +33.41  4.79   30/30
prev-bands     44    737  30.6%   +48.96   -27.25    2.015    144 |      +34.01  6.15   30/30
prev-bands     46    693  28.8%   +50.50   -27.71    2.066    144 |      +36.21  5.56   29/30
prev-bands     50    595  24.7%   +52.93   -28.32    2.125    141 |      +34.58  6.60   30/30
prev-bands     60    451  18.8%   +51.64   -31.54    1.912    135 |      +32.84  5.90   30/30
production      0   2405 100.0%   +34.12   -21.83    1.760    146 |           —     —     n/a
production     20   2405 100.0%   +34.12   -21.83    1.760    146 |           —     —     n/a
production     30   1790  74.4%   +37.65   -25.56    1.783    145 |      +32.89  5.69   24/30
production     40   1127  46.9%   +39.34   -27.46    1.771    144 |      +31.20  6.62   26/30
production     42    982  40.8%   +48.46   -27.50    2.009    146 |      +31.18  4.14   30/30
production     44    890  37.0%   +49.97   -28.27    2.057    145 |      +33.24  7.22   30/30
production     46    797  33.1%   +49.30   -27.86    2.038    145 |      +35.56  5.56   30/30
production     50    625  26.0%   +47.92   -28.91    1.973    143 |      +35.91  6.76   29/30
production     60    354  14.7%   +55.17   -28.36    2.179    127 |      +30.55  6.07   30/30
```
