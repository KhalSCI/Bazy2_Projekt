"""
Yahoo Finance API wrapper for fetching stock data.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, date
from typing import Optional

# Default stock symbols for US market
DEFAULT_US_STOCKS = {
    # Technology
    'AAPL': ('Apple Inc.', 'TECH'),
    'MSFT': ('Microsoft Corporation', 'TECH'),
    'GOOGL': ('Alphabet Inc.', 'TECH'),
    'NVDA': ('NVIDIA Corporation', 'TECH'),
    'META': ('Meta Platforms Inc.', 'TECH'),
    # Finance
    'JPM': ('JPMorgan Chase & Co.', 'FIN'),
    'BAC': ('Bank of America Corp.', 'FIN'),
    'GS': ('Goldman Sachs Group Inc.', 'FIN'),
    # Healthcare
    'JNJ': ('Johnson & Johnson', 'HEALTH'),
    'PFE': ('Pfizer Inc.', 'HEALTH'),
    'UNH': ('UnitedHealth Group Inc.', 'HEALTH'),
    # Consumer
    'AMZN': ('Amazon.com Inc.', 'CONS'),
    'WMT': ('Walmart Inc.', 'CONS'),
    'KO': ('Coca-Cola Company', 'CONS'),
    # Energy
    'XOM': ('Exxon Mobil Corporation', 'ENERGY'),
    'CVX': ('Chevron Corporation', 'ENERGY'),
}

# Sector definitions
SECTOR_DEFINITIONS = {
    'TECH': ('Technologia', 'Sektor technologiczny'),
    'FIN': ('Finanse', 'Sektor finansowy'),
    'HEALTH': ('Ochrona zdrowia', 'Sektor medyczny'),
    'CONS': ('Konsumpcja', 'Sektor dóbr konsumpcyjnych'),
    'ENERGY': ('Energia', 'Sektor energetyczny'),
}


def fetch_stock_data(symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    Fetch historical OHLCV data for a single stock from Yahoo Finance.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format

    Returns:
        DataFrame with columns: Date, Open, High, Low, Close, Volume
        or None if fetch fails
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            return None

        # Reset index to make Date a column
        df = df.reset_index()

        # Rename columns to standard names
        df = df.rename(columns={
            'Date': 'data',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })

        # Keep only needed columns
        df = df[['data', 'open', 'high', 'low', 'close', 'volume']]

        # Convert date to date only (remove time)
        df['data'] = pd.to_datetime(df['data']).dt.date

        # Round prices to 4 decimal places and convert to native Python float
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].round(4).astype(float)

        # Convert volume to native Python int (not numpy.int64)
        df['volume'] = df['volume'].astype(int).apply(lambda x: int(x))

        return df

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def fetch_multiple_stocks(symbols: list, start_date: str,
                          end_date: str) -> dict[str, pd.DataFrame]:
    """
    Fetch historical data for multiple stocks.

    Args:
        symbols: List of stock ticker symbols
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format

    Returns:
        Dictionary mapping symbol to DataFrame
    """
    results = {}
    for symbol in symbols:
        df = fetch_stock_data(symbol, start_date, end_date)
        if df is not None and not df.empty:
            results[symbol] = df
    return results


def get_stock_info(symbol: str) -> Optional[dict]:
    """
    Get basic info about a stock.

    Returns dict with: name, currency, exchange, sector
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        return {
            'name': info.get('longName', info.get('shortName', symbol)),
            'currency': info.get('currency', 'USD'),
            'exchange': info.get('exchange', 'UNKNOWN'),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
        }
    except Exception as e:
        print(f"Error getting info for {symbol}: {e}")
        return None


def get_current_quote(symbol: str) -> Optional[dict]:
    """
    Get current quote for a stock.

    Returns dict with: price, change, change_percent, volume
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose')

        if current_price is None:
            # Try to get from history
            hist = ticker.history(period='1d')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]

        if current_price is None:
            return None

        change = 0
        change_percent = 0
        if previous_close and current_price:
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100

        return {
            'price': round(current_price, 4),
            'previous_close': round(previous_close, 4) if previous_close else None,
            'change': round(change, 4),
            'change_percent': round(change_percent, 2),
            'volume': info.get('volume', 0),
        }
    except Exception as e:
        print(f"Error getting quote for {symbol}: {e}")
        return None


def validate_symbol(symbol: str) -> bool:
    """Check if a stock symbol is valid."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        # Check if we got valid data
        return info.get('regularMarketPrice') is not None or \
               info.get('currentPrice') is not None
    except Exception:
        return False


def get_default_stocks() -> dict:
    """Get the default US stocks dictionary."""
    return DEFAULT_US_STOCKS.copy()


def get_sector_definitions() -> dict:
    """Get sector definitions."""
    return SECTOR_DEFINITIONS.copy()


def get_2025_date_range() -> tuple[str, str]:
    """Get date range from 2025 until today."""
    today = date.today()

    # Start from 2025
    start = "2025-01-01"

    # End date is today
    end = today.strftime('%Y-%m-%d')

    return start, end
