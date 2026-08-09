# Ranking Weights — recalibrated 40/35/25 bands vs the two weightings they replaced

Period 2021-01-01 .. 2026-06-26, $30,000 initial equity, 4% positions, 366d calendar hold, next-day-open entries.

`production` is the shipped QullamaggieRanking — 40/35/25 with bands re-derived on 2026-08-07 from the bk50d_s12_v2.0 cohort tables, each dimension's floor anchored outside its entry filter so no qualifying cohort scores 0. `prev-bands` is the same 40/35/25 split with the superseded bands it replaces (fitted to an s15_v1.3_roc100 run; ADR < 4.5% scored 0, which was 49.6% of the s12 pool). `legacy` is the six-dimension weighting dropped on 2026-07-29 (SMA50 50, price 13, ADR 12, compression 12, ROC252 10, RSI 3). Ties are broken at random over 20 redraws; `null` is 30 random subsets of the same size.

## s20 (%abv_SMA50 > 20%) — 871 fillable signals (871 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  <40 kept%
------------------------------------------------------
legacy        45   56   63   70   97   63.8     100.0%
prev-bands    31   39   56   66  100   55.2      72.8%
production    34   44   54   65  100   57.3      88.1%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +55.97  2.32   -26.66    2.388    120 |      +38.95  7.27   30/30
  35% prev-bands    +52.93  1.93   -25.55    2.269    120 |      +39.16  6.90   30/30
  35% production    +58.35  3.16   -29.39    2.305    122 |      +36.17  5.84   30/30
  25% legacy        +51.22  1.43   -27.37    2.318    110 |      +36.52  5.37   30/30
  25% prev-bands    +53.81  2.07   -22.44    2.302    110 |      +39.06  7.19   30/30
  25% production    +57.91  1.36   -22.70    2.292    110 |      +37.43  6.40   30/30
  15% legacy        +56.66  1.71   -30.54    2.552    100 |      +34.55  5.55   30/30
  15% prev-bands    +56.87  1.62   -33.19    2.460     94 |      +33.24  6.24   30/30
  15% production    +48.97  1.98   -32.08    2.136     95 |      +32.17  6.77   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +47.99 (sd  2.5)     +86.41 (sd  0.7)
  35% prev-bands      +32.94 (sd  2.3)     +88.28 (sd  1.8)
  35% production      +41.23 (sd  0.9)     +85.81 (sd  1.9)
  25% legacy          +46.81 (sd  2.9)     +77.32 (sd  2.2)
  25% prev-bands      +38.21 (sd  1.9)     +84.44 (sd  4.5)
  25% production      +41.27 (sd  0.0)     +61.49 (sd  3.2)
  15% legacy          +46.63 (sd  0.9)     +65.96 (sd  0.9)
  15% prev-bands      +34.22 (sd  0.5)     +81.74 (sd  3.6)
  15% production      +40.62 (sd  2.2)     +71.81 (sd  2.4)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0    871 100.0%   +44.58   -27.82    1.926    146 |           —     —     n/a
legacy         20    871 100.0%   +44.58   -27.82    1.926    146 |           —     —     n/a
legacy         30    871 100.0%   +44.58   -27.82    1.926    146 |           —     —     n/a
legacy         40    871 100.0%   +44.58   -27.82    1.926    146 |           —     —     n/a
legacy         42    871 100.0%   +44.58   -27.82    1.926    146 |           —     —     n/a
legacy         44    871 100.0%   +44.58   -27.82    1.926    146 |           —     —     n/a
legacy         46    867  99.5%   +44.58   -27.82    1.926    146 |      +44.81  1.58    4/30
legacy         50    844  96.9%   +40.21   -27.31    1.726    146 |      +43.43  2.56    6/30
legacy         60    549  63.0%   +42.29   -30.40    1.717    136 |      +42.29  8.28   17/30
prev-bands      0    871 100.0%   +43.53   -27.82    1.896    146 |           —     —     n/a
prev-bands     20    871 100.0%   +43.53   -27.82    1.896    146 |           —     —     n/a
prev-bands     30    871 100.0%   +43.53   -27.82    1.896    146 |           —     —     n/a
prev-bands     40    634  72.8%   +47.59   -27.47    1.927    143 |      +41.46  7.71   24/30
prev-bands     42    618  71.0%   +48.32   -27.47    1.956    143 |      +43.90  6.20   24/30
prev-bands     44    554  63.6%   +50.93   -30.99    2.002    140 |      +40.74  7.20   28/30
prev-bands     46    545  62.6%   +50.90   -30.99    2.001    139 |      +39.29  6.49   28/30
prev-bands     50    475  54.5%   +62.05   -31.79    2.274    137 |      +40.09  6.08   30/30
prev-bands     60    424  48.7%   +54.63   -31.41    2.043    131 |      +39.00  6.26   30/30
production      0    871 100.0%   +43.96   -27.82    1.911    145 |           —     —     n/a
production     20    871 100.0%   +43.96   -27.82    1.911    145 |           —     —     n/a
production     30    871 100.0%   +43.96   -27.82    1.911    145 |           —     —     n/a
production     40    767  88.1%   +41.15   -27.47    1.710    145 |      +43.59  4.62   10/30
production     42    735  84.4%   +40.99   -27.47    1.702    144 |      +43.84  4.12    6/30
production     44    694  79.7%   +40.70   -27.47    1.694    143 |      +44.28  6.32    7/30
production     46    640  73.5%   +42.16   -27.47    1.732    140 |      +44.53  6.84   10/30
production     50    558  64.1%   +53.27   -31.99    2.040    134 |      +39.33  6.23   30/30
production     60    344  39.5%   +50.48   -27.42    2.082    126 |      +38.51  6.41   30/30
```

## s16 (%abv_SMA50 > 16%) — 1487 fillable signals (1487 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  <40 kept%
------------------------------------------------------
legacy        17   37   52   64   97   51.0      70.3%
prev-bands    12   24   40   60  100   43.1      50.1%
production    24   36   46   57  100   48.6      64.5%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +45.72  0.04   -30.69    1.841    134 |      +35.06  6.23   28/30
  35% prev-bands    +52.74  1.43   -30.48    2.053    141 |      +35.41  7.24   30/30
  35% production    +50.89  2.41   -30.72    1.979    139 |      +36.67  6.30   30/30
  25% legacy        +52.47  1.26   -29.14    2.208    129 |      +36.22  6.73   29/30
  25% prev-bands    +48.95  2.12   -29.22    2.009    133 |      +33.65  6.75   29/30
  25% production    +49.29  1.07   -28.65    2.059    130 |      +37.66  5.98   30/30
  15% legacy        +52.99  0.72   -26.89    2.397    112 |      +35.13  4.30   30/30
  15% prev-bands    +56.24  2.20   -23.47    2.374    114 |      +34.83  5.99   30/30
  15% production    +58.88  2.15   -23.51    2.296    112 |      +35.91  5.75   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +31.48 (sd  0.1)     +54.60 (sd  6.1)
  35% prev-bands      +38.50 (sd  1.3)     +65.86 (sd  2.5)
  35% production      +36.38 (sd  0.7)     +64.70 (sd  1.1)
  25% legacy          +37.44 (sd  2.1)     +68.35 (sd  1.9)
  25% prev-bands      +37.99 (sd  2.6)     +81.48 (sd  3.1)
  25% production      +32.96 (sd  1.6)     +74.68 (sd  2.6)
  15% legacy          +48.55 (sd  0.0)     +69.46 (sd  0.5)
  15% prev-bands      +39.23 (sd  1.6)     +87.25 (sd  2.8)
  15% production      +40.18 (sd  0.3)     +61.07 (sd  0.3)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   1487 100.0%   +40.05   -25.63    1.808    144 |           —     —     n/a
legacy         20   1473  99.1%   +40.81   -25.63    1.832    143 |      +40.21  1.08   23/30
legacy         30   1301  87.5%   +40.96   -24.69    1.819    143 |      +38.66  3.45   25/30
legacy         40   1045  70.3%   +45.64   -28.83    1.944    143 |      +38.16  4.91   28/30
legacy         42    983  66.1%   +44.36   -27.55    1.916    143 |      +36.30  4.32   29/30
legacy         44    917  61.7%   +44.63   -27.16    1.908    145 |      +37.47  5.80   27/30
legacy         46    865  58.2%   +48.37   -27.74    2.071    146 |      +36.59  6.42   29/30
legacy         50    807  54.3%   +47.60   -27.61    2.038    145 |      +36.25  4.32   30/30
legacy         60    521  35.0%   +45.72   -30.69    1.841    134 |      +35.87  6.41   28/30
prev-bands      0   1487 100.0%   +39.10   -28.50    1.758    143 |           —     —     n/a
prev-bands     20   1314  88.4%   +42.86   -28.50    1.868    141 |      +37.55  4.27   28/30
prev-bands     30   1058  71.1%   +43.22   -25.64    1.850    142 |      +36.49  4.49   28/30
prev-bands     40    745  50.1%   +44.83   -26.87    1.901    144 |      +38.02  5.72   28/30
prev-bands     42    676  45.5%   +47.58   -28.22    1.981    144 |      +35.86  6.86   29/30
prev-bands     44    621  41.8%   +47.40   -30.73    1.969    144 |      +37.70  8.23   27/30
prev-bands     46    613  41.2%   +47.37   -30.73    1.968    143 |      +35.87  5.70   30/30
prev-bands     50    512  34.4%   +52.05   -29.85    2.024    142 |      +36.48  7.58   30/30
prev-bands     60    426  28.6%   +62.78   -33.60    2.248    136 |      +36.30  6.60   30/30
production      0   1487 100.0%   +38.14   -25.63    1.744    144 |           —     —     n/a
production     20   1487 100.0%   +38.14   -25.63    1.744    144 |           —     —     n/a
production     30   1345  90.5%   +38.52   -25.66    1.731    145 |      +37.89  2.60   17/30
production     40    959  64.5%   +47.34   -28.13    1.974    143 |      +37.57  5.53   30/30
production     42    903  60.7%   +45.95   -27.86    1.931    146 |      +34.84  5.33   30/30
production     44    820  55.1%   +48.51   -28.46    2.034    146 |      +37.07  6.13   28/30
production     46    753  50.6%   +49.25   -27.90    2.014    145 |      +37.17  4.91   30/30
production     50    596  40.1%   +45.18   -28.85    1.867    143 |      +36.28  5.65   29/30
production     60    342  23.0%   +49.96   -27.69    2.079    127 |      +31.95  7.25   30/30
```

## s12 (%abv_SMA50 > 12%) — 2374 fillable signals (2374 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  <40 kept%
------------------------------------------------------
legacy        17   32   41   57   97   45.4      55.3%
prev-bands    12   17   31   49  100   36.5      38.0%
production    20   29   37   50  100   41.5      46.3%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +50.56  1.87   -28.16    2.149    145 |      +33.31  6.05   30/30
  35% prev-bands    +49.37  0.50   -26.92    2.052    144 |      +33.00  5.80   30/30
  35% production    +54.15  2.18   -26.77    2.197    145 |      +33.74  7.54   29/30
  25% legacy        +54.91  2.40   -31.94    2.112    137 |      +39.20  6.71   30/30
  25% prev-bands    +50.75  0.45   -27.23    2.076    142 |      +36.58  5.25   30/30
  25% production    +50.28  2.06   -27.99    2.069    143 |      +37.65  5.87   30/30
  15% legacy        +52.59  1.61   -26.81    2.295    126 |      +31.84  5.00   30/30
  15% prev-bands    +53.32  1.43   -28.78    2.156    132 |      +34.08  6.83   30/30
  15% production    +53.30  1.52   -32.10    2.123    129 |      +31.24  6.66   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +35.41 (sd  2.2)     +62.39 (sd  0.6)
  35% prev-bands      +43.15 (sd  0.3)     +62.39 (sd  1.4)
  35% production      +41.54 (sd  1.4)     +61.14 (sd  0.9)
  25% legacy          +37.87 (sd  1.1)     +62.66 (sd  0.8)
  25% prev-bands      +36.54 (sd  0.0)     +72.22 (sd  0.0)
  25% production      +40.67 (sd  1.9)     +67.47 (sd  0.2)
  15% legacy          +40.38 (sd  1.1)     +76.81 (sd  2.2)
  15% prev-bands      +44.43 (sd  1.2)     +75.44 (sd  0.9)
  15% production      +32.66 (sd  1.4)     +79.60 (sd  1.3)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   2374 100.0%   +41.97   -22.41    2.072    145 |           —     —     n/a
legacy         20   2362  99.5%   +42.19   -22.41    2.081    145 |      +41.22  2.31   27/30
legacy         30   2052  86.4%   +43.75   -22.41    2.108    145 |      +37.93  4.29   27/30
legacy         40   1314  55.3%   +41.55   -24.31    1.906    142 |      +33.77  5.90   28/30
legacy         42   1181  49.7%   +41.00   -24.36    1.864    143 |      +33.44  5.33   27/30
legacy         44   1062  44.7%   +45.52   -26.87    2.004    145 |      +33.64  6.37   29/30
legacy         46    964  40.6%   +48.72   -26.58    2.117    145 |      +34.73  5.26   30/30
legacy         50    835  35.2%   +50.24   -28.08    2.143    145 |      +35.13  7.19   29/30
legacy         60    520  21.9%   +44.86   -30.69    1.808    135 |      +35.17  7.83   29/30
prev-bands      0   2374 100.0%   +42.84   -22.41    2.119    145 |           —     —     n/a
prev-bands     20   1770  74.6%   +41.17   -22.36    1.950    145 |      +36.85  4.39   27/30
prev-bands     30   1288  54.3%   +43.86   -24.75    1.940    144 |      +32.07  5.74   30/30
prev-bands     40    902  38.0%   +45.06   -27.07    1.960    144 |      +33.07  5.70   30/30
prev-bands     42    778  32.8%   +50.69   -26.77    2.073    144 |      +34.76  5.48   30/30
prev-bands     44    718  30.2%   +50.31   -27.23    2.063    144 |      +38.56  6.31   29/30
prev-bands     46    675  28.4%   +50.70   -27.23    2.068    144 |      +39.35  5.79   30/30
prev-bands     50    581  24.5%   +53.49   -27.23    2.135    141 |      +38.79  8.78   28/30
prev-bands     60    439  18.5%   +61.23   -31.54    2.235    138 |      +33.86  6.08   30/30
production      0   2374 100.0%   +36.69   -23.06    1.875    146 |           —     —     n/a
production     20   2374 100.0%   +36.69   -23.06    1.875    146 |           —     —     n/a
production     30   1759  74.1%   +37.45   -25.60    1.784    145 |      +33.98  3.93   24/30
production     40   1099  46.3%   +40.81   -27.42    1.829    144 |      +30.94  5.67   29/30
production     42    956  40.3%   +51.11   -26.22    2.100    146 |      +32.73  4.49   30/30
production     44    868  36.6%   +54.19   -26.25    2.204    145 |      +36.34  6.26   30/30
production     46    777  32.7%   +51.92   -27.67    2.131    145 |      +36.94  7.23   30/30
production     50    608  25.6%   +47.98   -27.24    1.993    143 |      +36.99  6.37   30/30
production     60    344  14.5%   +55.26   -30.88    2.183    127 |      +33.12  7.36   30/30
```
