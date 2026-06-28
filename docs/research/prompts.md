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

could you provide portfolio simulation bk50d_s20_tr10_v1.2_roc100-366d and bk50d_s15_tr15_v1.2_roc100-366d 
- period 2001-01-01 : 2026-06-26
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