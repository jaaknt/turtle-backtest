-- Live Trading Database Schema Extensions
-- This file extends the existing turtle schema with live trading tables

-- Table for storing live orders
CREATE TABLE IF NOT EXISTS turtle.live_orders (
    id varchar(50) NOT NULL,                          -- Alpaca order ID
    client_order_id varchar(50),                      -- Client-side order ID
    ticker varchar(20) NOT NULL,                      -- Stock symbol
    side varchar(10) NOT NULL,                        -- buy/sell
    order_type varchar(20) NOT NULL,                  -- market/limit/stop/etc
    quantity integer NOT NULL,                        -- Number of shares
    price numeric(15,6),                             -- Order price (for limit orders)
    stop_price numeric(15,6),                        -- Stop price (for stop orders)
    time_in_force varchar(10) NOT NULL DEFAULT 'day', -- Order duration
    status varchar(20) NOT NULL,                      -- Order status
    created_at timestamp without time zone NOT NULL,   -- Order creation time
    submitted_at timestamp without time zone,          -- Order submission time
    filled_at timestamp without time zone,             -- Order fill time
    filled_price numeric(15,6),                       -- Actual fill price
    filled_quantity integer,                          -- Number of shares filled
    commission numeric(15,6),                         -- Commission paid
    signal_id varchar(50),                            -- Associated signal ID
    session_id varchar(50),                           -- Trading session ID
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_live_orders PRIMARY KEY (id)
);

-- Table for storing live positions
CREATE TABLE IF NOT EXISTS turtle.live_positions (
    ticker varchar(20) NOT NULL,                      -- Stock symbol
    quantity integer NOT NULL,                        -- Number of shares (positive=long, negative=short)
    avg_price numeric(15,6) NOT NULL,                -- Average cost basis
    market_price numeric(15,6) NOT NULL,             -- Current market price
    cost_basis numeric(15,6) NOT NULL,               -- Total cost basis
    unrealized_pnl numeric(15,6) NOT NULL DEFAULT 0,  -- Unrealized P&L
    entry_date timestamp without time zone NOT NULL,   -- Position entry date
    entry_signal_id varchar(50),                      -- Signal that initiated position
    stop_loss_order_id varchar(50),                   -- Associated stop loss order
    take_profit_order_id varchar(50),                 -- Associated take profit order
    session_id varchar(50),                           -- Trading session ID
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_live_positions PRIMARY KEY (ticker, session_id)
);

-- Table for storing trading sessions
CREATE TABLE IF NOT EXISTS turtle.trading_sessions (
    id varchar(50) NOT NULL,                          -- Unique session identifier
    strategy_name varchar(100) NOT NULL,              -- Trading strategy used
    start_time timestamp without time zone NOT NULL,   -- Session start time
    end_time timestamp without time zone,              -- Session end time (NULL if active)
    initial_balance numeric(15,2) NOT NULL,           -- Starting account balance
    current_balance numeric(15,2),                    -- Current account balance
    total_trades integer NOT NULL DEFAULT 0,          -- Total number of trades
    winning_trades integer NOT NULL DEFAULT 0,        -- Number of winning trades
    losing_trades integer NOT NULL DEFAULT 0,         -- Number of losing trades
    total_pnl numeric(15,2) NOT NULL DEFAULT 0,      -- Total realized P&L
    max_drawdown numeric(15,2) NOT NULL DEFAULT 0,   -- Maximum drawdown
    is_active boolean NOT NULL DEFAULT true,          -- Whether session is active
    paper_trading boolean NOT NULL DEFAULT true,      -- Whether using paper trading
    universe text,                                    -- JSON array of symbols being traded
    risk_parameters text,                             -- JSON of risk parameters
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_trading_sessions PRIMARY KEY (id)
);

-- Table for storing execution reports
CREATE TABLE IF NOT EXISTS turtle.execution_reports (
    execution_id varchar(50) NOT NULL,                -- Unique execution identifier
    order_id varchar(50) NOT NULL,                    -- Order identifier
    ticker varchar(20) NOT NULL,                      -- Stock symbol
    side varchar(10) NOT NULL,                        -- buy/sell
    quantity integer NOT NULL,                        -- Number of shares executed
    price numeric(15,6) NOT NULL,                    -- Execution price
    timestamp timestamp without time zone NOT NULL,   -- Execution timestamp
    commission numeric(15,6) NOT NULL DEFAULT 0,     -- Commission paid
    liquidity varchar(10),                           -- Liquidity indicator
    session_id varchar(50),                          -- Trading session ID
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_execution_reports PRIMARY KEY (execution_id)
);

-- Table for storing account snapshots
CREATE TABLE IF NOT EXISTS turtle.account_snapshots (
    id serial PRIMARY KEY,
    account_id varchar(50) NOT NULL,                  -- Account identifier
    snapshot_time timestamp without time zone NOT NULL, -- Snapshot timestamp
    equity numeric(15,2) NOT NULL,                   -- Total account equity
    cash numeric(15,2) NOT NULL,                     -- Available cash
    buying_power numeric(15,2) NOT NULL,             -- Available buying power
    portfolio_value numeric(15,2) NOT NULL,          -- Total portfolio value
    long_market_value numeric(15,2) NOT NULL DEFAULT 0, -- Long positions value
    short_market_value numeric(15,2) NOT NULL DEFAULT 0, -- Short positions value
    day_trade_count integer NOT NULL DEFAULT 0,      -- Day trade count
    pattern_day_trader boolean NOT NULL DEFAULT false, -- PDT status
    session_id varchar(50),                          -- Trading session ID
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_account_snapshots_time UNIQUE (account_id, snapshot_time, session_id)
);

-- Table for storing risk events and alerts
CREATE TABLE IF NOT EXISTS turtle.risk_events (
    id serial PRIMARY KEY,
    session_id varchar(50) NOT NULL,                 -- Trading session ID
    event_type varchar(50) NOT NULL,                 -- Type of risk event
    severity varchar(20) NOT NULL,                   -- low/medium/high/critical
    message text NOT NULL,                          -- Event description
    ticker varchar(20),                             -- Related ticker (if applicable)
    order_id varchar(50),                           -- Related order (if applicable)
    action_taken varchar(100),                      -- Action taken in response
    resolved boolean NOT NULL DEFAULT false,        -- Whether event is resolved
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at timestamp without time zone
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_live_orders_ticker_status ON turtle.live_orders(ticker, status);
CREATE INDEX IF NOT EXISTS idx_live_orders_session ON turtle.live_orders(session_id);
CREATE INDEX IF NOT EXISTS idx_live_orders_created_at ON turtle.live_orders(created_at);

CREATE INDEX IF NOT EXISTS idx_live_positions_session ON turtle.live_positions(session_id);
CREATE INDEX IF NOT EXISTS idx_live_positions_updated_at ON turtle.live_positions(updated_at);

CREATE INDEX IF NOT EXISTS idx_trading_sessions_active ON turtle.trading_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_trading_sessions_start_time ON turtle.trading_sessions(start_time);

CREATE INDEX IF NOT EXISTS idx_execution_reports_order ON turtle.execution_reports(order_id);
CREATE INDEX IF NOT EXISTS idx_execution_reports_timestamp ON turtle.execution_reports(timestamp);
CREATE INDEX IF NOT EXISTS idx_execution_reports_session ON turtle.execution_reports(session_id);

CREATE INDEX IF NOT EXISTS idx_account_snapshots_time ON turtle.account_snapshots(snapshot_time);
CREATE INDEX IF NOT EXISTS idx_account_snapshots_session ON turtle.account_snapshots(session_id);

CREATE INDEX IF NOT EXISTS idx_risk_events_session ON turtle.risk_events(session_id);
CREATE INDEX IF NOT EXISTS idx_risk_events_severity ON turtle.risk_events(severity, resolved);
CREATE INDEX IF NOT EXISTS idx_risk_events_created_at ON turtle.risk_events(created_at);

-- Foreign key constraints (referential integrity)
ALTER TABLE turtle.live_orders
ADD CONSTRAINT fk_live_orders_session
FOREIGN KEY (session_id) REFERENCES turtle.trading_sessions(id) ON DELETE CASCADE;

ALTER TABLE turtle.live_positions
ADD CONSTRAINT fk_live_positions_session
FOREIGN KEY (session_id) REFERENCES turtle.trading_sessions(id) ON DELETE CASCADE;

ALTER TABLE turtle.execution_reports
ADD CONSTRAINT fk_execution_reports_session
FOREIGN KEY (session_id) REFERENCES turtle.trading_sessions(id) ON DELETE CASCADE;

ALTER TABLE turtle.account_snapshots
ADD CONSTRAINT fk_account_snapshots_session
FOREIGN KEY (session_id) REFERENCES turtle.trading_sessions(id) ON DELETE CASCADE;

ALTER TABLE turtle.risk_events
ADD CONSTRAINT fk_risk_events_session
FOREIGN KEY (session_id) REFERENCES turtle.trading_sessions(id) ON DELETE CASCADE;

-- Triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
DROP TRIGGER IF EXISTS update_live_orders_modtime ON turtle.live_orders;
CREATE TRIGGER update_live_orders_modtime
    BEFORE UPDATE ON turtle.live_orders
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_live_positions_modtime ON turtle.live_positions;
CREATE TRIGGER update_live_positions_modtime
    BEFORE UPDATE ON turtle.live_positions
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

DROP TRIGGER IF EXISTS update_trading_sessions_modtime ON turtle.trading_sessions;
CREATE TRIGGER update_trading_sessions_modtime
    BEFORE UPDATE ON turtle.trading_sessions
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();