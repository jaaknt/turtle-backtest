CREATE SCHEMA IF NOT EXISTS turtle;

CREATE TABLE IF NOT EXISTS turtle.ticker(
    symbol          varchar(20) NOT NULL,
    "name"          text        NOT NULL,
    exchange        varchar(20) NOT NULL,
    country         varchar(3),
    currency        varchar(3),
    isin            varchar(30),
    symbol_type     varchar(20) NOT NULL,
    source          varchar(20) NOT NULL,
    created_at      timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at     timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_ticker PRIMARY KEY (symbol)
);

CREATE TABLE IF NOT EXISTS turtle.bars_history(
    symbol          varchar(20) NOT NULL,
    hdate           date        NOT NULL,
    open            numeric(12,6),
    high            numeric(12,6),
    low             numeric(12,6),
    close           numeric(12,6),
    volume          bigint,
    trade_count     bigint,
    source          varchar(20) NOT NULL,
    created_at      timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at     timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_bars_history PRIMARY KEY (symbol, hdate)
);

CREATE TABLE IF NOT EXISTS turtle.company(
    symbol          varchar(20) NOT NULL,
    short_name      text,
    country         varchar(50),
    industry_code   varchar(50),
    sector_code     varchar(50),
    employees_count bigint,
    dividend_rate   numeric(12,6),
    trailing_pe_ratio numeric(12,6),
    forward_pe_ratio numeric(12,6),
    avg_volume      bigint,  
    market_cap      bigint,
    enterprice_value bigint,
    short_ratio     numeric(12,6),
    peg_ratio       numeric(12,6),
    recommodation_mean numeric(12,6),
    number_of_analysyst bigint,
    roa_value       numeric(12,6),
    roe_value       numeric(12,6),  
    source          varchar(20) NOT NULL,
    created_at      timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at     timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_company PRIMARY KEY (symbol)
);
