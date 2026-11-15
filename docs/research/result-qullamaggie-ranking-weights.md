# Ranking Weights — recalibrated 40/35/25 bands vs the two weightings they replaced

Period 2021-01-01 .. 2026-06-26, $30,000 initial equity, 4% positions, 366d calendar hold, next-day-open entries.

`production` is the shipped QullamaggieRanking — 40/35/25 with bands re-derived on 2026-08-07 from the bk50d_s12_v2.0 cohort tables, each dimension's floor anchored outside its entry filter so no qualifying cohort scores 0. `prev-bands` is the same 40/35/25 split with the superseded bands it replaces (fitted to an s15_v1.3_roc100 run; ADR < 4.5% scored 0, which was 49.6% of the s12 pool). `legacy` is the six-dimension weighting dropped on 2026-07-29 (SMA50 50, price 13, ADR 12, compression 12, ROC252 10, RSI 3). Ties are broken at random over 20 redraws; `null` is 30 random subsets of the same size.

## s20 (%abv_SMA50 > 20%) — 845 fillable signals (845 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  >=44 kept%
-------------------------------------------------------
legacy        45   56   63   70   97   63.6      100.0%
prev-bands    31   39   56   66  100   54.8       63.0%
production    34   44   54   65  100   56.8       79.1%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +56.78  0.56   -27.11    2.421    123 |      +36.12  5.38   30/30
  35% prev-bands    +52.97  1.26   -25.70    2.275    119 |      +37.20  6.16   30/30
  35% production    +58.14  2.67   -27.60    2.327    122 |      +36.43  7.12   30/30
  25% legacy        +53.76  0.96   -26.23    2.396    114 |      +34.58  6.78   30/30
  25% prev-bands    +54.03  2.01   -22.68    2.327    113 |      +33.34  6.88   30/30
  25% production    +60.56  3.51   -24.62    2.440    114 |      +36.17  5.20   30/30
  15% legacy        +51.38  2.14   -32.07    2.252    102 |      +32.22  4.79   30/30
  15% prev-bands    +56.58  0.81   -31.62    2.565     97 |      +33.39  6.95   30/30
  15% production    +51.32  2.19   -30.18    2.225     98 |      +31.19  4.66   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +43.36 (sd  0.8)     +78.30 (sd  4.0)
  35% prev-bands      +33.78 (sd  0.4)     +75.84 (sd  2.7)
  35% production      +39.33 (sd  1.3)     +78.28 (sd  4.7)
  25% legacy          +48.13 (sd  0.2)     +78.30 (sd  0.2)
  25% prev-bands      +35.89 (sd  2.5)     +84.50 (sd  3.2)
  25% production      +38.39 (sd  0.6)     +72.00 (sd  5.1)
  15% legacy          +38.60 (sd  1.0)     +54.03 (sd  2.0)
  15% prev-bands      +33.10 (sd  0.9)     +78.90 (sd  1.2)
  15% production      +41.92 (sd  2.6)     +67.68 (sd  4.7)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0    845 100.0%   +35.67   -27.27    1.584    146 |           —     —     n/a
legacy         20    845 100.0%   +35.67   -27.27    1.584    146 |           —     —     n/a
legacy         30    845 100.0%   +35.67   -27.27    1.584    146 |           —     —     n/a
legacy         40    845 100.0%   +35.67   -27.27    1.584    146 |           —     —     n/a
legacy         42    845 100.0%   +35.67   -27.27    1.584    146 |           —     —     n/a
legacy         44    845 100.0%   +35.67   -27.27    1.584    146 |           —     —     n/a
legacy         46    841  99.5%   +35.67   -27.27    1.584    146 |      +36.05  1.39    4/30
legacy         50    818  96.8%   +36.05   -27.27    1.593    145 |      +37.96  2.73    8/30
legacy         60    523  61.9%   +43.45   -33.03    1.774    132 |      +37.96  7.61   23/30
prev-bands      0    845 100.0%   +36.78   -29.52    1.595    144 |           —     —     n/a
prev-bands     20    845 100.0%   +36.78   -29.52    1.595    144 |           —     —     n/a
prev-bands     30    845 100.0%   +36.78   -29.52    1.595    144 |           —     —     n/a
prev-bands     40    611  72.3%   +53.52   -30.81    2.112    135 |      +40.85  8.89   27/30
prev-bands     42    594  70.3%   +53.51   -30.81    2.114    135 |      +40.00  5.81   30/30
prev-bands     44    532  63.0%   +53.37   -31.43    2.109    135 |      +41.64  5.85   30/30
prev-bands     46    522  61.8%   +53.37   -31.43    2.109    135 |      +36.72  7.97   30/30
prev-bands     50    453  53.6%   +56.68   -30.83    2.183    134 |      +37.94  8.29   30/30
prev-bands     60    404  47.8%   +54.25   -31.81    2.124    132 |      +36.07  5.97   30/30
production      0    845 100.0%   +36.56   -27.47    1.589    144 |           —     —     n/a
production     20    845 100.0%   +36.56   -27.47    1.589    144 |           —     —     n/a
production     30    845 100.0%   +36.56   -27.47    1.589    144 |           —     —     n/a
production     40    741  87.7%   +43.24   -28.93    1.804    137 |      +43.10  4.36   14/30
production     42    710  84.0%   +43.68   -29.55    1.817    137 |      +42.85  5.47   15/30
production     44    668  79.1%   +43.11   -29.55    1.794    138 |      +42.86  6.99   15/30
production     46    612  72.4%   +49.81   -30.78    1.997    137 |      +40.57  6.80   27/30
production     50    536  63.4%   +48.61   -30.72    1.947    134 |      +39.78  6.40   28/30
production     60    326  38.6%   +51.94   -28.82    2.155    125 |      +37.19  6.37   30/30
```

## s16 (%abv_SMA50 > 16%) — 1442 fillable signals (1442 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  >=44 kept%
-------------------------------------------------------
legacy        17   37   52   64   97   50.8       61.3%
prev-bands    12   24   39   60  100   42.7       41.4%
production    24   36   45   57  100   48.2       54.4%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +42.68  2.53   -31.53    1.780    132 |      +34.17  6.36   28/30
  35% prev-bands    +54.06  0.47   -32.93    2.099    136 |      +35.17  6.24   30/30
  35% production    +55.47  2.49   -31.21    2.142    135 |      +33.45  6.53   30/30
  25% legacy        +51.35  1.08   -29.73    2.173    130 |      +36.23  6.42   30/30
  25% prev-bands    +54.49  4.03   -32.00    2.153    133 |      +32.37  5.08   30/30
  25% production    +50.12  1.33   -33.53    2.039    133 |      +32.70  5.81   29/30
  15% legacy        +53.49  1.51   -27.88    2.399    115 |      +33.64  7.02   30/30
  15% prev-bands    +55.67  1.92   -23.70    2.397    116 |      +34.68  7.29   30/30
  15% production    +60.31  3.31   -25.29    2.394    115 |      +31.65  5.40   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +29.47 (sd  2.2)     +56.88 (sd  2.6)
  35% prev-bands      +33.74 (sd  0.5)     +59.76 (sd  1.2)
  35% production      +35.21 (sd  1.3)     +61.18 (sd  4.4)
  25% legacy          +33.85 (sd  0.7)     +59.83 (sd  1.7)
  25% prev-bands      +34.85 (sd  2.0)     +70.69 (sd  3.9)
  25% production      +32.26 (sd  1.3)     +63.53 (sd  1.4)
  15% legacy          +48.78 (sd  1.7)     +64.32 (sd  2.0)
  15% prev-bands      +38.62 (sd  1.6)     +87.48 (sd  5.0)
  15% production      +37.48 (sd  1.8)     +61.59 (sd  4.0)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   1442 100.0%   +36.92   -26.18    1.692    144 |           —     —     n/a
legacy         20   1428  99.0%   +36.85   -26.18    1.694    144 |      +36.37  0.74   20/30
legacy         30   1261  87.4%   +36.49   -29.07    1.670    145 |      +35.73  3.26   16/30
legacy         40   1013  70.2%   +37.89   -26.59    1.713    145 |      +32.76  3.47   29/30
legacy         42    949  65.8%   +41.23   -27.96    1.804    145 |      +34.15  4.20   29/30
legacy         44    884  61.3%   +42.30   -27.32    1.838    147 |      +33.65  4.50   29/30
legacy         46    837  58.0%   +43.62   -26.30    1.932    146 |      +34.66  5.18   30/30
legacy         50    781  54.2%   +43.50   -27.99    1.917    145 |      +34.46  6.01   28/30
legacy         60    496  34.4%   +42.20   -32.56    1.782    133 |      +33.78  6.08   27/30
prev-bands      0   1442 100.0%   +38.00   -26.40    1.734    143 |           —     —     n/a
prev-bands     20   1272  88.2%   +39.94   -25.66    1.784    144 |      +35.40  3.23   30/30
prev-bands     30   1019  70.7%   +37.00   -26.61    1.660    145 |      +35.86  4.44   15/30
prev-bands     40    716  49.7%   +38.93   -28.49    1.716    144 |      +36.08  4.51   22/30
prev-bands     42    649  45.0%   +40.47   -27.20    1.746    145 |      +35.21  7.02   24/30
prev-bands     44    597  41.4%   +45.02   -29.14    1.870    142 |      +33.77  5.86   29/30
prev-bands     46    588  40.8%   +45.02   -29.14    1.870    142 |      +32.45  7.15   30/30
prev-bands     50    488  33.8%   +56.16   -32.99    2.132    136 |      +34.81  7.31   30/30
prev-bands     60    403  27.9%   +60.05   -32.96    2.209    132 |      +34.01  6.38   30/30
production      0   1442 100.0%   +37.29   -25.28    1.711    143 |           —     —     n/a
production     20   1442 100.0%   +37.29   -25.28    1.711    143 |           —     —     n/a
production     30   1300  90.2%   +36.42   -25.80    1.677    143 |      +35.35  3.87   18/30
production     40    920  63.8%   +41.69   -30.10    1.802    144 |      +35.67  4.39   29/30
production     42    866  60.1%   +42.38   -27.86    1.815    145 |      +35.75  5.06   29/30
production     44    784  54.4%   +46.02   -28.46    1.921    146 |      +36.36  4.54   29/30
production     46    717  49.7%   +48.14   -28.45    1.985    144 |      +34.78  6.28   30/30
production     50    572  39.7%   +56.03   -31.38    2.190    138 |      +35.69  7.08   30/30
production     60    324  22.5%   +53.14   -29.63    2.161    128 |      +33.05  4.58   30/30
```

## s12 (%abv_SMA50 > 12%) — 2313 fillable signals (2313 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  >=44 kept%
-------------------------------------------------------
legacy        17   32   41   57   97   45.2       44.1%
prev-bands    12   17   30   47  100   36.2       30.0%
production    20   29   37   50  100   41.2       35.9%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +45.62  0.00   -27.81    1.979    146 |      +33.41  7.17   27/30
  35% prev-bands    +48.83  0.59   -28.11    2.042    144 |      +34.38  5.68   29/30
  35% production    +46.15  1.01   -29.83    1.933    146 |      +33.51  5.45   30/30
  25% legacy        +53.37  1.66   -31.39    2.094    133 |      +36.24  5.89   30/30
  25% prev-bands    +48.01  1.25   -27.23    1.939    142 |      +35.56  5.60   30/30
  25% production    +46.03  0.77   -28.73    1.914    145 |      +33.91  6.53   28/30
  15% legacy        +52.18  0.97   -28.24    2.218    130 |      +30.83  5.97   30/30
  15% prev-bands    +60.09  2.05   -32.57    2.337    132 |      +29.96  5.59   30/30
  15% production    +52.61  1.02   -34.70    2.126    132 |      +31.29  5.80   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +37.42 (sd  0.0)     +58.25 (sd  1.0)
  35% prev-bands      +40.30 (sd  0.1)     +54.98 (sd  0.7)
  35% production      +39.67 (sd  0.9)     +55.36 (sd  1.1)
  25% legacy          +36.12 (sd  0.1)     +59.66 (sd  1.5)
  25% prev-bands      +36.36 (sd  0.2)     +65.43 (sd  2.6)
  25% production      +37.25 (sd  0.0)     +62.94 (sd  0.0)
  15% legacy          +35.16 (sd  1.9)     +59.72 (sd  3.2)
  15% prev-bands      +41.45 (sd  1.7)     +62.74 (sd  4.6)
  15% production      +31.58 (sd  1.4)     +63.76 (sd  1.5)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   2313 100.0%   +36.69   -22.95    1.902    144 |           —     —     n/a
legacy         20   2301  99.5%   +36.46   -22.95    1.894    144 |      +36.62  0.81    5/30
legacy         30   1995  86.3%   +37.06   -22.95    1.910    144 |      +34.05  4.04   23/30
legacy         40   1268  54.8%   +36.80   -25.94    1.713    144 |      +30.76  6.17   25/30
legacy         42   1139  49.2%   +35.96   -28.37    1.674    145 |      +30.39  4.97   25/30
legacy         44   1020  44.1%   +39.26   -26.93    1.769    146 |      +29.98  5.08   28/30
legacy         46    928  40.1%   +40.60   -28.40    1.812    146 |      +30.93  5.48   30/30
legacy         50    807  34.9%   +45.62   -27.81    1.979    146 |      +35.03  6.11   30/30
legacy         60    494  21.4%   +39.87   -33.78    1.682    133 |      +33.78  6.14   24/30
prev-bands      0   2313 100.0%   +34.74   -22.18    1.823    145 |           —     —     n/a
prev-bands     20   1720  74.4%   +33.46   -24.33    1.670    146 |      +34.60  3.86   13/30
prev-bands     30   1238  53.5%   +37.88   -26.88    1.742    142 |      +31.12  5.73   26/30
prev-bands     40    869  37.6%   +46.27   -27.78    1.987    144 |      +34.84  5.68   29/30
prev-bands     42    751  32.5%   +48.29   -25.85    2.028    144 |      +35.68  5.49   30/30
prev-bands     44    693  30.0%   +47.93   -25.42    2.017    144 |      +33.26  4.42   30/30
prev-bands     46    647  28.0%   +46.71   -27.25    1.934    143 |      +35.73  5.36   29/30
prev-bands     50    554  24.0%   +53.33   -27.23    2.063    140 |      +36.52  6.83   30/30
prev-bands     60    415  17.9%   +59.43   -33.94    2.186    133 |      +31.83  6.15   30/30
production      0   2313 100.0%   +34.14   -21.48    1.791    145 |           —     —     n/a
production     20   2313 100.0%   +34.14   -21.48    1.791    145 |           —     —     n/a
production     30   1706  73.8%   +34.33   -27.02    1.680    144 |      +32.66  4.25   19/30
production     40   1056  45.7%   +40.64   -26.65    1.834    143 |      +32.87  4.81   27/30
production     42    917  39.6%   +44.60   -30.23    1.899    145 |      +32.02  5.99   29/30
production     44    830  35.9%   +45.43   -29.76    1.914    146 |      +32.16  7.92   28/30
production     46    740  32.0%   +47.91   -30.10    1.965    148 |      +33.86  4.86   29/30
production     50    580  25.1%   +45.45   -28.67    1.896    145 |      +37.32  7.05   27/30
production     60    324  14.0%   +53.49   -31.65    2.190    129 |      +33.13  6.54   30/30
```
