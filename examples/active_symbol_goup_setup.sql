/*
setup an "active" ticker group based on criteria such as industry classification, 
average price, market cap, and trading volume. This group can be used for focused 
analysis or backtesting on a subset of actively traded stocks.
*/
select 'exchange', count(*) from turtle.exchange
union all
select 'company', count(*) from turtle.company
union all
select 'ticker', count(*) from turtle.ticker
union all
select 'ticker_group', count(*) from turtle.ticker_group
union all
select 'daily_bars', count(*) from turtle.daily_bars
;

select 'daily_bars', count(*), count(distinct symbol), min(date), max(date) from turtle.daily_bars;

insert into turtle.ticker_group 
  (select 'active'   as code
        , t.code     as ticker_code
        , null       as rate
     from turtle.ticker t
       inner join turtle.company c
               on c.ticker_code = t.code
    where c.industry is not null
      and c.average_price > 5.0
      and coalesce(c.market_cap,0) >= 10000000
      and coalesce(c.average_volume,0) >= 300000
);

insert into turtle.ticker_group (code, ticker_code, rate)
values  ('active', 'SPY.US', null),
        ('active', 'QQQ.US', null),
        ('active', 'XLV.US', NULL),                                                                                                                                                                                                                                 ('active', 'XLF.US', NULL),
        ('active', 'XLI.US', NULL),                                                                                                                                                                                                                                 ('active', 'XLK.US', NULL),
        ('active', 'XLY.US', NULL),
        ('active', 'XLC.US', NULL),
        ('active', 'XLB.US', NULL),
        ('active', 'XLE.US', NULL),
        ('active', 'XLRE.US', NULL),
        ('active', 'XLP.US', NULL),
        ('active', 'XLU.US', NULL)
  ON CONFLICT DO NOTHING;

select 'ticker_group', count(*) from turtle.ticker_group where code = 'active';

SELECT column_name FROM information_schema.columns
  WHERE table_schema = 'turtle' AND table_name = 'company'
  ORDER BY ordinal_position

select * from turtle.company;

select type, count(*)  from turtle.ticker t group by 1;

select count(*) from (
select t.code
   from turtle.ticker t
     inner join turtle.company c
             on c.ticker_code = t.code
  where t.type = 'Common Stock' 
    and c.sector is not null
union 
 select t.code 
   from turtle.ticker t 
  where t.code in ('SPY.US', 'QQQ.US', 'XLB.US', 'XLC.US', 'XLE.US', 'XLF.US', 'XLI.US', 'XLK.US', 'XLP.US', 'XLRE.US', 'XLU.US', 'XLV.US', 'XLY.US', 'XBI.US', 'XAR.US')
  );

select snapshot_date, count(*) from turtle.company_history group by 1 order by 1;


INSERT INTO turtle.ticker_group (code, ticker_code)
         VALUES ('lightyear','AVTR.US'),('lightyear','BULL.US'),('lightyear','DUOL.US'),('lightyear','GENI.US'),('lightyear','GDDY.US'),('lightyear','GTLB.US'),('lightyear','HNI.US'),('lightyear','PRGS.US'),('lightyear','SN.US')
         ON CONFLICT DO NOTHING;

select * from turtle.ticker_group where code = 'lightyear';

select * from turtle.lightyear_transaction lt ;
delete from turtle.lightyear_transaction lt ;

delete from turtle.job_runs;

select * from turtle.job_runs;


