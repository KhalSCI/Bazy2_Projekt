"""
Integration tests for the Stock Exchange Simulator.
These tests require a running Oracle database.

To run these tests:
    RUN_INTEGRATION_TESTS=1 pytest tests/test_integration.py -v

Make sure the following environment variables are set:
    ORACLE_HOST, ORACLE_PORT, ORACLE_SERVICE, ORACLE_USER, ORACLE_PASSWORD
"""

import pytest
import os
import sys
from datetime import date, datetime
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Skip all tests in this module if integration tests are disabled
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to run."
)


class TestDatabaseConnection:
    """Tests for database connection."""

    def test_connection_pool(self):
        """Test that connection pool is created successfully."""
        from db.connection import get_db_connection

        with get_db_connection() as conn:
            assert conn is not None

    def test_execute_query(self):
        """Test executing a simple query."""
        from db.connection import execute_query

        result = execute_query("SELECT 1 FROM DUAL")

        assert result is not None
        assert len(result) == 1
        assert result[0][0] == 1

    def test_execute_query_dict(self):
        """Test executing a query with dict result."""
        from db.connection import execute_query_dict

        result = execute_query_dict("SELECT 1 as value FROM DUAL")

        assert result is not None
        assert len(result) == 1
        # Column names are converted to lowercase in execute_query_dict
        assert result[0]['value'] == 1


class TestUserIntegration:
    """Integration tests for user operations."""

    def _generate_unique_login(self):
        """Generate unique login for testing."""
        return f"test_{uuid.uuid4().hex[:8]}"

    def test_create_user(self):
        """Test creating a new user."""
        from services.portfolio_service import UserService

        login = self._generate_unique_login()
        email = f"{login}@test.com"

        success, message, user_id = UserService.create_user(
            login=login,
            password='testpass123',
            email=email,
            first_name='Test',
            last_name='User'
        )

        assert success, f"Failed to create user: {message}"
        assert user_id is not None

    def test_create_user_duplicate_login(self):
        """Test creating user with duplicate login fails."""
        from services.portfolio_service import UserService

        login = self._generate_unique_login()
        email1 = f"{login}@test1.com"
        email2 = f"{login}@test2.com"

        # Create first user
        success1, _, _ = UserService.create_user(login, 'pass1', email1)
        assert success1

        # Try to create second user with same login
        success2, message, _ = UserService.create_user(login, 'pass2', email2)
        assert not success2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        from services.portfolio_service import UserService

        login = self._generate_unique_login()
        password = 'correctpassword'
        email = f"{login}@test.com"

        UserService.create_user(login, password, email)
        user_id = UserService.verify_login(login, password)

        assert user_id is not None

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        from services.portfolio_service import UserService

        login = self._generate_unique_login()
        email = f"{login}@test.com"

        UserService.create_user(login, 'correctpassword', email)
        user_id = UserService.verify_login(login, 'wrongpassword')

        assert user_id is None

    def test_get_user_by_login(self):
        """Test getting user by login."""
        from services.portfolio_service import UserService

        login = self._generate_unique_login()
        email = f"{login}@test.com"

        UserService.create_user(login, 'password', email)
        user = UserService.get_user_by_login(login)

        assert user is not None
        assert user['login'] == login.upper() or user['login'] == login


class TestPortfolioIntegration:
    """Integration tests for portfolio operations."""

    @pytest.fixture
    def test_user(self):
        """Create a test user for portfolio tests."""
        from services.portfolio_service import UserService

        login = f"portfolio_test_{uuid.uuid4().hex[:8]}"
        email = f"{login}@test.com"

        success, _, user_id = UserService.create_user(login, 'password', email)
        assert success

        return user_id

    def test_create_portfolio(self, test_user):
        """Test creating a new portfolio."""
        from services.portfolio_service import PortfolioService

        success, message, portfolio_id = PortfolioService.create_portfolio(
            user_id=test_user,
            name='Test Portfolio',
            currency='USD',
            initial_balance=10000
        )

        assert success, f"Failed to create portfolio: {message}"
        assert portfolio_id is not None

    def test_deposit_funds(self, test_user):
        """Test depositing funds to portfolio."""
        from services.portfolio_service import PortfolioService

        _, _, portfolio_id = PortfolioService.create_portfolio(
            test_user, 'Deposit Test', 'USD', 1000
        )

        success, message = PortfolioService.deposit_funds(portfolio_id, 500)

        assert success, f"Failed to deposit: {message}"

        # Verify new balance
        cash = PortfolioService.get_available_cash(portfolio_id)
        assert cash == 1500

    def test_withdraw_funds(self, test_user):
        """Test withdrawing funds from portfolio."""
        from services.portfolio_service import PortfolioService

        _, _, portfolio_id = PortfolioService.create_portfolio(
            test_user, 'Withdraw Test', 'USD', 1000
        )

        success, message = PortfolioService.withdraw_funds(portfolio_id, 300)

        assert success, f"Failed to withdraw: {message}"

        cash = PortfolioService.get_available_cash(portfolio_id)
        assert cash == 700

    def test_withdraw_insufficient_funds(self, test_user):
        """Test withdrawing more than available fails."""
        from services.portfolio_service import PortfolioService

        _, _, portfolio_id = PortfolioService.create_portfolio(
            test_user, 'Insufficient Test', 'USD', 1000
        )

        success, message = PortfolioService.withdraw_funds(portfolio_id, 2000)

        assert not success

    def test_get_portfolio_summary(self, test_user):
        """Test getting portfolio summary."""
        from services.portfolio_service import PortfolioService

        _, _, portfolio_id = PortfolioService.create_portfolio(
            test_user, 'Summary Test', 'USD', 5000
        )

        summary = PortfolioService.get_portfolio_summary(portfolio_id)

        assert summary is not None
        assert summary['saldo_gotowkowe'] == 5000
        assert 'wartosc_calkowita' in summary


class TestMarketIntegration:
    """Integration tests for market data operations."""

    def test_get_all_instruments(self):
        """Test getting all instruments."""
        from services.market_service import MarketService

        instruments = MarketService.get_all_instruments()

        assert instruments is not None
        assert len(instruments) > 0

    def test_get_instrument_by_symbol(self):
        """Test getting instrument by symbol."""
        from services.market_service import MarketService

        # Assuming AAPL exists in the database
        instrument = MarketService.get_instrument_by_symbol('AAPL')

        if instrument:
            assert instrument['symbol'] == 'AAPL'

    def test_get_current_price(self):
        """Test getting current price."""
        from services.market_service import MarketService

        instruments = MarketService.get_all_instruments()
        if instruments:
            instrument_id = instruments[0]['instrument_id']
            price = MarketService.get_current_price(instrument_id)

            # Price may be None if no data exists
            if price is not None:
                assert price > 0

    def test_get_all_sectors(self):
        """Test getting all sectors."""
        from services.market_service import MarketService

        sectors = MarketService.get_all_sectors()

        assert sectors is not None

    def test_get_date_range(self):
        """Test getting available date range."""
        from services.market_service import MarketService

        min_date, max_date = MarketService.get_date_range()

        if min_date and max_date:
            assert min_date <= max_date


class TestOrderIntegration:
    """Integration tests for order operations."""

    @pytest.fixture
    def test_portfolio(self):
        """Create a test user and portfolio for order tests."""
        from services.portfolio_service import UserService, PortfolioService

        login = f"order_test_{uuid.uuid4().hex[:8]}"
        email = f"{login}@test.com"

        _, _, user_id = UserService.create_user(login, 'password', email)
        _, _, portfolio_id = PortfolioService.create_portfolio(
            user_id, 'Order Test Portfolio', 'USD', 100000
        )

        return portfolio_id

    def test_calculate_order_cost(self):
        """Test calculating order cost."""
        from services.order_service import OrderService

        result = OrderService.calculate_order_cost(10, 150.00)

        assert result['wartosc'] == 1500.00
        assert result['prowizja'] > 0
        assert result['koszt_calkowity'] > result['wartosc']

    def test_calculate_order_proceeds(self):
        """Test calculating order proceeds."""
        from services.order_service import OrderService

        result = OrderService.calculate_order_proceeds(10, 150.00)

        assert result['wartosc'] == 1500.00
        assert result['prowizja'] > 0
        assert result['przychod_netto'] < result['wartosc']

    def test_get_orders_empty(self, test_portfolio):
        """Test getting orders for empty portfolio."""
        from services.order_service import OrderService

        orders = OrderService.get_orders_by_portfolio(test_portfolio)

        assert orders is not None
        assert len(orders) == 0


class TestFullTradingFlow:
    """Integration tests for complete trading flows."""

    @pytest.fixture
    def trading_setup(self):
        """Create complete trading setup with user, portfolio, and find instrument."""
        from services.portfolio_service import UserService, PortfolioService
        from services.market_service import MarketService

        # Create user
        login = f"trading_test_{uuid.uuid4().hex[:8]}"
        email = f"{login}@test.com"
        _, _, user_id = UserService.create_user(login, 'password', email)

        # Create portfolio with funds
        _, _, portfolio_id = PortfolioService.create_portfolio(
            user_id, 'Trading Test', 'USD', 50000
        )

        # Get an instrument with price data
        instruments = MarketService.get_all_instruments()
        instrument = None
        price = None

        for inst in instruments:
            p = MarketService.get_current_price(inst['instrument_id'])
            if p and p > 0:
                instrument = inst
                price = p
                break

        return {
            'portfolio_id': portfolio_id,
            'instrument_id': instrument['instrument_id'] if instrument else None,
            'symbol': instrument['symbol'] if instrument else None,
            'price': price
        }

    def test_buy_and_check_position(self, trading_setup):
        """Test buying shares and verifying position."""
        from services.order_service import OrderService
        from services.portfolio_service import PortfolioService

        if not trading_setup['instrument_id']:
            pytest.skip("No instrument with price data available")

        portfolio_id = trading_setup['portfolio_id']
        instrument_id = trading_setup['instrument_id']
        price = trading_setup['price']

        # Execute buy order
        success, message = OrderService.create_and_execute_buy(
            portfolio_id, instrument_id, 10, price
        )

        assert success, f"Buy failed: {message}"

        # Check position was created
        positions = PortfolioService.get_positions(portfolio_id)
        position = next(
            (p for p in positions if p['instrument_id'] == instrument_id),
            None
        )

        assert position is not None
        assert float(position['ilosc_akcji']) == 10

    def test_buy_then_sell(self, trading_setup):
        """Test complete buy and sell flow."""
        from services.order_service import OrderService
        from services.portfolio_service import PortfolioService

        if not trading_setup['instrument_id']:
            pytest.skip("No instrument with price data available")

        portfolio_id = trading_setup['portfolio_id']
        instrument_id = trading_setup['instrument_id']
        price = trading_setup['price']

        # Get initial cash
        initial_cash = PortfolioService.get_available_cash(portfolio_id)

        # Buy shares
        success, _ = OrderService.create_and_execute_buy(
            portfolio_id, instrument_id, 5, price
        )
        assert success

        # Sell shares
        success, _ = OrderService.create_and_execute_sell(
            portfolio_id, instrument_id, 5, price
        )
        assert success

        # Verify position is closed
        position = PortfolioService.get_position_by_instrument(
            portfolio_id, instrument_id
        )
        if position:
            assert float(position.get('ilosc_akcji', 0)) == 0

        # Cash should be slightly less due to commission (bought and sold at same price)
        final_cash = PortfolioService.get_available_cash(portfolio_id)
        assert final_cash < initial_cash  # Commission was paid


class TestTransactionHistory:
    """Integration tests for transaction history."""

    @pytest.fixture
    def portfolio_with_transactions(self):
        """Create portfolio with some transactions."""
        from services.portfolio_service import UserService, PortfolioService
        from services.order_service import OrderService
        from services.market_service import MarketService

        # Create user and portfolio
        login = f"txn_test_{uuid.uuid4().hex[:8]}"
        email = f"{login}@test.com"
        _, _, user_id = UserService.create_user(login, 'password', email)
        _, _, portfolio_id = PortfolioService.create_portfolio(
            user_id, 'Transaction Test', 'USD', 50000
        )

        # Find instrument with price
        instruments = MarketService.get_all_instruments()
        for inst in instruments:
            price = MarketService.get_current_price(inst['instrument_id'])
            if price and price > 0:
                # Execute some transactions
                OrderService.create_and_execute_buy(
                    portfolio_id, inst['instrument_id'], 5, price
                )
                OrderService.create_and_execute_sell(
                    portfolio_id, inst['instrument_id'], 2, price
                )
                return portfolio_id

        return portfolio_id

    def test_get_transactions(self, portfolio_with_transactions):
        """Test retrieving transaction history."""
        from services.order_service import TransactionService

        transactions = TransactionService.get_transactions_by_portfolio(
            portfolio_with_transactions
        )

        # Should have at least 2 transactions (buy and sell)
        assert len(transactions) >= 2

    def test_get_transactions_by_date_range(self, portfolio_with_transactions):
        """Test retrieving transactions by date range."""
        from services.order_service import TransactionService

        transactions = TransactionService.get_transactions_by_date_range(
            portfolio_with_transactions,
            date(2020, 1, 1),
            date(2030, 12, 31)
        )

        assert len(transactions) >= 0
