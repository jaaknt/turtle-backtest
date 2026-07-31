# Ranking Weights — three-feature 40/35/25 vs the legacy six-dimension weighting

Period 2021-01-01 .. 2026-06-26, $30,000 initial equity, 4% positions, 366d calendar hold, next-day-open entries.

`production` is the shipped QullamaggieRanking (ADR 40 / SMA50 35 / price 25); `legacy` is the six-dimension weighting it replaced (SMA50 50, price 13, ADR 12, compression 12, ROC252 10, RSI 3). Ties are broken at random over 20 redraws; `null` is 30 random subsets of the same size.

## s20 (%abv_SMA50 > 20%) — 506 fillable signals (506 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  <40 kept%
------------------------------------------------------
legacy        45   56   63   70   97   63.9     100.0%
production    31   39   56   66  100   54.8      73.3%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +41.53  1.52   -24.94    2.018    105 |      +32.99  4.22   30/30
  35% production    +46.08  0.31   -25.21    2.073    105 |      +34.66  5.47   29/30
  25% legacy        +42.40  1.46   -27.50    1.890    100 |      +30.08  5.34   30/30
  25% production    +41.95  2.07   -26.02    1.875     97 |      +30.62  5.70   30/30
  15% legacy        +36.51  2.62   -28.46    2.098     76 |      +22.37  5.25   30/30
  15% production    +35.14  0.63   -32.07    1.752     76 |      +23.39  5.12   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +35.20 (sd  0.5)     +53.99 (sd  0.9)
  35% production      +28.32 (sd  0.3)     +63.65 (sd  0.7)
  25% legacy          +29.35 (sd  0.9)     +49.80 (sd  1.5)
  25% production      +26.20 (sd  1.4)     +59.76 (sd  3.9)
  15% legacy          +24.82 (sd  0.6)     +43.04 (sd  6.2)
  15% production      +15.75 (sd  1.4)     +50.04 (sd  0.4)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0    506 100.0%   +29.49   -30.93    1.552    131 |           —     —     n/a
legacy         20    506 100.0%   +29.49   -30.93    1.552    131 |           —     —     n/a
legacy         30    506 100.0%   +29.49   -30.93    1.552    131 |           —     —     n/a
legacy         40    506 100.0%   +29.49   -30.93    1.552    131 |           —     —     n/a
legacy         50    493  97.4%   +28.79   -30.50    1.527    131 |      +30.17  1.87    6/30
legacy         60    326  64.4%   +35.17   -24.99    1.732    114 |      +34.47  4.06   16/30
production      0    506 100.0%   +28.57   -31.34    1.523    132 |           —     —     n/a
production     20    506 100.0%   +28.57   -31.34    1.523    132 |           —     —     n/a
production     30    506 100.0%   +28.57   -31.34    1.523    132 |           —     —     n/a
production     40    371  73.3%   +33.81   -24.83    1.689    120 |      +33.62  4.58   14/30
production     50    269  53.2%   +37.28   -25.28    1.742    115 |      +32.83  4.28   24/30
production     60    239  47.2%   +43.57   -25.16    1.939    113 |      +33.76  6.74   28/30
```

## s16 (%abv_SMA50 > 16%) — 841 fillable signals (841 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  <40 kept%
------------------------------------------------------
legacy        18   38   54   65   97   51.9      72.9%
production    12   27   41   60  100   43.7      52.1%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +41.32  0.43   -24.42    1.940    116 |      +34.90  4.65   27/30
  35% production    +42.72  0.00   -25.74    1.939    123 |      +34.12  5.08   29/30
  25% legacy        +35.40  0.92   -22.82    1.789    107 |      +32.40  5.53   20/30
  25% production    +39.92  3.59   -23.87    1.834    110 |      +31.39  7.25   28/30
  15% legacy        +33.35  0.74   -27.93    1.555     99 |      +25.14  5.34   28/30
  15% production    +45.18  2.21   -25.90    1.987     99 |      +27.03  5.65   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +27.07 (sd  0.5)     +44.40 (sd  0.6)
  35% production      +26.23 (sd  0.0)     +56.62 (sd  1.9)
  25% legacy          +31.33 (sd  1.4)     +47.75 (sd  1.3)
  25% production      +25.30 (sd  1.6)     +57.91 (sd  2.5)
  15% legacy          +29.35 (sd  0.0)     +39.40 (sd  1.0)
  15% production      +29.31 (sd  0.9)     +62.75 (sd  2.9)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0    841 100.0%   +37.31   -27.10    1.746    143 |           —     —     n/a
legacy         20    835  99.3%   +37.25   -27.10    1.749    143 |      +36.87  1.00   13/30
legacy         30    744  88.5%   +35.98   -25.47    1.725    141 |      +33.89  2.39   23/30
legacy         40    613  72.9%   +35.96   -25.47    1.720    140 |      +33.10  4.34   22/30
legacy         50    479  57.0%   +35.27   -30.88    1.711    132 |      +33.59  4.51   19/30
legacy         60    316  37.6%   +40.64   -24.99    1.896    118 |      +34.25  4.83   28/30
production      0    841 100.0%   +37.50   -27.10    1.762    143 |           —     —     n/a
production     20    748  88.9%   +40.60   -27.32    1.867    141 |      +35.69  3.35   29/30
production     30    613  72.9%   +38.91   -25.84    1.862    138 |      +31.83  3.85   28/30
production     40    438  52.1%   +41.15   -24.95    1.899    129 |      +32.90  5.16   28/30
production     50    301  35.8%   +44.37   -25.74    2.005    123 |      +32.70  5.22   30/30
production     60    246  29.3%   +47.18   -25.95    2.028    115 |      +32.70  4.92   30/30
```

## s12 (%abv_SMA50 > 12%) — 1312 fillable signals (1312 raised, 0 with no entry bar inside the period)

Score distribution — the same gate keeps different fractions under each scheme:

```text
scheme       min  p25  p50  p75  max   mean  <40 kept%
------------------------------------------------------
legacy        18   33   43   59   97   46.4      58.7%
production    12   22   33   50  100   37.4      40.1%
```

Matched selectivity — top K% by each scheme, so both arms choose from an identical number of candidates. The `taken` columns still differ: cash runs out on different days under each ordering, so the executed counts are an outcome, not a control.

```text
 keep scheme         CAGR%    sd   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
-------------------------------------------------------------------------------------
  35% legacy        +41.84  1.62   -32.35    1.901    129 |      +30.03  4.46   30/30
  35% production    +48.01  0.00   -32.50    2.018    132 |      +29.45  5.56   30/30
  25% legacy        +41.91  1.82   -24.85    1.928    120 |      +29.94  6.20   28/30
  25% production    +51.23  1.18   -26.29    2.170    125 |      +28.96  6.47   30/30
  15% legacy        +36.36  1.64   -21.58    1.827    106 |      +29.05  5.42   26/30
  15% production    +54.16  1.27   -22.40    2.316    112 |      +26.61  5.13   30/30
```

Sub-period split — an edge that only exists in one half is not an edge:

```text
 keep scheme          2021-01..2023-07     2023-07..2026-06
-----------------------------------------------------------
  35% legacy          +25.29 (sd  1.0)     +61.50 (sd  3.1)
  35% production      +33.41 (sd  0.0)     +57.21 (sd  0.0)
  25% legacy          +24.48 (sd  0.6)     +48.11 (sd  1.4)
  25% production      +31.59 (sd  0.4)     +58.88 (sd  1.3)
  15% legacy          +33.81 (sd  0.5)     +46.88 (sd  1.8)
  15% production      +33.13 (sd  1.3)     +62.92 (sd  2.1)
```

MIN_RANKING gate sweep — each gate against a random gate keeping the same count:

```text
scheme       gate   kept  keep%    CAGR%   MaxDD%  Sortino  taken |  null CAGR%    sd   beats
---------------------------------------------------------------------------------------------
legacy          0   1312 100.0%   +22.95   -27.60    1.236    142 |           —     —     n/a
legacy         20   1306  99.5%   +22.87   -27.60    1.233    142 |      +23.59  1.09    4/30
legacy         30   1157  88.2%   +30.42   -27.28    1.535    143 |      +30.11  3.64   17/30
legacy         40    770  58.7%   +41.99   -26.97    1.952    142 |      +34.89  5.37   27/30
legacy         50    501  38.2%   +44.96   -30.57    2.002    130 |      +28.06  5.26   29/30
legacy         60    316  24.1%   +41.14   -24.99    1.922    118 |      +30.96  6.03   27/30
production      0   1312 100.0%   +28.19   -25.36    1.467    142 |           —     —     n/a
production     20   1013  77.2%   +33.45   -28.15    1.636    141 |      +32.20  2.38   19/30
production     30    745  56.8%   +49.68   -30.60    2.144    140 |      +31.65  6.05   30/30
production     40    526  40.1%   +55.76   -32.82    2.233    132 |      +30.94  4.68   30/30
production     50    336  25.6%   +49.69   -26.29    2.115    126 |      +31.24  6.29   30/30
production     60    251  19.1%   +48.19   -26.99    2.081    119 |      +31.32  6.10   30/30
```
