/*
setup an "active" ticker group based on criteria such as industry classification, 
average price, market cap, and trading volume. This group can be used for focused 
analysis or backtesting on a subset of actively traded stocks.
*/
select 'company', count(*) from turtle.company
union all
select 'ticker', count(*) from turtle.ticker;

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
        ('active', 'QQQ.US', null);

select 'ticker_group', count(*) from turtle.ticker_group where code = 'active';