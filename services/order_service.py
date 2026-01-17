"""
Order management service.
"""

from typing import Optional, List, Dict, Tuple
from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import execute_query_dict
from db.queries import Queries
from db.procedures import Procedures, create_and_execute_market_order
from config import APP_CONFIG


class OrderService:
    """Service for order operations."""

    @staticmethod
    def get_orders_by_portfolio(portfolio_id: int) -> List[Dict]:
        """Get all orders for a portfolio."""
        return execute_query_dict(
            Queries.GET_ORDERS_BY_PORTFOLIO,
            {'portfolio_id': portfolio_id}
        )

    @staticmethod
    def get_pending_orders(portfolio_id: int) -> List[Dict]:
        """Get pending orders for a portfolio."""
        return execute_query_dict(
            Queries.GET_PENDING_ORDERS,
            {'portfolio_id': portfolio_id}
        )

    @staticmethod
    def get_executed_orders(portfolio_id: int) -> List[Dict]:
        """Get executed orders for a portfolio."""
        return execute_query_dict(
            Queries.GET_EXECUTED_ORDERS,
            {'portfolio_id': portfolio_id}
        )

    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[Dict]:
        """Get order details by ID."""
        results = execute_query_dict(
            Queries.GET_ORDER_BY_ID,
            {'order_id': order_id}
        )
        return results[0] if results else None

    @staticmethod
    def create_order(portfolio_id: int, instrument_id: int, order_type: str,
                    order_side: str, quantity: float, limit_price: float = None,
                    expiration_date: date = None, order_date: date = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new order.

        Args:
            portfolio_id: Portfolio ID
            instrument_id: Instrument ID
            order_type: 'MARKET' or 'LIMIT'
            order_side: 'KUPNO' or 'SPRZEDAZ'
            quantity: Number of shares
            limit_price: Price limit for LIMIT orders
            expiration_date: Order expiration date
            order_date: Order creation date (simulation date)

        Returns:
            Tuple of (success, message, order_id)
        """
        from datetime import datetime
        order_datetime = datetime.combine(order_date, datetime.min.time()) if order_date else None
        return Procedures.create_order(
            portfolio_id, instrument_id, order_type, order_side,
            quantity, limit_price, expiration_date, order_datetime
        )

    @staticmethod
    def create_and_execute_buy(portfolio_id: int, instrument_id: int,
                               quantity: float, price: float, order_date: date = None) -> Tuple[bool, str]:
        """
        Create and immediately execute a market buy order.

        Args:
            order_date: Order creation date (simulation date)

        Returns:
            Tuple of (success, message)
        """
        from datetime import datetime
        order_datetime = datetime.combine(order_date, datetime.min.time()) if order_date else None
        return create_and_execute_market_order(
            portfolio_id, instrument_id, 'KUPNO', quantity, price, order_datetime
        )

    @staticmethod
    def create_and_execute_sell(portfolio_id: int, instrument_id: int,
                                quantity: float, price: float, order_date: date = None) -> Tuple[bool, str]:
        """
        Create and immediately execute a market sell order.

        Args:
            order_date: Order creation date (simulation date)

        Returns:
            Tuple of (success, message)
        """
        from datetime import datetime
        order_datetime = datetime.combine(order_date, datetime.min.time()) if order_date else None
        return create_and_execute_market_order(
            portfolio_id, instrument_id, 'SPRZEDAZ', quantity, price, order_datetime
        )

    @staticmethod
    def create_limit_buy(portfolio_id: int, instrument_id: int,
                        quantity: float, limit_price: float,
                        expiration_date: date = None, order_date: date = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a limit buy order.

        Args:
            order_date: Order creation date (simulation date)

        Returns:
            Tuple of (success, message, order_id)
        """
        from datetime import datetime
        order_datetime = datetime.combine(order_date, datetime.min.time()) if order_date else None
        return Procedures.create_order(
            portfolio_id, instrument_id, 'LIMIT', 'KUPNO',
            quantity, limit_price, expiration_date, order_datetime
        )

    @staticmethod
    def create_limit_sell(portfolio_id: int, instrument_id: int,
                         quantity: float, limit_price: float,
                         expiration_date: date = None, order_date: date = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a limit sell order.

        Args:
            order_date: Order creation date (simulation date)

        Returns:
            Tuple of (success, message, order_id)
        """
        from datetime import datetime
        order_datetime = datetime.combine(order_date, datetime.min.time()) if order_date else None
        return Procedures.create_order(
            portfolio_id, instrument_id, 'LIMIT', 'SPRZEDAZ',
            quantity, limit_price, expiration_date, order_datetime
        )

    @staticmethod
    def cancel_order(order_id: int) -> Tuple[bool, str]:
        """
        Cancel a pending order.

        Returns:
            Tuple of (success, message)
        """
        return Procedures.cancel_order(order_id)

    @staticmethod
    def process_limit_orders(portfolio_id: int, simulation_date: date) -> Tuple[bool, str]:
        """
        Process all pending limit orders for a portfolio.

        Returns:
            Tuple of (success, message)
        """
        return Procedures.process_limit_orders(portfolio_id, simulation_date)

    @staticmethod
    def calculate_order_cost(quantity: float, price: float,
                            commission_rate: float = None) -> Dict:
        """
        Calculate the total cost for a buy order.

        Returns dict with:
        - wartosc: Base value
        - prowizja: Commission
        - koszt_calkowity: Total cost
        """
        if commission_rate is None:
            commission_rate = APP_CONFIG['commission_rate']

        wartosc = quantity * price
        prowizja = Procedures.calculate_commission(wartosc, commission_rate)
        koszt_calkowity = wartosc + prowizja

        return {
            'wartosc': round(wartosc, 2),
            'prowizja': round(prowizja, 2),
            'koszt_calkowity': round(koszt_calkowity, 2)
        }

    @staticmethod
    def calculate_order_proceeds(quantity: float, price: float,
                                 commission_rate: float = None) -> Dict:
        """
        Calculate the net proceeds for a sell order.

        Returns dict with:
        - wartosc: Base value
        - prowizja: Commission
        - przychod_netto: Net proceeds
        """
        if commission_rate is None:
            commission_rate = APP_CONFIG['commission_rate']

        wartosc = quantity * price
        prowizja = Procedures.calculate_commission(wartosc, commission_rate)
        przychod_netto = wartosc - prowizja

        return {
            'wartosc': round(wartosc, 2),
            'prowizja': round(prowizja, 2),
            'przychod_netto': round(przychod_netto, 2)
        }

    @staticmethod
    def has_pending_limit_orders(portfolio_id: int) -> bool:
        """Check if portfolio has any pending LIMIT orders."""
        pending = OrderService.get_pending_orders(portfolio_id)
        return any(o.get('typ_zlecenia') == 'LIMIT' for o in pending)

    @staticmethod
    def process_limit_orders_for_range(portfolio_id: int, old_date: date, new_date: date) -> Tuple[int, List[str]]:
        """
        Process limit orders for all trading days between old_date and new_date.

        Only processes forward in time (can't un-execute orders).
        Stops early if no more pending LIMIT orders exist.

        Args:
            portfolio_id: Portfolio ID
            old_date: Previous simulation date
            new_date: New simulation date

        Returns:
            Tuple of (executed_count, messages)
        """
        from services.market_service import MarketService

        messages = []
        executed_count = 0

        # Only process forward in time
        if new_date <= old_date:
            return 0, []

        # Get trading days between dates
        trading_days = MarketService.get_trading_days_between(old_date, new_date)

        if not trading_days:
            return 0, []

        # Process each trading day
        for day in trading_days:
            # Check if there are still pending LIMIT orders
            if not OrderService.has_pending_limit_orders(portfolio_id):
                break

            # Process limit orders for this day
            success, message = OrderService.process_limit_orders(portfolio_id, day)

            if success and message and "wykonano" in message.lower():
                # Extract execution info from message
                messages.append(f"{day}: {message}")
                executed_count += 1

        return executed_count, messages


class TransactionService:
    """Service for transaction history."""

    @staticmethod
    def get_transactions_by_portfolio(portfolio_id: int) -> List[Dict]:
        """Get all transactions for a portfolio."""
        return execute_query_dict(
            Queries.GET_TRANSACTIONS_BY_PORTFOLIO,
            {'portfolio_id': portfolio_id}
        )

    @staticmethod
    def get_transactions_by_date_range(portfolio_id: int,
                                       start_date: date,
                                       end_date: date) -> List[Dict]:
        """Get transactions within a date range."""
        return execute_query_dict(
            Queries.GET_TRANSACTIONS_BY_DATE_RANGE,
            {
                'portfolio_id': portfolio_id,
                'start_date': start_date,
                'end_date': end_date
            }
        )
