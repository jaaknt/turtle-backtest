analyze bk50d_s15_tr15_v1.2_roc100 366d results in period 2001-01-01 : 2026-06-26
  - propose 5 options how to achieve ~3 signals per month
  - important is that Med% and Sortino must stay on the same level
  - the main idea is to loose currently applied filters. what filters conditions loosening affects the Mean%, Sortino less
  
could you propose rankig algorithm for  s15_tr15 trades that will select only trades with most potential based on technical data (ADR is higher, (SMA10, SMA20), <your discovery> ) 

validate that @docs/research/qullamaggie-backtest-v4.md and @scripts/qullamaggie-backtest-v4.py are consistent
run the backtest described in @docs/research/qullamaggie-backtest-v4.md

could you provide portfolio simulation bk50d_s20_tr20_v1.2_roc100-366d, bk50d_s17_tr20_v1.2_roc100-366d, bk50d_s15_tr20_v1.2_roc100-366d
important files  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md, @scripts/qullamaggie-portfolio-sim.py
- period 2018-01-01 : 2026-06-26
- initial portfolio amount 30000$
- invest {3%, 4%, 5%, 6%, 7%, 8%} of portfolio at the time per trade
- if there is no liquidity then skip the trade
<!-- - prefer always bk50d_s20_tr10_v1.2_roc100 signals, but if there is liquidity then use bk50d_s15_tr15_v1.2_roc100 signals to reduce uninvested amounts
 - implement rank based funding to choose trade if there are several trades available on the same day 
- sell position if stock closes below 200 day SMA for 3 consequtive trades -->
- provide these metrics as output
  Mean% per months/years (rows are years and columns are months)
  Portfolio Max DD 
  Portfolio Calmar ratio
  Portfolio Sortino ratio  
  signals taken / skipped
  average uninvested capital per month
- add your findings to improve the portfolio perfoermance (Mean%, Sortino, Calmar)
- for top 10 algorithms print monthly returns by years (years are rows, months are columns)
- output file @docs/research/result-qullamaggie-portfolio-v4.md

could you provide bk50d_s15_tr20_v1.2_roc100 signals for period 2026-06-01 : today
mark signals that are also in bk50d_s20_tr20_v1.2_roc100
provide information to signals that are not in bk50d_s20_tr20_v1.2_roc100 list what was missing
Date    │ Symbol │ Entry $ │ Curr Price | Change in % | %abv SMA50 │ ADR% │ ADR_CHANGE │ RSI14 │ TR% │ ROC252% |
%abv SMA50 │ ADR% │ RSI14 │ TR% │ ROC252% - these values must be calculated on entry date 
add also latest date when stock data is available
references:  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md

could you provide bk50d_s20_tr20_v1.2_roc100 signals for period 2025-07-01 : today
Date    │ Symbol │ Entry $ │ Curr Price | Change in % | %abv SMA50 │ ADR% │ ADR_CHANGE │ RSI14 │ TR% │ ROC252% |
%abv SMA50 │ ADR% │ RSI14 │ TR% │ ROC252% - these values must be calculated on entry date 
add also latest date when stock data is available
provide mean trade performance, trade count if all trades will be closed on last date
references:  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md
- output file @docs/research/result-qullamaggie-trades-v4.md


 could you analyze bk50d_s20_tr20_v1.2_roc100-366d, bk50d_s15_tr20_v1.2_roc100-366d algorithms
 how  `roc_12m_cap`: `close / close[-252] − 1 < 100%` 
 cohorts (<20),  [-20-0), [0-20), [20-40), [40-60), [40-60), [60-80), [80-100), [100-120), [120-140), [140-160), [>160)
 affect performance
 output format columns
 Cohort            N     Med%    Mean%    Win%   Sortino      PF
 analyze period: 2015-01-01 : 2026-06-26  
 script: @scripts/qullamaggie-adr-cohorts.py
 save results in @docs/research/result-qullamaggie-roc-cohorts.md
 important files  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md

 could you analyze bk50d_s20_tr20_v1.2_roc100-366d, bk50d_s15_tr20_v1.2_roc100-366d algorithms
 how  `adr_pct`: `mean((high_i − low_i)/low_i, i in last 20 days, shift-1)`
 cohorts [0-1.0), [1.0-2.0), [2.0-2.5), [2.5-3.0), [3.0-3.5), [3.5-4.0), [4.0-4.5), [4.5-5.0), [5.0-7.0), (>8.0)  
 affect performance
 output format columns
 Cohort            N     Med%    Mean%    Win%   Sortino      PF
 analyze period: 2015-01-01 : 2026-06-26  
 script: @scripts/qullamaggie-adr-cohorts.py
 save results in @docs/research/result-qullamaggie-adr-cohorts.md
 important files:  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md

 could you analyze bk50d_s20_tr20_v1.2_roc100-366d, bk50d_s15_tr20_v1.2_roc100-366d algorithms
 how adr compresstion before breakout affects results
 ADR%(N) = mean( (high − low) / low ) over previous N days × 100 (exclude current day)
  compression = ADR%(10) / ADR%(50)
 cohorts [<0.5), [0.5-0.7) [0.7-0.8), [0.8-0.9), [0.9-1.0), [1.0-1.3), [>1.3) 
 output format columns
 Cohort            N     Med%    Mean%    Win%   Sortino      PF
 analyze period: 2015-01-01 : 2026-06-26  
 script: @docs/research/result-qullamaggie-adr-compression-cohorts.md
 important files: @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md

 could you analyze bk50d_s20_tr10_v1.2_roc100, bk50d_s15_tr15_v1.2_roc100 algorithms
 how  `rsi_filter`: `RSI(14)
 cohorts [0-20), [20-40), [40-60), [40-50), [50-60), [60-70), [70-75), [75-80), [80-90), [90-100]
 output format columns
 N     Med%    Mean%    Win%  Sortino  PF
 analyze period: 2015-01-01 : 2026-06-26  

 could you analyze bk50d_s20_tr10_v1.2_roc100, bk50d_s15_tr15_v1.2_roc100 algorithms
 how close price on entry affects results
 cohorts [0-5), [5-10), [10-20), [20-50), [50-100), [100-250), [250-700), [700-2000), [>2000]
 output format columns
 N     Med%    Mean%    Win%  Sortino  PF
 analyze period: 2015-01-01 : 2026-06-26  
 save results in @docs/research/result-qullamaggie-price-cohorts.md
 important files  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md

 could you analyze bk50d_s20_tr10_v1.2_roc100, bk50d_s15_tr15_v1.2_roc100 algorithms
 how vol_surge_ratio = volume / mean(volume[-51:-1]) affects results
 cohorts [<0.7), [0.7-0.8), [0.8-0.9), [0.9-1.0), [1.0-1.1), [1.1-1.2), [1.2-1.3), [1.3-1.4), [1.4-1.6), [1.6-2.0), [2.0-3.0), [3.0-4.0), [4.0-6.0), [>6.0) 
 output format columns
 Cohort            N     Med%    Mean%    Win%   Sortino      PF
 analyze period: 2015-01-01 : 2026-06-26  
 save results in @docs/research/result-qullamaggie-volsurge-cohorts.md
 important files  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md

 could you analyze bk50d_s12_tr20_v1.2_roc100-366d, bk50d_s15_tr20_v1.2_roc100-366d, bk50d_s17_tr20_v1.2_roc100-366d, bk50d_s20_tr20_v1.2_roc100-366d algorithms
 how tight_range2: (max(close[-11:-1]) − min(close[-11:-1])) / mean(close[-11:-1]) < Y affects results
 cohorts [<0), [0.0-0.1) [0.1-0.15), [0.15-0.2), [0.2-0.25), [0.25-0.3), [>0.3) 
 output format columns
 Cohort            N     Med%    Mean%    Win%   Sortino      PF
 analyze period: 2015-01-01 : 2026-06-26  
 save results in @docs/research/result-qullamaggie-tightrange-cohorts.md
 important files  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md

 could you analyze bk50d_s12_tr20_v1.2_roc100-366d, bk50d_s15_tr20_v1.2_roc100-366d, bk50d_s17_tr20_v1.2_roc100-366d, bk50d_s20_tr20_v1.2_roc100-366d algorithms
   in period 2007-01-01 : 2026-06-26
  and provide monthly Mean%, trade count by years
  and share your general findings and pros/cons of different algorithms  
Output format ->
 Year |    Jan    Feb    Mar    Apr    May    Jun    Jul    Aug    Sep    Oct    Nov    Dec |   Mean%    N
------------------------------------------------------------------------------------------------------------
 2007 |  +22.3   -4.5      ·      ·  +46.4      ·      ·  -31.4  -28.6  -39.1      ·      · |    -4.4   10
 2008 |      ·      ·      ·      ·      ·  +24.8  +19.7   +9.3  +32.2  +37.2   +1.7  +23.5 |   +20.3   61
 ...
and
 Year     N   Win%   Mean%    Med%  Sortino  CVaR95%
----------------------------------------------------
 2007    10   40.0   -4.45   -5.48   -0.093   -80.13
 2008    61   73.8  +20.26  +17.01    0.977   -33.40
 2009    61   73.8  +20.26  +17.01    0.977   -33.40
 ...
