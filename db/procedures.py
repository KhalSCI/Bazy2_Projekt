"""
Python wrappers for Oracle PL/SQL procedures.
Handles error translation to Polish user-friendly messages.
"""

import oracledb
from typing import Optional, Tuple
from datetime import date, datetime
from .connection import get_db_connection, get_db_cursor, call_function


# Error code to Polish message mapping
ERROR_MESSAGES = {
    20001: "Błąd podczas obliczania wartości portfela",
    20002: "Błąd podczas pobierania ceny instrumentu",
    20003: "Błąd podczas aktualizacji pozycji",
    1: "Naruszenie unikalności - rekord już istnieje",
    1400: "Wartość nie może być pusta",
    2291: "Nieprawidłowe odwołanie - powiązany rekord nie istnieje",
    2292: "Nie można usunąć - istnieją powiązane rekordy",
}


def translate_oracle_error(error: oracledb.Error) -> str:
    """Translate Oracle error to Polish user-friendly message."""
    try:
        error_obj, = error.args
        code = error_obj.code
        if code in ERROR_MESSAGES:
            return ERROR_MESSAGES[code]
        return f"Błąd bazy danych: {error_obj.message}"
    except Exception:
        return f"Nieoczekiwany błąd: {str(error)}"


def parse_result(result: str) -> Tuple[bool, str]:
    """
    Parse procedure result string.

    Returns:
        Tuple of (success, message)
    """
    if result is None:
        return False, "Brak odpowiedzi z bazy danych"
    if result.startswith('OK:'):
        return True, result[4:].strip()
    elif result.startswith('BŁĄD:'):
        return False, result[6:].strip()
    else:
        return False, result


class Procedures:
    """Wrapper class for Oracle PL/SQL procedures."""

    # =========================================
    # USER PROCEDURES
    # =========================================

    @staticmethod
    def create_user(login: str, password: str, email: str,
                    first_name: str = None, last_name: str = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new user.

        Returns:
            Tuple of (success, message, user_id)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                user_id = cursor.var(oracledb.NUMBER)
                result = cursor.var(oracledb.STRING, 500)

                cursor.callproc('pkg_gielda_ext.utworz_uzytkownika', [
                    login, password, email, first_name, last_name,
                    user_id, result
                ])

                success, message = parse_result(result.getvalue())
                return success, message, int(user_id.getvalue()) if user_id.getvalue() else None

        except oracledb.Error as e:
            return False, translate_oracle_error(e), None

    @staticmethod
    def verify_password(login: str, password: str) -> Optional[int]:
        """
        Verify user password.

        Returns:
            user_id if credentials are valid, None otherwise
        """
        try:
            result = call_function(
                'pkg_gielda_ext.weryfikuj_haslo',
                oracledb.NUMBER,
                [login, password]
            )
            return int(result) if result else None
        except oracledb.Error:
            return None

    # =========================================
    # PORTFOLIO PROCEDURES
    # =========================================

    @staticmethod
    def create_portfolio(user_id: int, name: str, currency: str,
                        initial_balance: float = 0) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new portfolio.

        Returns:
            Tuple of (success, message, portfolio_id)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                portfolio_id = cursor.var(oracledb.NUMBER)
                result = cursor.var(oracledb.STRING, 500)

                cursor.callproc('pkg_gielda_ext.utworz_portfel', [
                    user_id, name, currency, initial_balance,
                    portfolio_id, result
                ])

                success, message = parse_result(result.getvalue())
                return success, message, int(portfolio_id.getvalue()) if portfolio_id.getvalue() else None

        except oracledb.Error as e:
            return False, translate_oracle_error(e), None

    @staticmethod
    def deposit_funds(portfolio_id: int, amount: float) -> Tuple[bool, str]:
        """
        Deposit funds to portfolio.

        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                result = cursor.var(oracledb.STRING, 500)

                cursor.callproc('pkg_gielda.wplac_srodki', [
                    portfolio_id, amount, result
                ])

                return parse_result(result.getvalue())

        except oracledb.Error as e:
            return False, translate_oracle_error(e)

    @staticmethod
    def withdraw_funds(portfolio_id: int, amount: float) -> Tuple[bool, str]:
        """
        Withdraw funds from portfolio.

        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                result = cursor.var(oracledb.STRING, 500)

                cursor.callproc('pkg_gielda_ext.wyplac_srodki', [
                    portfolio_id, amount, result
                ])

                return parse_result(result.getvalue())

        except oracledb.Error as e:
            return False, translate_oracle_error(e)

    @staticmethod
    def update_portfolio_positions(portfolio_id: int) -> Tuple[bool, str]:
        """
        Update all positions in portfolio with current prices.

        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.callproc('pkg_gielda.aktualizuj_pozycje_portfela', [portfolio_id])
                return True, "Pozycje zaktualizowane"

        except oracledb.Error as e:
            return False, translate_oracle_error(e)

    @staticmethod
    def get_portfolio_value(portfolio_id: int) -> Optional[float]:
        """
        Get total portfolio value (cash + positions).

        Returns:
            Portfolio value or None on error
        """
        try:
            result = call_function(
                'pkg_gielda.oblicz_wartosc_portfela',
                oracledb.NUMBER,
                [portfolio_id]
            )
            return float(result) if result else 0.0
        except oracledb.Error:
            return None

    @staticmethod
    def get_portfolio_value_for_date(portfolio_id: int, simulation_date: date) -> Optional[float]:
        """
        Get portfolio value for a specific date (time travel).

        Returns:
            Portfolio value or None on error
        """
        try:
            result = call_function(
                'pkg_gielda_ext.oblicz_wartosc_portfela_dla_daty',
                oracledb.NUMBER,
                [portfolio_id, simulation_date]
            )
            return float(result) if result else 0.0
        except oracledb.Error:
            return None

    # =========================================
    # ORDER PROCEDURES
    # =========================================

    @staticmethod
    def create_order(portfolio_id: int, instrument_id: int, order_type: str,
                     order_side: str, quantity: float, limit_price: float = None,
                     expiration_date: date = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new order.

        Args:
            portfolio_id: Portfolio ID
            instrument_id: Instrument ID
            order_type: 'MARKET', 'LIMIT', or 'STOP'
            order_side: 'KUPNO' or 'SPRZEDAZ'
            quantity: Number of shares
            limit_price: Price limit for LIMIT orders
            expiration_date: Order expiration date

        Returns:
            Tuple of (success, message, order_id)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                order_id = cursor.var(oracledb.NUMBER)
                result = cursor.var(oracledb.STRING, 500)

                cursor.callproc('pkg_gielda_ext.utworz_zlecenie', [
                    portfolio_id, instrument_id, order_type, order_side,
                    quantity, limit_price, expiration_date,
                    order_id, result
                ])

                success, message = parse_result(result.getvalue())
                return success, message, int(order_id.getvalue()) if order_id.getvalue() else None

        except oracledb.Error as e:
            return False, translate_oracle_error(e), None

    @staticmethod
    def execute_buy_order(order_id: int, execution_price: float) -> Tuple[bool, str]:
        """
        Execute a pending buy order.

        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                result = cursor.var(oracledb.STRING, 500)

                cursor.callproc('pkg_gielda.wykonaj_zlecenie_kupna', [
                    order_id, execution_price, result
                ])

                return parse_result(result.getvalue())

        except oracledb.Error as e:
            return False, translate_oracle_error(e)

    @staticmethod
    def execute_sell_order(order_id: int, execution_price: float) -> Tuple[bool, str]:
        """
        Execute a pending sell order.

        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                result = cursor.var(oracledb.STRING, 500)

                cursor.callproc('pkg_gielda.wykonaj_zlecenie_sprzedazy', [
                    order_id, execution_price, result
                ])

                return parse_result(result.getvalue())

        except oracledb.Error as e:
            return False, translate_oracle_error(e)

    @staticmethod
    def cancel_order(order_id: int) -> Tuple[bool, str]:
        """
        Cancel a pending order.

        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                result = cursor.var(oracledb.STRING, 500)

                cursor.callproc('pkg_gielda_ext.anuluj_zlecenie', [
                    order_id, result
                ])

                return parse_result(result.getvalue())

        except oracledb.Error as e:
            return False, translate_oracle_error(e)

    @staticmethod
    def process_limit_orders(portfolio_id: int, simulation_date: date) -> Tuple[bool, str]:
        """
        Process all pending limit orders for a portfolio.

        Returns:
            Tuple of (success, message)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                result = cursor.var(oracledb.STRING, 500)

                cursor.callproc('pkg_gielda_ext.przetworz_zlecenia_limit', [
                    portfolio_id, simulation_date, result
                ])

                return parse_result(result.getvalue())

        except oracledb.Error as e:
            return False, translate_oracle_error(e)

    # =========================================
    # PRICE FUNCTIONS
    # =========================================

    @staticmethod
    def get_current_price(instrument_id: int) -> Optional[float]:
        """
        Get current (latest) price for an instrument.

        Returns:
            Current price or None if not available
        """
        try:
            result = call_function(
                'pkg_gielda.pobierz_aktualna_cene',
                oracledb.NUMBER,
                [instrument_id]
            )
            return float(result) if result else None
        except oracledb.Error:
            return None

    @staticmethod
    def get_price_for_date(instrument_id: int, price_date: date) -> Optional[float]:
        """
        Get price for a specific date (time travel).

        Returns:
            Price or None if not available
        """
        try:
            result = call_function(
                'pkg_gielda_ext.pobierz_cene_dla_daty',
                oracledb.NUMBER,
                [instrument_id, price_date]
            )
            return float(result) if result else None
        except oracledb.Error:
            return None

    @staticmethod
    def calculate_commission(value: float, rate: float = 0.0039) -> float:
        """
        Calculate commission for a transaction.

        Returns:
            Commission amount
        """
        try:
            result = call_function(
                'pkg_gielda_ext.oblicz_prowizje',
                oracledb.NUMBER,
                [value, rate]
            )
            return float(result) if result else 0.0
        except oracledb.Error:
            return round(value * rate, 2)

    @staticmethod
    def calculate_gain_percent(purchase_value: float, current_value: float) -> float:
        """
        Calculate percentage gain/loss.

        Returns:
            Percentage value
        """
        try:
            result = call_function(
                'pkg_gielda.oblicz_zysk_procent',
                oracledb.NUMBER,
                [purchase_value, current_value]
            )
            return float(result) if result else 0.0
        except oracledb.Error:
            if purchase_value and purchase_value != 0:
                return ((current_value - purchase_value) / purchase_value) * 100
            return 0.0


# Convenience function for creating and immediately executing market orders
def create_and_execute_market_order(portfolio_id: int, instrument_id: int,
                                    order_side: str, quantity: float,
                                    price: float) -> Tuple[bool, str]:
    """
    Create and immediately execute a market order.

    Returns:
        Tuple of (success, message)
    """
    # Create the order
    success, message, order_id = Procedures.create_order(
        portfolio_id=portfolio_id,
        instrument_id=instrument_id,
        order_type='MARKET',
        order_side=order_side,
        quantity=quantity
    )

    if not success or order_id is None:
        return False, message

    # Execute the order
    if order_side == 'KUPNO':
        return Procedures.execute_buy_order(order_id, price)
    else:
        return Procedures.execute_sell_order(order_id, price)
