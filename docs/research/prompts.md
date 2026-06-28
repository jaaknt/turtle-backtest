analyze bk50d_s15_tr15_v1.2_roc100 366d results in period 2001-01-01 : 2026-06-26
  - propose 5 options how to achieve ~3 signals per month
  - important is that Med% and Sortino must stay on the same level
  - the main idea is to loose currently applied filters. what filters conditions loosening affects the Mean%, Sortino less
  
could you analyze bk50d_s20_tr10_v1.2_roc100 366d, bk50d_s15_tr10_v1.2_roc100 366d, bk50d_s15_tr15_v1.2_roc100 366d
  in period 2001-01-01 : 2026-06-26
  and provide monthly Mean% by years
  and share your general findings and pros/cons of different algorithms  
  
could you propose rankig algorithm for  s15_tr15 trades that will select only trades with most potential based on technical data (ADR is higher, (SMA10, SMA20), <your discovery> ) 

run the backtest described in @docs/research/qullamaggie-backtest-v4.md

could you provide portfolio simulation bk50d_s20_tr10_v1.2_roc100-366d, bk50d_s15_tr15_v1.2_roc100-366d, bk50d_s15_tr10_v1.2_roc100-366d
important files  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md, @scripts/qullamaggie-portfolio-sim.py
- period 2010-01-01 : 2026-06-26
- initial portfolio amount 30000$
- invest {3%, 4%, 5%} of portfolio at the time per trade
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
- for top 3 algorithms print monthly returns by years (years are rows, months are columns)

could you provide bk50d_s20_tr10_v1.2_roc100 signals for period 2026-05-01 : 2026-06-26
 Date    │ Symbol │ Entry $ │ Curr Price | Change in % | %abv SMA50 │ ADR% │ RSI14 │ TR% │ ROC252% |

 could you provide bk50d_s15_tr15_v1.2_roc100 signals for period 2026-03-01 : 2026-06-26
 mark signals that are also in bk50d_s20_tr10_v1.2_roc100
 provide information to signals that are not in bk50d_s20_tr10_v1.2_roc100 list what was missing
 Date    │ Symbol │ Entry $ │ Curr Price | Change in % | %abv SMA50 │ ADR% │ RSI14 │ TR% │ ROC252% | 
 important files  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md

 could you analyze bk50d_s20_tr10_v1.2_roc100, bk50d_s15_tr15_v1.2_roc100 algorithms
 how  `roc_12m_cap`: `close[-1] / close[-253] − 1 < 100%` 
 cohorts (<20),  [-20-0), [0-20), [20-40), [40-60), [40-60), [60-80), [80-100), [100-120), [120-140), [140-160), [>160)
 output format columns
 N     Med%    Mean%    Win%  Sortino
 analyze period: 2015-01-01 : 2026-06-26  
 save results in @docs/research/result-qullamaggie-roc-cohorts.md
 important files  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md

 could you analyze bk50d_s20_tr10_v1.2_roc100, bk50d_s15_tr15_v1.2_roc100 algorithms
 how  `adr_pct`: `mean(high[-(21+1):-1] − low[-(21+1):-1]) / mean(close[-(21+1):-1])
 cohorts [0-1.0), [1.0-2.0), [2.0-2.5), [2.5-3.0), [3.0-3.5), [3.5-4.0), [4.0-4.5), [4.5-5.0), [5.0-7.0), (>8.0)  
 affect performance
 output format columns
 N     Med%    Mean%    Win%  Sortino
 analyze period: 2015-01-01 : 2026-06-26  
 save results in @docs/research/result-qullamaggie-adr-cohorts.md
 important files  @docs/research/qullamaggie-backtest-v4.md, @docs/research/result-qullamaggie-backtest-v4.md

 could you analyze bk50d_s20_tr10_v1.2_roc100, bk50d_s15_tr15_v1.2_roc100 algorithms
 how  `rsi_filter`: `RSI(14)
 cohorts [0-20), [20-40), [40-60), [40-50), [50-60), [60-70), [70-75), [75-80), [80-100]
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