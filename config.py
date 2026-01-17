"""
Configuration settings for the Stock Exchange Simulation application.
"""

import os

# Database connection settings
DB_CONFIG = {
    'host': os.environ.get('ORACLE_HOST', 'localhost'),
    'port': int(os.environ.get('ORACLE_PORT', 1521)),
    'service_name': os.environ.get('ORACLE_SERVICE', 'XEPDB1'),
    'user': os.environ.get('ORACLE_USER', 'system'),
    'password': os.environ.get('ORACLE_PASSWORD', 'YourPassword123'),
}

# Connection string format for oracledb
def get_connection_string() -> str:
    """Get Oracle connection string in DSN format."""
    return f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}"

# Application settings
APP_CONFIG = {
    'title': 'Symulator Giełdy',
    'page_icon': ':chart_with_upwards_trend:',
    'layout': 'wide',
    'default_currency': 'USD',
    'commission_rate': 0.0039,  # 0.39%
}

# Supported currencies
SUPPORTED_CURRENCIES = ['USD']

# Order types
ORDER_TYPES = {
    'MARKET': 'Rynkowe (natychmiastowe)',
    'LIMIT': 'Z limitem ceny',
}

# Order sides
ORDER_SIDES = {
    'KUPNO': 'Kupno',
    'SPRZEDAZ': 'Sprzedaż',
}

# Order statuses
ORDER_STATUSES = {
    'OCZEKUJACE': 'Oczekujące',
    'WYKONANE': 'Wykonane',
    'ANULOWANE': 'Anulowane',
    'CZESCIOWE': 'Częściowo wykonane',
}

# Instrument types
INSTRUMENT_TYPES = {
    'AKCJE': 'Akcje',
    'ETF': 'ETF',
    'INDEKS': 'Indeks',
    'OBLIGACJE': 'Obligacje',
}
