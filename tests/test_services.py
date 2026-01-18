"""
Unit tests for service layer with mocked database.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPortfolioService:
    """Tests for PortfolioService."""

    @patch('services.portfolio_service.execute_query_dict')
    def test_get_user_portfolios(self, mock_execute):
        """Test getting user portfolios."""
        from services.portfolio_service import PortfolioService

        mock_execute.return_value = [
            {'portfolio_id': 1, 'nazwa_portfela': 'Portfel 1'},
            {'portfolio_id': 2, 'nazwa_portfela': 'Portfel 2'}
        ]

        result = PortfolioService.get_user_portfolios(1)

        assert len(result) == 2
        assert result[0]['portfolio_id'] == 1
        mock_execute.assert_called_once()

    @patch('services.portfolio_service.execute_query_dict')
    def test_get_portfolio_found(self, mock_execute):
        """Test getting portfolio by ID - found."""
        from services.portfolio_service import PortfolioService

        mock_execute.return_value = [{'portfolio_id': 1, 'nazwa_portfela': 'Test'}]

        result = PortfolioService.get_portfolio(1)

        assert result is not None
        assert result['portfolio_id'] == 1

    @patch('services.portfolio_service.execute_query_dict')
    def test_get_portfolio_not_found(self, mock_execute):
        """Test getting portfolio by ID - not found."""
        from services.portfolio_service import PortfolioService

        mock_execute.return_value = []

        result = PortfolioService.get_portfolio(999)

        assert result is None

    @patch('services.portfolio_service.execute_query_dict')
    def test_get_portfolio_summary(self, mock_execute):
        """Test getting portfolio summary."""
        from services.portfolio_service import PortfolioService

        mock_execute.return_value = [{
            'portfolio_id': 1,
            'saldo_gotowkowe': 10000.00,
            'wartosc_pozycji': 5000.00
        }]

        result = PortfolioService.get_portfolio_summary(1)

        assert result is not None
        assert result['wartosc_calkowita'] == 15000.00

    @patch('services.portfolio_service.execute_query_dict')
    def test_get_portfolio_summary_with_none_values(self, mock_execute):
        """Test portfolio summary with None values."""
        from services.portfolio_service import PortfolioService

        mock_execute.return_value = [{
            'portfolio_id': 1,
            'saldo_gotowkowe': None,
            'wartosc_pozycji': None
        }]

        result = PortfolioService.get_portfolio_summary(1)

        assert result is not None
        assert result['wartosc_calkowita'] == 0.0

    @patch('services.portfolio_service.execute_query_dict')
    def test_get_positions(self, mock_execute):
        """Test getting portfolio positions."""
        from services.portfolio_service import PortfolioService

        mock_execute.return_value = [
            {'position_id': 1, 'symbol': 'AAPL'},
            {'position_id': 2, 'symbol': 'MSFT'}
        ]

        result = PortfolioService.get_positions(1)

        assert len(result) == 2

    @patch('services.portfolio_service.Procedures')
    def test_get_portfolio_value(self, mock_procedures):
        """Test getting portfolio value."""
        from services.portfolio_service import PortfolioService

        mock_procedures.get_portfolio_value.return_value = 15000.00

        result = PortfolioService.get_portfolio_value(1)

        assert result == 15000.00

    @patch('services.portfolio_service.Procedures')
    def test_get_portfolio_value_none(self, mock_procedures):
        """Test getting portfolio value when None."""
        from services.portfolio_service import PortfolioService

        mock_procedures.get_portfolio_value.return_value = None

        result = PortfolioService.get_portfolio_value(1)

        assert result == 0.0

    @patch('services.portfolio_service.Procedures')
    def test_create_portfolio_success(self, mock_procedures):
        """Test creating portfolio successfully."""
        from services.portfolio_service import PortfolioService

        mock_procedures.create_portfolio.return_value = (True, 'Portfel utworzony', 1)

        success, msg, portfolio_id = PortfolioService.create_portfolio(1, 'Test', 'USD', 10000)

        assert success
        assert portfolio_id == 1

    @patch('services.portfolio_service.Procedures')
    def test_deposit_funds(self, mock_procedures):
        """Test depositing funds."""
        from services.portfolio_service import PortfolioService

        mock_procedures.deposit_funds.return_value = (True, 'Środki wpłacone')

        success, msg = PortfolioService.deposit_funds(1, 1000)

        assert success
        mock_procedures.deposit_funds.assert_called_once_with(1, 1000)

    @patch('services.portfolio_service.Procedures')
    def test_withdraw_funds(self, mock_procedures):
        """Test withdrawing funds."""
        from services.portfolio_service import PortfolioService

        mock_procedures.withdraw_funds.return_value = (True, 'Środki wypłacone')

        success, msg = PortfolioService.withdraw_funds(1, 500)

        assert success

    @patch('services.portfolio_service.execute_query_dict')
    def test_get_available_cash(self, mock_execute):
        """Test getting available cash."""
        from services.portfolio_service import PortfolioService

        mock_execute.return_value = [{'saldo_gotowkowe': 5000.00}]

        result = PortfolioService.get_available_cash(1)

        assert result == 5000.00

    @patch('services.portfolio_service.execute_query_dict')
    def test_get_available_cash_no_portfolio(self, mock_execute):
        """Test getting available cash when no portfolio."""
        from services.portfolio_service import PortfolioService

        mock_execute.return_value = []

        result = PortfolioService.get_available_cash(999)

        assert result == 0.0


class TestUserService:
    """Tests for UserService."""

    @patch('services.portfolio_service.execute_query_dict')
    def test_get_user_by_login_found(self, mock_execute):
        """Test getting user by login - found."""
        from services.portfolio_service import UserService

        mock_execute.return_value = [{'user_id': 1, 'login': 'testuser'}]

        result = UserService.get_user_by_login('testuser')

        assert result is not None
        assert result['login'] == 'testuser'

    @patch('services.portfolio_service.execute_query_dict')
    def test_get_user_by_login_not_found(self, mock_execute):
        """Test getting user by login - not found."""
        from services.portfolio_service import UserService

        mock_execute.return_value = []

        result = UserService.get_user_by_login('nonexistent')

        assert result is None

    @patch('services.portfolio_service.Procedures')
    def test_create_user_success(self, mock_procedures):
        """Test creating user successfully."""
        from services.portfolio_service import UserService

        mock_procedures.create_user.return_value = (True, 'Użytkownik utworzony', 1)

        success, msg, user_id = UserService.create_user('test', 'pass123', 'test@example.com')

        assert success
        assert user_id == 1

    @patch('services.portfolio_service.Procedures')
    def test_verify_login_success(self, mock_procedures):
        """Test successful login verification."""
        from services.portfolio_service import UserService

        mock_procedures.verify_password.return_value = 1

        result = UserService.verify_login('testuser', 'password')

        assert result == 1

    @patch('services.portfolio_service.Procedures')
    def test_verify_login_failure(self, mock_procedures):
        """Test failed login verification."""
        from services.portfolio_service import UserService

        mock_procedures.verify_password.return_value = None

        result = UserService.verify_login('testuser', 'wrongpassword')

        assert result is None

    @patch('services.portfolio_service.Procedures')
    @patch('services.portfolio_service.execute_query_dict')
    def test_authenticate_success(self, mock_execute, mock_procedures):
        """Test successful authentication."""
        from services.portfolio_service import UserService

        mock_procedures.verify_password.return_value = 1
        mock_execute.return_value = [{'user_id': 1, 'login': 'testuser'}]

        success, msg, user = UserService.authenticate('testuser', 'password')

        assert success
        assert user is not None
        assert user['login'] == 'testuser'

    @patch('services.portfolio_service.Procedures')
    def test_authenticate_failure(self, mock_procedures):
        """Test failed authentication."""
        from services.portfolio_service import UserService

        mock_procedures.verify_password.return_value = None

        success, msg, user = UserService.authenticate('testuser', 'wrongpassword')

        assert not success
        assert user is None
        assert 'Nieprawidłowy' in msg


class TestOrderService:
    """Tests for OrderService."""

    @patch('services.order_service.execute_query_dict')
    def test_get_orders_by_portfolio(self, mock_execute):
        """Test getting orders by portfolio."""
        from services.order_service import OrderService

        mock_execute.return_value = [
            {'order_id': 1, 'status': 'WYKONANE'},
            {'order_id': 2, 'status': 'OCZEKUJACE'}
        ]

        result = OrderService.get_orders_by_portfolio(1)

        assert len(result) == 2

    @patch('services.order_service.execute_query_dict')
    def test_get_pending_orders(self, mock_execute):
        """Test getting pending orders."""
        from services.order_service import OrderService

        mock_execute.return_value = [{'order_id': 1, 'status': 'OCZEKUJACE'}]

        result = OrderService.get_pending_orders(1)

        assert len(result) == 1
        assert result[0]['status'] == 'OCZEKUJACE'

    @patch('services.order_service.execute_query_dict')
    def test_get_order_by_id_found(self, mock_execute):
        """Test getting order by ID - found."""
        from services.order_service import OrderService

        mock_execute.return_value = [{'order_id': 1, 'typ_zlecenia': 'MARKET'}]

        result = OrderService.get_order_by_id(1)

        assert result is not None
        assert result['order_id'] == 1

    @patch('services.order_service.execute_query_dict')
    def test_get_order_by_id_not_found(self, mock_execute):
        """Test getting order by ID - not found."""
        from services.order_service import OrderService

        mock_execute.return_value = []

        result = OrderService.get_order_by_id(999)

        assert result is None

    @patch('services.order_service.Procedures')
    def test_calculate_order_cost(self, mock_procedures):
        """Test calculating order cost."""
        from services.order_service import OrderService

        mock_procedures.calculate_commission.return_value = 3.90

        result = OrderService.calculate_order_cost(10, 100)

        assert result['wartosc'] == 1000.00
        assert result['prowizja'] == 3.90
        assert result['koszt_calkowity'] == 1003.90

    @patch('services.order_service.Procedures')
    def test_calculate_order_proceeds(self, mock_procedures):
        """Test calculating order proceeds."""
        from services.order_service import OrderService

        mock_procedures.calculate_commission.return_value = 3.90

        result = OrderService.calculate_order_proceeds(10, 100)

        assert result['wartosc'] == 1000.00
        assert result['prowizja'] == 3.90
        assert result['przychod_netto'] == 996.10

    @patch('services.order_service.execute_query_dict')
    def test_has_pending_limit_orders_true(self, mock_execute):
        """Test checking for pending limit orders - has orders."""
        from services.order_service import OrderService

        mock_execute.return_value = [
            {'order_id': 1, 'typ_zlecenia': 'LIMIT', 'status': 'OCZEKUJACE'}
        ]

        result = OrderService.has_pending_limit_orders(1)

        assert result is True

    @patch('services.order_service.execute_query_dict')
    def test_has_pending_limit_orders_false(self, mock_execute):
        """Test checking for pending limit orders - no orders."""
        from services.order_service import OrderService

        mock_execute.return_value = [
            {'order_id': 1, 'typ_zlecenia': 'MARKET', 'status': 'OCZEKUJACE'}
        ]

        result = OrderService.has_pending_limit_orders(1)

        assert result is False


class TestTransactionService:
    """Tests for TransactionService."""

    @patch('services.order_service.execute_query_dict')
    def test_get_transactions_by_portfolio(self, mock_execute):
        """Test getting transactions by portfolio."""
        from services.order_service import TransactionService

        mock_execute.return_value = [
            {'transaction_id': 1, 'typ_transakcji': 'KUPNO'},
            {'transaction_id': 2, 'typ_transakcji': 'SPRZEDAZ'}
        ]

        result = TransactionService.get_transactions_by_portfolio(1)

        assert len(result) == 2

    @patch('services.order_service.execute_query_dict')
    def test_get_transactions_by_date_range(self, mock_execute):
        """Test getting transactions by date range."""
        from services.order_service import TransactionService

        mock_execute.return_value = [
            {'transaction_id': 1, 'data_transakcji': date(2025, 1, 15)}
        ]

        result = TransactionService.get_transactions_by_date_range(
            1, date(2025, 1, 1), date(2025, 1, 31)
        )

        assert len(result) == 1


class TestMarketService:
    """Tests for MarketService."""

    @patch('services.market_service.execute_query_dict')
    def test_get_all_instruments(self, mock_execute):
        """Test getting all instruments."""
        from services.market_service import MarketService

        mock_execute.return_value = [
            {'instrument_id': 1, 'symbol': 'AAPL'},
            {'instrument_id': 2, 'symbol': 'MSFT'}
        ]

        result = MarketService.get_all_instruments()

        assert len(result) == 2

    @patch('services.market_service.execute_query_dict')
    def test_get_instrument_by_id_found(self, mock_execute):
        """Test getting instrument by ID - found."""
        from services.market_service import MarketService

        mock_execute.return_value = [{'instrument_id': 1, 'symbol': 'AAPL'}]

        result = MarketService.get_instrument_by_id(1)

        assert result is not None
        assert result['symbol'] == 'AAPL'

    @patch('services.market_service.execute_query_dict')
    def test_get_instrument_by_symbol_found(self, mock_execute):
        """Test getting instrument by symbol - found."""
        from services.market_service import MarketService

        mock_execute.return_value = [{'instrument_id': 1, 'symbol': 'AAPL'}]

        result = MarketService.get_instrument_by_symbol('AAPL')

        assert result is not None
        assert result['instrument_id'] == 1

    @patch('services.market_service.Procedures')
    def test_get_current_price(self, mock_procedures):
        """Test getting current price."""
        from services.market_service import MarketService

        mock_procedures.get_current_price.return_value = 150.00

        result = MarketService.get_current_price(1)

        assert result == 150.00

    @patch('services.market_service.Procedures')
    def test_get_price_for_date(self, mock_procedures):
        """Test getting price for date."""
        from services.market_service import MarketService

        mock_procedures.get_price_for_date.return_value = 145.00

        result = MarketService.get_price_for_date(1, date(2025, 1, 15))

        assert result == 145.00

    @patch('services.market_service.execute_query_dict')
    def test_get_all_sectors(self, mock_execute):
        """Test getting all sectors."""
        from services.market_service import MarketService

        mock_execute.return_value = [
            {'sector_id': 1, 'nazwa_sektora': 'Technologia'},
            {'sector_id': 2, 'nazwa_sektora': 'Finanse'}
        ]

        result = MarketService.get_all_sectors()

        assert len(result) == 2

    @patch('services.market_service.execute_query')
    def test_get_date_range(self, mock_execute):
        """Test getting date range."""
        from services.market_service import MarketService

        mock_execute.return_value = [(date(2025, 1, 1), date(2025, 12, 31))]

        min_date, max_date = MarketService.get_date_range()

        assert min_date == date(2025, 1, 1)
        assert max_date == date(2025, 12, 31)

    @patch('services.market_service.execute_query')
    def test_get_date_range_empty(self, mock_execute):
        """Test getting date range when empty."""
        from services.market_service import MarketService

        mock_execute.return_value = []

        min_date, max_date = MarketService.get_date_range()

        assert min_date is None
        assert max_date is None

    @patch('services.market_service.execute_query')
    def test_get_trading_days_between(self, mock_execute):
        """Test getting trading days between dates."""
        from services.market_service import MarketService

        mock_execute.return_value = [
            (date(2025, 1, 2),),
            (date(2025, 1, 3),),
            (date(2025, 1, 6),)
        ]

        result = MarketService.get_trading_days_between(date(2025, 1, 1), date(2025, 1, 6))

        assert len(result) == 3
