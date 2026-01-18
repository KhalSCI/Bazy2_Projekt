"""
Pytest configuration and fixtures for the Stock Exchange Simulator tests.
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import date, datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================
# MOCK FIXTURES
# ============================================

@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    with patch('db.connection.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.__enter__ = MagicMock(return_value=MagicMock(cursor=MagicMock(return_value=mock_cursor)))
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_conn, mock_cursor


@pytest.fixture
def mock_execute_query_dict():
    """Mock execute_query_dict function."""
    with patch('db.connection.execute_query_dict') as mock:
        yield mock


@pytest.fixture
def mock_execute_query():
    """Mock execute_query function."""
    with patch('db.connection.execute_query') as mock:
        yield mock


@pytest.fixture
def mock_call_function():
    """Mock call_function for PL/SQL functions."""
    with patch('db.connection.call_function') as mock:
        yield mock


# ============================================
# SAMPLE DATA FIXTURES
# ============================================

@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        'user_id': 1,
        'login': 'testuser',
        'email': 'test@example.com',
        'imie': 'Jan',
        'nazwisko': 'Kowalski',
        'data_rejestracji': date(2025, 1, 1),
        'waluta_bazowa': 'USD'
    }


@pytest.fixture
def sample_portfolio():
    """Sample portfolio data."""
    return {
        'portfolio_id': 1,
        'user_id': 1,
        'nazwa_portfela': 'Portfel testowy',
        'saldo_gotowkowe': 10000.00,
        'waluta_portfela': 'USD',
        'data_utworzenia': date(2025, 1, 1)
    }


@pytest.fixture
def sample_portfolio_summary():
    """Sample portfolio summary data."""
    return {
        'portfolio_id': 1,
        'nazwa_portfela': 'Portfel testowy',
        'saldo_gotowkowe': 10000.00,
        'waluta_portfela': 'USD',
        'wartosc_pozycji': 5000.00,
        'zysk_strata_pozycji': 250.00,
        'liczba_pozycji': 3
    }


@pytest.fixture
def sample_instrument():
    """Sample instrument data."""
    return {
        'instrument_id': 1,
        'symbol': 'AAPL',
        'nazwa_pelna': 'Apple Inc.',
        'typ_instrumentu': 'AKCJA',
        'waluta_notowania': 'USD',
        'sector_id': 1,
        'nazwa_sektora': 'Technologia'
    }


@pytest.fixture
def sample_position():
    """Sample position data."""
    return {
        'position_id': 1,
        'portfolio_id': 1,
        'instrument_id': 1,
        'symbol': 'AAPL',
        'nazwa_pelna': 'Apple Inc.',
        'ilosc_akcji': 10.0,
        'srednia_cena_zakupu': 150.00,
        'wartosc_zakupu': 1500.00,
        'wartosc_biezaca': 1600.00,
        'cena_biezaca': 160.00,
        'zysk_strata': 100.00,
        'zysk_strata_procent': 6.67,
        'data_pierwszego_zakupu': date(2025, 1, 15)
    }


@pytest.fixture
def sample_positions():
    """Sample list of positions."""
    return [
        {
            'position_id': 1,
            'portfolio_id': 1,
            'instrument_id': 1,
            'symbol': 'AAPL',
            'nazwa_pelna': 'Apple Inc.',
            'ilosc_akcji': 10.0,
            'srednia_cena_zakupu': 150.00,
            'wartosc_zakupu': 1500.00,
            'wartosc_biezaca': 1600.00,
            'zysk_strata': 100.00,
            'zysk_strata_procent': 6.67
        },
        {
            'position_id': 2,
            'portfolio_id': 1,
            'instrument_id': 2,
            'symbol': 'MSFT',
            'nazwa_pelna': 'Microsoft Corporation',
            'ilosc_akcji': 5.0,
            'srednia_cena_zakupu': 300.00,
            'wartosc_zakupu': 1500.00,
            'wartosc_biezaca': 1400.00,
            'zysk_strata': -100.00,
            'zysk_strata_procent': -6.67
        }
    ]


@pytest.fixture
def sample_order():
    """Sample order data."""
    return {
        'order_id': 1,
        'portfolio_id': 1,
        'instrument_id': 1,
        'symbol': 'AAPL',
        'typ_zlecenia': 'MARKET',
        'strona_zlecenia': 'KUPNO',
        'ilosc': 10.0,
        'limit_ceny': None,
        'status': 'WYKONANE',
        'data_utworzenia': datetime(2025, 1, 15, 10, 30, 0)
    }


@pytest.fixture
def sample_pending_orders():
    """Sample pending orders list."""
    return [
        {
            'order_id': 1,
            'portfolio_id': 1,
            'instrument_id': 1,
            'symbol': 'AAPL',
            'typ_zlecenia': 'LIMIT',
            'strona_zlecenia': 'KUPNO',
            'ilosc': 10.0,
            'limit_ceny': 145.00,
            'status': 'OCZEKUJACE',
            'data_utworzenia': datetime(2025, 1, 15, 10, 30, 0)
        }
    ]


@pytest.fixture
def sample_transaction():
    """Sample transaction data."""
    return {
        'transaction_id': 1,
        'order_id': 1,
        'portfolio_id': 1,
        'instrument_id': 1,
        'symbol': 'AAPL',
        'typ_transakcji': 'KUPNO',
        'ilosc': 10.0,
        'cena_jednostkowa': 150.00,
        'wartosc_transakcji': 1500.00,
        'prowizja': 5.85,
        'waluta_transakcji': 'USD',
        'data_transakcji': datetime(2025, 1, 15, 10, 30, 0)
    }


@pytest.fixture
def sample_price_data():
    """Sample price data (OHLCV)."""
    return {
        'data_id': 1,
        'instrument_id': 1,
        'data_notowan': date(2025, 1, 15),
        'cena_otwarcia': 148.00,
        'cena_max': 152.00,
        'cena_min': 147.50,
        'cena_zamkniecia': 150.00,
        'wolumen': 1000000
    }


# ============================================
# INTEGRATION TEST FIXTURES
# ============================================

@pytest.fixture(scope="session")
def db_connection_string():
    """Get database connection string from environment."""
    host = os.environ.get('ORACLE_HOST', 'localhost')
    port = os.environ.get('ORACLE_PORT', '1521')
    service = os.environ.get('ORACLE_SERVICE', 'XEPDB1')
    user = os.environ.get('ORACLE_USER', 'gielda')
    password = os.environ.get('ORACLE_PASSWORD', 'gielda')

    return f"{user}/{password}@{host}:{port}/{service}"


@pytest.fixture
def integration_skip():
    """Skip integration tests if DB is not available."""
    if not os.environ.get('RUN_INTEGRATION_TESTS'):
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to run.")


# ============================================
# HELPER FUNCTIONS
# ============================================

def create_mock_cursor_var(value):
    """Create a mock cursor variable that returns a value."""
    mock_var = MagicMock()
    mock_var.getvalue.return_value = value
    return mock_var
