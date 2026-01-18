"""
Unit tests for database procedures wrapper module.
Tests the error handling and result parsing without actual DB connection.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.procedures import translate_oracle_error, parse_result, Procedures


class TestTranslateOracleError:
    """Tests for Oracle error translation."""

    def test_known_error_code(self):
        """Test translation of known error code."""
        mock_error = MagicMock()
        mock_error_obj = MagicMock()
        mock_error_obj.code = 20001
        mock_error.args = (mock_error_obj,)

        result = translate_oracle_error(mock_error)

        assert 'wartości portfela' in result.lower()

    def test_unique_constraint_error(self):
        """Test translation of unique constraint violation."""
        mock_error = MagicMock()
        mock_error_obj = MagicMock()
        mock_error_obj.code = 1
        mock_error.args = (mock_error_obj,)

        result = translate_oracle_error(mock_error)

        assert 'unikalności' in result.lower()

    def test_not_null_error(self):
        """Test translation of not null constraint violation."""
        mock_error = MagicMock()
        mock_error_obj = MagicMock()
        mock_error_obj.code = 1400
        mock_error.args = (mock_error_obj,)

        result = translate_oracle_error(mock_error)

        assert 'pusta' in result.lower()

    def test_foreign_key_error(self):
        """Test translation of foreign key violation."""
        mock_error = MagicMock()
        mock_error_obj = MagicMock()
        mock_error_obj.code = 2291
        mock_error.args = (mock_error_obj,)

        result = translate_oracle_error(mock_error)

        assert 'odwołanie' in result.lower()

    def test_unknown_error_code(self):
        """Test translation of unknown error code."""
        mock_error = MagicMock()
        mock_error_obj = MagicMock()
        mock_error_obj.code = 99999
        mock_error_obj.message = "Unknown error occurred"
        mock_error.args = (mock_error_obj,)

        result = translate_oracle_error(mock_error)

        assert 'Błąd bazy danych' in result
        assert 'Unknown error' in result

    def test_unexpected_error_format(self):
        """Test handling of unexpected error format."""
        mock_error = MagicMock()
        mock_error.args = ()
        mock_error.__str__ = MagicMock(return_value="Some error")

        result = translate_oracle_error(mock_error)

        assert 'Nieoczekiwany błąd' in result


class TestParseResult:
    """Tests for result string parsing."""

    def test_success_result(self):
        """Test parsing successful result."""
        result = "OK: Operacja zakończona pomyślnie"

        success, message = parse_result(result)

        assert success is True
        assert message == "Operacja zakończona pomyślnie"

    def test_error_result(self):
        """Test parsing error result."""
        result = "BŁĄD: Niewystarczające środki"

        success, message = parse_result(result)

        assert success is False
        assert message == "Niewystarczające środki"

    def test_none_result(self):
        """Test parsing None result."""
        success, message = parse_result(None)

        assert success is False
        assert 'Brak odpowiedzi' in message

    def test_unknown_format(self):
        """Test parsing unknown format."""
        result = "Some unexpected message"

        success, message = parse_result(result)

        assert success is False
        assert message == "Some unexpected message"


class TestProceduresUser:
    """Tests for user-related procedures."""

    @patch('db.procedures.get_db_connection')
    def test_create_user_success(self, mock_get_conn):
        """Test successful user creation."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        # Mock the OUT parameters
        user_id_var = MagicMock()
        user_id_var.getvalue.return_value = 1
        result_var = MagicMock()
        result_var.getvalue.return_value = "OK: Użytkownik utworzony"

        mock_cursor.var.side_effect = [user_id_var, result_var]

        success, message, user_id = Procedures.create_user(
            'testuser', 'password123', 'test@example.com'
        )

        assert success is True
        assert user_id == 1
        mock_cursor.callproc.assert_called_once()

    @patch('db.procedures.call_function')
    def test_verify_password_success(self, mock_call):
        """Test successful password verification."""
        mock_call.return_value = 1

        result = Procedures.verify_password('testuser', 'password123')

        assert result == 1

    @patch('db.procedures.call_function')
    def test_verify_password_failure(self, mock_call):
        """Test failed password verification."""
        mock_call.return_value = None

        result = Procedures.verify_password('testuser', 'wrongpassword')

        assert result is None


class TestProceduresPortfolio:
    """Tests for portfolio-related procedures."""

    @patch('db.procedures.get_db_connection')
    def test_create_portfolio_success(self, mock_get_conn):
        """Test successful portfolio creation."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        portfolio_id_var = MagicMock()
        portfolio_id_var.getvalue.return_value = 1
        result_var = MagicMock()
        result_var.getvalue.return_value = "OK: Portfel utworzony"

        mock_cursor.var.side_effect = [portfolio_id_var, result_var]

        success, message, portfolio_id = Procedures.create_portfolio(
            1, 'Mój portfel', 'USD', 10000
        )

        assert success is True
        assert portfolio_id == 1

    @patch('db.procedures.get_db_connection')
    def test_deposit_funds_success(self, mock_get_conn):
        """Test successful deposit."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        result_var = MagicMock()
        result_var.getvalue.return_value = "OK: Środki wpłacone"
        mock_cursor.var.return_value = result_var

        success, message = Procedures.deposit_funds(1, 1000)

        assert success is True
        assert 'wpłacone' in message.lower()

    @patch('db.procedures.get_db_connection')
    def test_withdraw_funds_success(self, mock_get_conn):
        """Test successful withdrawal."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        result_var = MagicMock()
        result_var.getvalue.return_value = "OK: Środki wypłacone"
        mock_cursor.var.return_value = result_var

        success, message = Procedures.withdraw_funds(1, 500)

        assert success is True

    @patch('db.procedures.get_db_connection')
    def test_withdraw_funds_insufficient(self, mock_get_conn):
        """Test withdrawal with insufficient funds."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        result_var = MagicMock()
        result_var.getvalue.return_value = "BŁĄD: Niewystarczające środki"
        mock_cursor.var.return_value = result_var

        success, message = Procedures.withdraw_funds(1, 100000)

        assert success is False
        assert 'Niewystarczające' in message

    @patch('db.procedures.call_function')
    def test_get_portfolio_value(self, mock_call):
        """Test getting portfolio value."""
        mock_call.return_value = 15000.00

        result = Procedures.get_portfolio_value(1)

        assert result == 15000.00

    @patch('db.procedures.call_function')
    def test_get_portfolio_value_none(self, mock_call):
        """Test getting portfolio value when None."""
        mock_call.return_value = None

        result = Procedures.get_portfolio_value(1)

        assert result == 0.0


class TestProceduresOrder:
    """Tests for order-related procedures."""

    @patch('db.procedures.get_db_connection')
    def test_create_order_success(self, mock_get_conn):
        """Test successful order creation."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        order_id_var = MagicMock()
        order_id_var.getvalue.return_value = 1
        result_var = MagicMock()
        result_var.getvalue.return_value = "OK: Zlecenie utworzone"

        mock_cursor.var.side_effect = [order_id_var, result_var]

        success, message, order_id = Procedures.create_order(
            portfolio_id=1,
            instrument_id=1,
            order_type='MARKET',
            order_side='KUPNO',
            quantity=10
        )

        assert success is True
        assert order_id == 1

    @patch('db.procedures.get_db_connection')
    def test_execute_buy_order_success(self, mock_get_conn):
        """Test successful buy order execution."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        result_var = MagicMock()
        result_var.getvalue.return_value = "OK: Zlecenie wykonane"
        mock_cursor.var.return_value = result_var

        success, message = Procedures.execute_buy_order(1, 150.00)

        assert success is True

    @patch('db.procedures.get_db_connection')
    def test_execute_sell_order_success(self, mock_get_conn):
        """Test successful sell order execution."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        result_var = MagicMock()
        result_var.getvalue.return_value = "OK: Zlecenie wykonane"
        mock_cursor.var.return_value = result_var

        success, message = Procedures.execute_sell_order(1, 155.00)

        assert success is True

    @patch('db.procedures.get_db_connection')
    def test_cancel_order_success(self, mock_get_conn):
        """Test successful order cancellation."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        result_var = MagicMock()
        result_var.getvalue.return_value = "OK: Zlecenie anulowane"
        mock_cursor.var.return_value = result_var

        success, message = Procedures.cancel_order(1)

        assert success is True


class TestProceduresPrice:
    """Tests for price-related procedures."""

    @patch('db.procedures.call_function')
    def test_get_current_price(self, mock_call):
        """Test getting current price."""
        mock_call.return_value = 150.00

        result = Procedures.get_current_price(1)

        assert result == 150.00

    @patch('db.procedures.call_function')
    def test_get_current_price_none(self, mock_call):
        """Test getting current price when not available."""
        mock_call.return_value = None

        result = Procedures.get_current_price(999)

        assert result is None

    @patch('db.procedures.call_function')
    def test_get_price_for_date(self, mock_call):
        """Test getting price for specific date."""
        from datetime import date
        mock_call.return_value = 145.00

        result = Procedures.get_price_for_date(1, date(2025, 1, 15))

        assert result == 145.00

    @patch('db.procedures.call_function')
    def test_calculate_commission(self, mock_call):
        """Test commission calculation."""
        mock_call.return_value = 3.90

        result = Procedures.calculate_commission(1000, 0.0039)

        assert result == 3.90

    @patch('db.procedures.call_function')
    def test_calculate_commission_fallback(self, mock_call):
        """Test commission calculation fallback on error."""
        import oracledb
        mock_call.side_effect = oracledb.Error("DB error")

        result = Procedures.calculate_commission(1000, 0.0039)

        # Should fall back to Python calculation
        assert result == 3.90

    @patch('db.procedures.call_function')
    def test_calculate_gain_percent(self, mock_call):
        """Test gain percentage calculation."""
        mock_call.return_value = 10.0

        result = Procedures.calculate_gain_percent(1000, 1100)

        assert result == 10.0

    @patch('db.procedures.call_function')
    def test_calculate_gain_percent_fallback(self, mock_call):
        """Test gain percentage fallback calculation."""
        import oracledb
        mock_call.side_effect = oracledb.Error("DB error")

        result = Procedures.calculate_gain_percent(1000, 1100)

        # Should fall back to Python calculation
        assert result == 10.0


class TestCreateAndExecuteMarketOrder:
    """Tests for combined market order creation and execution."""

    @patch('db.procedures.Procedures.execute_buy_order')
    @patch('db.procedures.Procedures.create_order')
    def test_create_and_execute_buy(self, mock_create, mock_execute):
        """Test creating and executing a buy market order."""
        from db.procedures import create_and_execute_market_order

        mock_create.return_value = (True, "Zlecenie utworzone", 1)
        mock_execute.return_value = (True, "Zlecenie wykonane")

        success, message = create_and_execute_market_order(
            portfolio_id=1,
            instrument_id=1,
            order_side='KUPNO',
            quantity=10,
            price=150.00
        )

        assert success is True
        mock_execute.assert_called_once()

    @patch('db.procedures.Procedures.execute_sell_order')
    @patch('db.procedures.Procedures.create_order')
    def test_create_and_execute_sell(self, mock_create, mock_execute):
        """Test creating and executing a sell market order."""
        from db.procedures import create_and_execute_market_order

        mock_create.return_value = (True, "Zlecenie utworzone", 1)
        mock_execute.return_value = (True, "Zlecenie wykonane")

        success, message = create_and_execute_market_order(
            portfolio_id=1,
            instrument_id=1,
            order_side='SPRZEDAZ',
            quantity=10,
            price=155.00
        )

        assert success is True
        mock_execute.assert_called_once()

    @patch('db.procedures.Procedures.create_order')
    def test_create_order_fails(self, mock_create):
        """Test handling when order creation fails."""
        from db.procedures import create_and_execute_market_order

        mock_create.return_value = (False, "Niewystarczające środki", None)

        success, message = create_and_execute_market_order(
            portfolio_id=1,
            instrument_id=1,
            order_side='KUPNO',
            quantity=1000,
            price=150.00
        )

        assert success is False
        assert 'Niewystarczające' in message
