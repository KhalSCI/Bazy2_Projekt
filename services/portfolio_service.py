"""
Portfolio management service.
"""

from typing import Optional, List, Dict, Tuple
from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import execute_query_dict
from db.queries import Queries
from db.procedures import Procedures


class PortfolioService:
    """Service for portfolio operations."""

    @staticmethod
    def get_user_portfolios(user_id: int) -> List[Dict]:
        """Get all portfolios for a user."""
        return execute_query_dict(
            Queries.GET_PORTFOLIOS_BY_USER,
            {'user_id': user_id}
        )

    @staticmethod
    def get_portfolio(portfolio_id: int) -> Optional[Dict]:
        """Get portfolio details by ID."""
        results = execute_query_dict(
            Queries.GET_PORTFOLIO_BY_ID,
            {'portfolio_id': portfolio_id}
        )
        return results[0] if results else None

    @staticmethod
    def get_portfolio_summary(portfolio_id: int) -> Optional[Dict]:
        """
        Get portfolio summary including positions value.

        Returns dict with:
        - portfolio_id, nazwa_portfela, saldo_gotowkowe, waluta_portfela
        - wartosc_pozycji, zysk_strata_pozycji, liczba_pozycji
        - wartosc_calkowita (calculated)
        """
        results = execute_query_dict(
            Queries.GET_PORTFOLIO_SUMMARY,
            {'portfolio_id': portfolio_id}
        )
        if not results:
            return None

        summary = results[0]
        # Calculate total value
        summary['wartosc_calkowita'] = (
            float(summary.get('saldo_gotowkowe', 0) or 0) +
            float(summary.get('wartosc_pozycji', 0) or 0)
        )
        return summary

    @staticmethod
    def get_positions(portfolio_id: int) -> List[Dict]:
        """Get all positions in a portfolio."""
        return execute_query_dict(
            Queries.GET_POSITIONS_BY_PORTFOLIO,
            {'portfolio_id': portfolio_id}
        )

    @staticmethod
    def get_position_by_instrument(portfolio_id: int, instrument_id: int) -> Optional[Dict]:
        """Get position for a specific instrument."""
        results = execute_query_dict(
            Queries.GET_POSITION_BY_INSTRUMENT,
            {'portfolio_id': portfolio_id, 'instrument_id': instrument_id}
        )
        return results[0] if results else None

    @staticmethod
    def get_portfolio_value(portfolio_id: int) -> float:
        """Get total portfolio value."""
        value = Procedures.get_portfolio_value(portfolio_id)
        return value if value is not None else 0.0

    @staticmethod
    def get_portfolio_value_for_date(portfolio_id: int, target_date: date) -> float:
        """Get portfolio value for a specific date (time travel)."""
        value = Procedures.get_portfolio_value_for_date(portfolio_id, target_date)
        return value if value is not None else 0.0

    @staticmethod
    def create_portfolio(user_id: int, name: str, currency: str,
                        initial_balance: float = 0) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new portfolio.

        Returns:
            Tuple of (success, message, portfolio_id)
        """
        return Procedures.create_portfolio(user_id, name, currency, initial_balance)

    @staticmethod
    def deposit_funds(portfolio_id: int, amount: float) -> Tuple[bool, str]:
        """Deposit funds to portfolio."""
        return Procedures.deposit_funds(portfolio_id, amount)

    @staticmethod
    def withdraw_funds(portfolio_id: int, amount: float) -> Tuple[bool, str]:
        """Withdraw funds from portfolio."""
        return Procedures.withdraw_funds(portfolio_id, amount)

    @staticmethod
    def update_positions(portfolio_id: int) -> Tuple[bool, str]:
        """Update all positions with current prices."""
        return Procedures.update_portfolio_positions(portfolio_id)

    @staticmethod
    def get_available_cash(portfolio_id: int) -> float:
        """Get available cash balance."""
        portfolio = PortfolioService.get_portfolio(portfolio_id)
        if portfolio:
            return float(portfolio.get('saldo_gotowkowe', 0) or 0)
        return 0.0

    @staticmethod
    def get_positions_for_date(portfolio_id: int, target_date: date) -> List[Dict]:
        """
        Get positions with values calculated for a specific date.
        Used for time travel feature.
        Only returns positions that existed at the target_date.
        """
        positions = PortfolioService.get_positions(portfolio_id)

        # Filter positions that existed at target_date
        filtered_positions = []
        for pos in positions:
            # Check if position existed at target_date
            data_pierwszego_zakupu = pos.get('data_pierwszego_zakupu')
            if data_pierwszego_zakupu:
                # Convert to date if datetime
                if hasattr(data_pierwszego_zakupu, 'date'):
                    data_pierwszego_zakupu = data_pierwszego_zakupu.date()

                # Skip positions that didn't exist yet at target_date
                if data_pierwszego_zakupu > target_date:
                    continue

            instrument_id = pos['instrument_id']
            price = Procedures.get_price_for_date(instrument_id, target_date)

            if price:
                ilosc = float(pos.get('ilosc_akcji', 0) or 0)
                srednia_cena = float(pos.get('srednia_cena_zakupu', 0) or 0)

                pos['cena_biezaca'] = price
                pos['wartosc_biezaca'] = round(ilosc * price, 2)
                pos['wartosc_zakupu'] = round(ilosc * srednia_cena, 2)
                pos['zysk_strata'] = round(ilosc * (price - srednia_cena), 2)

                if srednia_cena > 0:
                    pos['zysk_strata_procent'] = round(
                        ((price - srednia_cena) / srednia_cena) * 100, 2
                    )
                else:
                    pos['zysk_strata_procent'] = 0.0

                filtered_positions.append(pos)

        return filtered_positions


class UserService:
    """Service for user operations."""

    @staticmethod
    def get_user_by_login(login: str) -> Optional[Dict]:
        """Get user by login."""
        results = execute_query_dict(
            Queries.GET_USER_BY_LOGIN,
            {'login': login}
        )
        return results[0] if results else None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        results = execute_query_dict(
            Queries.GET_USER_BY_ID,
            {'user_id': user_id}
        )
        return results[0] if results else None

    @staticmethod
    def create_user(login: str, password: str, email: str,
                   first_name: str = None, last_name: str = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new user.

        Returns:
            Tuple of (success, message, user_id)
        """
        return Procedures.create_user(login, password, email, first_name, last_name)

    @staticmethod
    def verify_login(login: str, password: str) -> Optional[int]:
        """
        Verify user credentials.

        Returns:
            user_id if valid, None otherwise
        """
        return Procedures.verify_password(login, password)

    @staticmethod
    def authenticate(login: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user and return user data.

        Returns:
            Tuple of (success, message, user_data)
        """
        user_id = Procedures.verify_password(login, password)

        if user_id is None:
            return False, "Nieprawidłowy login lub hasło", None

        user = UserService.get_user_by_id(user_id)
        if user is None:
            return False, "Nie znaleziono użytkownika", None

        return True, "Zalogowano pomyślnie", user
