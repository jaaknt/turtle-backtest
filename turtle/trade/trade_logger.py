"""Trade logging and audit trail for live trading operations."""

import json
import logging
from datetime import datetime, timedelta

import psycopg

from .models import LiveOrder, LivePosition, ExecutionReport, TradingSession

logger = logging.getLogger(__name__)


class TradeLogger:
    """Comprehensive trade logging and audit trail."""

    def __init__(self, db_dsn: str):
        """
        Initialize trade logger.

        Args:
            db_dsn: Database connection string
        """
        self.db_dsn = db_dsn
        logger.info("Trade logger initialized")

    def log_order_event(self, order: LiveOrder, event_message: str) -> None:
        """
        Log order-related event.

        Args:
            order: Order object
            event_message: Event description
        """
        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    # Update order in database
                    cur.execute("""
                        INSERT INTO turtle.live_orders (
                            id, client_order_id, ticker, side, order_type, quantity,
                            price, stop_price, time_in_force, status, created_at,
                            submitted_at, filled_at, filled_price, filled_quantity,
                            commission, signal_id, session_id
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (id) DO UPDATE SET
                            status = EXCLUDED.status,
                            filled_at = EXCLUDED.filled_at,
                            filled_price = EXCLUDED.filled_price,
                            filled_quantity = EXCLUDED.filled_quantity,
                            commission = EXCLUDED.commission,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        order.id,
                        order.client_order_id,
                        order.ticker,
                        order.side.value,
                        order.order_type.value,
                        order.quantity,
                        float(order.price) if order.price else None,
                        float(order.stop_price) if order.stop_price else None,
                        order.time_in_force,
                        order.status.value,
                        order.created_at,
                        order.submitted_at,
                        order.filled_at,
                        float(order.filled_price) if order.filled_price else None,
                        order.filled_quantity,
                        float(order.commission) if order.commission else None,
                        order.signal_id,
                        getattr(order, 'session_id', None)
                    ))

                    conn.commit()

            # Log event message
            logger.info(f"Order {order.id} ({order.ticker}): {event_message}")

        except Exception as e:
            logger.error(f"Error logging order event: {e}")

    def log_position_event(self, position: LivePosition, event_message: str) -> None:
        """
        Log position-related event.

        Args:
            position: Position object
            event_message: Event description
        """
        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    # Update position in database
                    cur.execute("""
                        INSERT INTO turtle.live_positions (
                            ticker, quantity, avg_price, market_price, cost_basis,
                            unrealized_pnl, entry_date, entry_signal_id,
                            stop_loss_order_id, take_profit_order_id, session_id
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (ticker, session_id) DO UPDATE SET
                            quantity = EXCLUDED.quantity,
                            avg_price = EXCLUDED.avg_price,
                            market_price = EXCLUDED.market_price,
                            cost_basis = EXCLUDED.cost_basis,
                            unrealized_pnl = EXCLUDED.unrealized_pnl,
                            stop_loss_order_id = EXCLUDED.stop_loss_order_id,
                            take_profit_order_id = EXCLUDED.take_profit_order_id,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        position.ticker,
                        position.quantity,
                        float(position.avg_price),
                        float(position.market_price),
                        float(position.cost_basis),
                        float(position.unrealized_pnl),
                        position.entry_date,
                        getattr(position.entry_signal, 'id', None) if position.entry_signal else None,
                        position.stop_loss_order_id,
                        position.take_profit_order_id,
                        getattr(position, 'session_id', None)
                    ))

                    conn.commit()

            # Log event message
            logger.info(f"Position {position.ticker}: {event_message}")

        except Exception as e:
            logger.error(f"Error logging position event: {e}")

    def log_execution(self, execution: ExecutionReport) -> None:
        """
        Log trade execution.

        Args:
            execution: Execution report
        """
        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO turtle.execution_reports (
                            execution_id, order_id, ticker, side, quantity,
                            price, timestamp, commission, liquidity, session_id
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (execution_id) DO NOTHING
                    """, (
                        execution.execution_id,
                        execution.order_id,
                        execution.ticker,
                        execution.side.value,
                        execution.quantity,
                        float(execution.price),
                        execution.timestamp,
                        float(execution.commission),
                        execution.liquidity,
                        getattr(execution, 'session_id', None)
                    ))

                    conn.commit()

            logger.info(f"Execution logged: {execution.ticker} {execution.side.value} {execution.quantity}@${execution.price}")

        except Exception as e:
            logger.error(f"Error logging execution: {e}")

    def log_session_event(self, session: TradingSession, event_message: str) -> None:
        """
        Log session-related event.

        Args:
            session: Trading session
            event_message: Event description
        """
        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    # Update session in database
                    cur.execute("""
                        INSERT INTO turtle.trading_sessions (
                            id, strategy_name, start_time, end_time, initial_balance,
                            current_balance, total_trades, winning_trades, losing_trades,
                            total_pnl, max_drawdown, is_active, paper_trading,
                            universe, risk_parameters
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (id) DO UPDATE SET
                            end_time = EXCLUDED.end_time,
                            current_balance = EXCLUDED.current_balance,
                            total_trades = EXCLUDED.total_trades,
                            winning_trades = EXCLUDED.winning_trades,
                            losing_trades = EXCLUDED.losing_trades,
                            total_pnl = EXCLUDED.total_pnl,
                            max_drawdown = EXCLUDED.max_drawdown,
                            is_active = EXCLUDED.is_active,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        session.id,
                        session.strategy_name,
                        session.start_time,
                        session.end_time,
                        float(session.initial_balance),
                        float(session.current_balance) if session.current_balance else None,
                        session.total_trades,
                        session.winning_trades,
                        session.losing_trades,
                        float(session.total_pnl),
                        float(session.max_drawdown),
                        session.is_active,
                        session.paper_trading,
                        json.dumps(session.universe),
                        json.dumps({})  # Risk parameters placeholder
                    ))

                    conn.commit()

            # Log event message
            logger.info(f"Session {session.id}: {event_message}")

        except Exception as e:
            logger.error(f"Error logging session event: {e}")

    def log_risk_event(
        self,
        session_id: str,
        event_type: str,
        severity: str,
        message: str,
        ticker: str | None = None,
        order_id: str | None = None,
        action_taken: str | None = None
    ) -> None:
        """
        Log risk management event.

        Args:
            session_id: Trading session ID
            event_type: Type of risk event
            severity: Event severity (low, medium, high, critical)
            message: Event description
            ticker: Related ticker (optional)
            order_id: Related order ID (optional)
            action_taken: Action taken in response (optional)
        """
        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO turtle.risk_events (
                            session_id, event_type, severity, message,
                            ticker, order_id, action_taken
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        session_id,
                        event_type,
                        severity,
                        message,
                        ticker,
                        order_id,
                        action_taken
                    ))

                    conn.commit()

            logger.warning(f"Risk event ({severity}): {event_type} - {message}")

        except Exception as e:
            logger.error(f"Error logging risk event: {e}")

    def log_account_snapshot(
        self,
        account_id: str,
        equity: float,
        cash: float,
        buying_power: float,
        portfolio_value: float,
        long_market_value: float = 0.0,
        short_market_value: float = 0.0,
        day_trade_count: int = 0,
        pattern_day_trader: bool = False,
        session_id: str | None = None
    ) -> None:
        """
        Log account snapshot.

        Args:
            account_id: Account identifier
            equity: Total account equity
            cash: Available cash
            buying_power: Available buying power
            portfolio_value: Total portfolio value
            long_market_value: Long positions value
            short_market_value: Short positions value
            day_trade_count: Day trade count
            pattern_day_trader: PDT status
            session_id: Trading session ID
        """
        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO turtle.account_snapshots (
                            account_id, snapshot_time, equity, cash, buying_power,
                            portfolio_value, long_market_value, short_market_value,
                            day_trade_count, pattern_day_trader, session_id
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON CONFLICT (account_id, snapshot_time, session_id) DO NOTHING
                    """, (
                        account_id,
                        datetime.now(),
                        equity,
                        cash,
                        buying_power,
                        portfolio_value,
                        long_market_value,
                        short_market_value,
                        day_trade_count,
                        pattern_day_trader,
                        session_id
                    ))

                    conn.commit()

            logger.debug(f"Account snapshot logged: equity=${equity}, cash=${cash}")

        except Exception as e:
            logger.error(f"Error logging account snapshot: {e}")

    def get_order_history(self, ticker: str | None = None, days: int = 30) -> list[dict]:
        """
        Get order history.

        Args:
            ticker: Filter by ticker (optional)
            days: Number of days to look back

        Returns:
            List of order history records
        """
        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT * FROM turtle.live_orders
                        WHERE created_at >= %s
                    """
                    params = [datetime.now() - timedelta(days=days)]

                    if ticker:
                        query += " AND ticker = %s"
                        params.append(ticker)

                    query += " ORDER BY created_at DESC"

                    cur.execute(query, params)
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    return [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Error getting order history: {e}")
            return []

    def get_execution_history(self, ticker: str | None = None, days: int = 30) -> list[dict]:
        """
        Get execution history.

        Args:
            ticker: Filter by ticker (optional)
            days: Number of days to look back

        Returns:
            List of execution history records
        """
        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT * FROM turtle.execution_reports
                        WHERE timestamp >= %s
                    """
                    params = [datetime.now() - timedelta(days=days)]

                    if ticker:
                        query += " AND ticker = %s"
                        params.append(ticker)

                    query += " ORDER BY timestamp DESC"

                    cur.execute(query, params)
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    return [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Error getting execution history: {e}")
            return []

    def get_risk_events(self, session_id: str, severity: str | None = None, days: int = 7) -> list[dict]:
        """
        Get risk events.

        Args:
            session_id: Trading session ID
            severity: Filter by severity (optional)
            days: Number of days to look back

        Returns:
            List of risk event records
        """
        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT * FROM turtle.risk_events
                        WHERE session_id = %s AND created_at >= %s
                    """
                    params = [session_id, datetime.now() - timedelta(days=days)]

                    if severity:
                        query += " AND severity = %s"
                        params.append(severity)

                    query += " ORDER BY created_at DESC"

                    cur.execute(query, params)
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    return [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Error getting risk events: {e}")
            return []

    def get_session_performance(self, session_id: str) -> dict:
        """
        Get session performance metrics.

        Args:
            session_id: Trading session ID

        Returns:
            Dictionary with performance metrics
        """
        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    # Get session info
                    cur.execute("""
                        SELECT * FROM turtle.trading_sessions WHERE id = %s
                    """, (session_id,))
                    session_row = cur.fetchone()

                    if not session_row:
                        return {}

                    session_columns = [desc[0] for desc in cur.description] if cur.description else []
                    session_data = dict(zip(session_columns, session_row, strict=False))

                    # Get execution summary
                    cur.execute("""
                        SELECT
                            COUNT(*) as total_executions,
                            SUM(CASE WHEN side = 'buy' THEN quantity ELSE 0 END) as total_bought,
                            SUM(CASE WHEN side = 'sell' THEN quantity ELSE 0 END) as total_sold,
                            SUM(price * quantity) as total_volume,
                            SUM(commission) as total_commission
                        FROM turtle.execution_reports
                        WHERE session_id = %s
                    """, (session_id,))
                    exec_row = cur.fetchone()

                    if exec_row:
                        exec_columns = [desc[0] for desc in cur.description] if cur.description else []
                        exec_data = dict(zip(exec_columns, exec_row, strict=False))
                        session_data.update(exec_data)

                    # Get risk summary
                    cur.execute("""
                        SELECT
                            COUNT(*) as total_risk_events,
                            SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_events,
                            SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high_events,
                            SUM(CASE WHEN resolved = true THEN 1 ELSE 0 END) as resolved_events
                        FROM turtle.risk_events
                        WHERE session_id = %s
                    """, (session_id,))
                    risk_row = cur.fetchone()

                    if risk_row:
                        risk_columns = [desc[0] for desc in cur.description] if cur.description else []
                        risk_data = dict(zip(risk_columns, risk_row, strict=False))
                        session_data.update(risk_data)

                    return session_data

        except Exception as e:
            logger.error(f"Error getting session performance: {e}")
            return {}

    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Clean up old trading data.

        Args:
            days_to_keep: Number of days of data to keep

        Returns:
            Number of records cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        total_cleaned = 0

        try:
            with psycopg.connect(self.db_dsn) as conn:
                with conn.cursor() as cur:
                    # Clean up old orders
                    cur.execute("""
                        DELETE FROM turtle.live_orders
                        WHERE created_at < %s
                    """, (cutoff_date,))
                    orders_cleaned = cur.rowcount

                    # Clean up old executions
                    cur.execute("""
                        DELETE FROM turtle.execution_reports
                        WHERE timestamp < %s
                    """, (cutoff_date,))
                    executions_cleaned = cur.rowcount

                    # Clean up old account snapshots
                    cur.execute("""
                        DELETE FROM turtle.account_snapshots
                        WHERE snapshot_time < %s
                    """, (cutoff_date,))
                    snapshots_cleaned = cur.rowcount

                    # Clean up old risk events
                    cur.execute("""
                        DELETE FROM turtle.risk_events
                        WHERE created_at < %s AND resolved = true
                    """, (cutoff_date,))
                    events_cleaned = cur.rowcount

                    conn.commit()
                    total_cleaned = orders_cleaned + executions_cleaned + snapshots_cleaned + events_cleaned

            logger.info(f"Cleaned up {total_cleaned} old records (>{days_to_keep} days)")
            return total_cleaned

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
