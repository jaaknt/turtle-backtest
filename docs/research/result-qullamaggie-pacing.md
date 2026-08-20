# Qullamaggie Portfolio Pacing — does a monthly intake cap help?

Run date: 2026-08-20 21:25:12 Tallinn time

| Parameter | Value |
|---|---|
| Algorithm | bk50d_s12_v2.0, 366d calendar hold |
| Ranking gate | QullamaggieRanking >= 44 (held fixed) |
| Window | 2015-01-01 – 2024-12-31 (holdout excluded) |
| Gated signals | 1698 |
| Sizing | 4% of portfolio value, $30,000 fresh at each start |
| Starts | quarterly, every horizon replayed from each |
| Cap | **the variable under study** — new positions per calendar month |

`sd`, `p10` and `min` are taken across start dates, not across trades: vintage concentration is a claim about start-date dependence, so the spread is the point. Quarterly starts overlap heavily, so treat those columns as ruling out a large effect rather than resolving a small one.

## Horizon 18 months — 35 start dates

```text
 cap/mo    mean  median     sd     p10     min  meanDD  Sortino  taken  vintages  top-mo%
-----------------------------------------------------------------------------------------
   none  +25.42  +23.53  21.32   +4.76   -8.62  -23.79    1.393     43       6.8    38.6%
      5  +26.51  +20.85  23.19   +2.02   -3.67  -23.00    1.478     39      10.5    13.3%
      4  +23.80  +24.69  20.04   +4.67  -11.41  -22.64    1.405     37      11.4    11.1%
      3  +22.72  +19.00  18.17   +5.53  -12.53  -21.66    1.441     34      13.0     8.9%
      2  +19.32  +17.94  16.64   +3.04  -10.42  -20.22    1.357     29      15.0     7.1%
```

## Horizon 3 years — 28 start dates

```text
 cap/mo    mean  median     sd     p10     min  meanDD  Sortino  taken  vintages  top-mo%
-----------------------------------------------------------------------------------------
   none  +29.03  +28.14  12.67  +12.91   +6.91  -28.34    1.518     72      13.8    23.8%
      5  +29.52  +27.20  13.37  +12.54   +3.89  -28.49    1.579     69      20.0     7.2%
      4  +29.01  +27.59  14.43  +10.99   +6.50  -28.37    1.557     67      21.5     6.0%
      3  +28.59  +28.81  12.92  +12.01   +5.69  -28.40    1.607     65      25.1     4.7%
      2  +26.89  +25.72  13.53   +9.16   +5.07  -29.08    1.563     57      29.6     3.5%
```

## Horizon 5 years — 21 start dates

```text
 cap/mo    mean  median     sd     p10     min  meanDD  Sortino  taken  vintages  top-mo%
-----------------------------------------------------------------------------------------
   none  +34.50  +36.66   9.91  +20.60  +13.41  -33.45    1.694    115      23.7    16.6%
      5  +33.07  +32.12   9.62  +17.42  +15.63  -34.34    1.677    110      32.8     4.6%
      4  +34.03  +35.48  10.78  +19.76  +13.78  -34.67    1.711    108      35.0     3.7%
      3  +33.32  +35.77   8.63  +21.43  +14.50  -34.97    1.754    105      41.0     2.8%
      2  +32.97  +34.34   8.29  +22.43  +13.60  -38.47    1.757     95      49.3     2.1%
```

## Reading

The cap works mechanically — `top-mo%` and `vintages` move sharply in the intended direction at every horizon — and buys nothing. At 18 months it cuts dispersion and the mean in the same proportion, which is what holding less exposure does rather than what managing risk does, and it leaves the worst start date worse off. At 3 years there is no effect at all. At 5 years the p10 and Sortino edge is inside what overlapping start dates can produce by chance, and mean drawdown moves the wrong way.

So an intake cap is a preference, not an edge. It is a reasonable thing to want if committing a year of capacity on one month's signals is uncomfortable to hold — it just should not be adopted expecting better returns.
