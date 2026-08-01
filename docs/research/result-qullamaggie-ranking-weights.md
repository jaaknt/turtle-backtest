# Ranking Weights — three-feature 40/35/25 vs the legacy six-dimension weighting

Period 2021-01-01 .. 2026-06-26, $30,000 initial equity, 4% positions, 366d calendar hold, next-day-open entries.

`production` is the shipped QullamaggieRanking (ADR 40 / SMA50 35 / price 25); `legacy` is the six-dimension weighting it replaced (SMA50 50, price 13, ADR 12, compression 12, ROC252 10, RSI 3). Ties are broken at random over 20 redraws; `null` is 30 random subsets of the same size.

## s20 (%abv_SMA50 > 20%) — 680 fillable signals (680 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  <40 kept%
------------------------------------------------------
legacy        45   57   63   70   97   64.0     100.0%
production    31   39   60   66  100   55.9      74.6%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +41.30  1.91   -27.42    1.866    112 |      +32.83  5.43   26/30
  35% production    +43.16  1.14   -25.40    1.845    114 |      +34.51  5.00   30/30
  25% legacy        +50.17  4.18   -28.53    2.160    104 |      +35.14  6.65   29/30
  25% production    +47.52  1.93   -26.12    1.993    105 |      +32.71  6.16   30/30
  15% legacy        +45.07  2.18   -31.67    2.089     94 |      +28.04  5.58   30/30
  15% production    +47.61  1.69   -37.63    1.970     86 |      +29.39  5.91   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +36.44 (sd  1.3)     +59.93 (sd  1.6)
  35% production      +29.23 (sd  0.3)     +69.50 (sd  2.6)
  25% legacy          +40.07 (sd  1.7)     +55.73 (sd  1.4)
  25% production      +35.73 (sd  2.2)     +71.54 (sd  1.7)
  15% legacy          +33.26 (sd  0.5)     +54.39 (sd  5.5)
  15% production      +24.06 (sd  0.8)     +69.52 (sd  3.1)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0    680 100.0%   +41.05   -28.54    1.729    140 |           —     —     n/a
legacy         20    680 100.0%   +41.05   -28.54    1.729    140 |           —     —     n/a
legacy         30    680 100.0%   +41.05   -28.54    1.729    140 |           —     —     n/a
legacy         40    680 100.0%   +41.05   -28.54    1.729    140 |           —     —     n/a
legacy         50    658  96.8%   +41.05   -28.54    1.729    140 |      +38.39  2.51   26/30
legacy         60    437  64.3%   +32.16   -25.92    1.500    133 |      +36.76  5.85    7/30
production      0    680 100.0%   +40.46   -28.54    1.710    139 |           —     —     n/a
production     20    680 100.0%   +40.46   -28.54    1.710    139 |           —     —     n/a
production     30    680 100.0%   +40.46   -28.54    1.710    139 |           —     —     n/a
production     40    507  74.6%   +42.61   -28.01    1.772    135 |      +36.14  5.17   26/30
production     50    382  56.2%   +44.63   -28.90    1.844    132 |      +34.10  6.26   29/30
production     60    342  50.3%   +53.26   -30.87    2.062    128 |      +35.43  5.70   30/30
```

## s16 (%abv_SMA50 > 16%) — 1144 fillable signals (1144 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  <40 kept%
------------------------------------------------------
legacy        18   38   54   64   97   51.5      71.9%
production    12   24   41   60  100   44.1      52.6%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +41.20  1.44   -27.06    1.771    131 |      +34.56  6.23   25/30
  35% production    +47.57  0.79   -31.72    1.869    137 |      +35.43  4.43   29/30
  25% legacy        +40.83  0.62   -24.75    1.845    119 |      +36.18  5.31   24/30
  25% production    +44.92  1.86   -27.06    1.892    121 |      +34.20  5.72   29/30
  15% legacy        +49.82  1.16   -28.16    2.154    106 |      +30.43  5.73   30/30
  15% production    +48.62  2.73   -26.84    2.023    109 |      +32.09  5.53   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +29.15 (sd  0.8)     +42.07 (sd  0.7)
  35% production      +32.52 (sd  0.2)     +67.69 (sd  4.5)
  25% legacy          +33.52 (sd  0.5)     +51.64 (sd  0.7)
  25% production      +32.89 (sd  1.7)     +74.53 (sd  1.4)
  15% legacy          +38.68 (sd  0.8)     +44.97 (sd  1.9)
  15% production      +36.35 (sd  2.6)     +67.16 (sd  2.1)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   1144 100.0%   +38.01   -26.16    1.651    142 |           —     —     n/a
legacy         20   1135  99.2%   +37.41   -26.16    1.632    142 |      +38.07  0.65    3/30
legacy         30   1008  88.1%   +38.16   -25.34    1.647    142 |      +35.20  2.89   26/30
legacy         40    822  71.9%   +35.78   -27.33    1.567    143 |      +38.15  3.55    9/30
legacy         50    636  55.6%   +42.21   -30.29    1.783    144 |      +35.80  4.48   27/30
legacy         60    416  36.4%   +40.77   -29.38    1.726    132 |      +33.69  5.55   27/30
production      0   1144 100.0%   +38.09   -25.86    1.653    142 |           —     —     n/a
production     20   1020  89.2%   +39.51   -25.86    1.691    141 |      +36.34  2.53   27/30
production     30    834  72.9%   +38.33   -27.40    1.666    142 |      +37.39  3.46   18/30
production     40    602  52.6%   +40.97   -30.95    1.668    142 |      +35.47  5.18   25/30
production     50    418  36.5%   +47.78   -32.87    1.868    138 |      +33.90  4.79   30/30
production     60    347  30.3%   +55.87   -30.76    2.094    131 |      +34.53  5.06   30/30
```

## s12 (%abv_SMA50 > 12%) — 1775 fillable signals (1775 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  <40 kept%
------------------------------------------------------
legacy        18   33   43   58   97   46.2      58.1%
production    12   22   33   50  100   37.9      41.2%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +43.69  0.28   -29.33    1.822    140 |      +36.79  6.15   25/30
  35% production    +44.55  1.20   -27.69    1.842    143 |      +36.10  5.56   29/30
  25% legacy        +44.34  0.89   -32.24    1.798    132 |      +32.51  5.23   29/30
  25% production    +56.43  0.65   -27.67    2.123    138 |      +33.86  5.91   30/30
  15% legacy        +41.18  0.74   -25.63    1.858    116 |      +30.33  5.60   28/30
  15% production    +53.02  1.28   -27.30    2.081    120 |      +30.87  5.00   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +35.33 (sd  0.0)     +61.53 (sd  0.0)
  35% production      +38.90 (sd  0.5)     +55.43 (sd  2.0)
  25% legacy          +29.73 (sd  0.0)     +49.84 (sd  0.0)
  25% production      +43.19 (sd  0.2)     +52.67 (sd  2.2)
  15% legacy          +33.81 (sd  0.9)     +53.94 (sd  0.8)
  15% production      +38.81 (sd  0.5)     +65.69 (sd  2.5)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   1775 100.0%   +31.87   -24.90    1.574    145 |           —     —     n/a
legacy         20   1767  99.5%   +31.59   -24.27    1.565    145 |      +31.59  0.89   10/30
legacy         30   1552  87.4%   +33.41   -27.98    1.600    145 |      +31.36  2.65   23/30
legacy         40   1032  58.1%   +36.61   -25.51    1.632    144 |      +32.03  3.59   28/30
legacy         50    664  37.4%   +47.82   -26.26    1.961    145 |      +36.85  5.02   30/30
legacy         60    415  23.4%   +40.67   -29.43    1.723    132 |      +33.83  6.07   25/30
production      0   1775 100.0%   +33.49   -25.66    1.600    145 |           —     —     n/a
production     20   1375  77.5%   +35.92   -25.25    1.640    143 |      +31.56  3.71   26/30
production     30   1027  57.9%   +40.39   -26.20    1.771    144 |      +33.62  5.23   28/30
production     40    732  41.2%   +44.93   -26.00    1.879    143 |      +36.47  4.81   29/30
production     50    476  26.8%   +58.05   -27.76    2.168    138 |      +34.80  6.16   30/30
production     60    359  20.2%   +57.87   -34.70    2.073    131 |      +30.41  6.10   30/30
```
