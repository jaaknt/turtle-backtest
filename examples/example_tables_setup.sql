/*
How TO setup configuration tables AFTER download
Only tickers/companies with status='ACTIVE' will participate in setup search
*/

-- initial setup: set all records are in ACTIVE state
update turtle.ticker
   set status = 'ACTIVE',
       reason_code = NULL;

-- fix EODHD data problem      
update turtle.ticker
   set status = 'NON-ACTIVE',
       reason_code = 'invalid-symbol'
 where status = 'ACTIVE'
   and symbol like ('%old');            

-- set companies in NON-ACTIVE state if average price is < 5.00$  
update turtle.ticker
   set status = 'NON-ACTIVE',
       reason_code = 'price-less-than-5'
 where status = 'ACTIVE'
   and symbol in (select symbol 
                    from turtle.company
                   where coalesce(avg_price,0) < 5);       

-- set companies in NON-ACTIVE state if market cap < 1M                   
update turtle.ticker
   set status = 'NON-ACTIVE',
       reason_code = 'market-cap-less-than-1M'
 where status = 'ACTIVE'
   and symbol in (select symbol 
                    from turtle.company
                   where coalesce(market_cap,0) < 1000000);       

-- set companies in NON-ACTIVE state if average volume < 300000                  
update turtle.ticker
   set status = 'NON-ACTIVE',
       reason_code = 'avg-volume-less-than-0.3M'
 where status = 'ACTIVE'
   and symbol in (select symbol 
                    from turtle.company
                   where coalesce(avg_volume,0) < 300000);                         

-- statistics
select status, reason_code, count(*)
  from turtle.ticker
  group by 1,2
  order by 1,2;

ACTIVE		                            2206
NON-ACTIVE	avg-volume-less-than-0.3M	1777
NON-ACTIVE	market-cap-less-than-1M	     293
NON-ACTIVE	price-less-than-5	        2394 
 
                  