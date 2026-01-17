"""
Market data service.
"""

from typing import Optional, List, Dict, Tuple
from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import execute_query_dict, execute_query
from db.queries import Queries
from db.procedures import Procedures


class MarketService:
    """Service for market data operations."""

    @staticmethod
    def get_all_instruments() -> List[Dict]:
        """Get all active instruments."""
        return execute_query_dict(Queries.GET_ALL_INSTRUMENTS)

    @staticmethod
    def get_instrument_by_id(instrument_id: int) -> Optional[Dict]:
        """Get instrument details by ID."""
        results = execute_query_dict(
            Queries.GET_INSTRUMENT_BY_ID,
            {'instrument_id': instrument_id}
        )
        return results[0] if results else None

    @staticmethod
    def get_instrument_by_symbol(symbol: str) -> Optional[Dict]:
        """Get instrument details by symbol."""
        results = execute_query_dict(
            Queries.GET_INSTRUMENT_BY_SYMBOL,
            {'symbol': symbol}
        )
        return results[0] if results else None

    @staticmethod
    def get_instruments_by_sector(sector_id: int) -> List[Dict]:
        """Get instruments in a specific sector."""
        return execute_query_dict(
            Queries.GET_INSTRUMENTS_BY_SECTOR,
            {'sector_id': sector_id}
        )

    @staticmethod
    def get_all_sectors() -> List[Dict]:
        """Get all sectors."""
        return execute_query_dict(Queries.GET_ALL_SECTORS)

    @staticmethod
    def get_all_exchanges() -> List[Dict]:
        """Get all exchanges."""
        return execute_query_dict(Queries.GET_ALL_EXCHANGES)

    @staticmethod
    def get_current_price(instrument_id: int) -> Optional[float]:
        """Get current (latest) price for an instrument."""
        return Procedures.get_current_price(instrument_id)

    @staticmethod
    def get_price_for_date(instrument_id: int, target_date: date) -> Optional[float]:
        """Get price for a specific date."""
        return Procedures.get_price_for_date(instrument_id, target_date)

    @staticmethod
    def get_latest_price_data(instrument_id: int) -> Optional[Dict]:
        """Get latest OHLCV data for an instrument."""
        results = execute_query_dict(
            Queries.GET_LATEST_PRICE,
            {'instrument_id': instrument_id}
        )
        return results[0] if results else None

    @staticmethod
    def get_price_data_for_date(instrument_id: int, target_date: date) -> Optional[Dict]:
        """Get OHLCV data for a specific date."""
        results = execute_query_dict(
            Queries.GET_PRICE_FOR_DATE,
            {'instrument_id': instrument_id, 'data_notowan': target_date}
        )
        return results[0] if results else None

    @staticmethod
    def get_price_history(instrument_id: int, start_date: date, end_date: date) -> List[Dict]:
        """Get price history for a date range."""
        return execute_query_dict(
            Queries.GET_PRICE_HISTORY,
            {
                'instrument_id': instrument_id,
                'start_date': start_date,
                'end_date': end_date
            }
        )

    @staticmethod
    def get_all_prices_for_date(target_date: date) -> List[Dict]:
        """Get prices for all instruments for a specific date."""
        return execute_query_dict(
            Queries.GET_ALL_PRICES_FOR_DATE,
            {'data_notowan': target_date}
        )

    @staticmethod
    def get_available_dates() -> List[date]:
        """Get all dates with available price data."""
        results = execute_query(Queries.GET_AVAILABLE_DATES)
        return [row[0] for row in results]

    @staticmethod
    def get_date_range() -> Tuple[Optional[date], Optional[date]]:
        """Get min and max dates with price data."""
        results = execute_query(Queries.GET_DATE_RANGE)
        if results and results[0]:
            return results[0][0], results[0][1]
        return None, None

    @staticmethod
    def get_trading_days_between(start_date: date, end_date: date) -> List[date]:
        """Get all trading days between two dates (exclusive start, inclusive end)."""
        results = execute_query(
            Queries.GET_TRADING_DAYS_BETWEEN,
            {'start_date': start_date, 'end_date': end_date}
        )
        return [row[0] for row in results]

    @staticmethod
    def get_instruments_with_prices(target_date: date = None) -> List[Dict]:
        """
        Get all instruments with their current prices.
        If target_date is provided, uses prices from that date.
        """
        instruments = MarketService.get_all_instruments()

        for inst in instruments:
            instrument_id = inst['instrument_id']

            if target_date:
                price_data = MarketService.get_price_data_for_date(instrument_id, target_date)
            else:
                price_data = MarketService.get_latest_price_data(instrument_id)

            if price_data:
                inst['cena_zamkniecia'] = price_data.get('cena_zamkniecia')
                inst['cena_otwarcia'] = price_data.get('cena_otwarcia')
                inst['cena_max'] = price_data.get('cena_max')
                inst['cena_min'] = price_data.get('cena_min')
                inst['wolumen'] = price_data.get('wolumen')
                inst['data_notowan'] = price_data.get('data_notowan')

                # Calculate daily change
                if price_data.get('cena_otwarcia') and price_data.get('cena_zamkniecia'):
                    open_price = float(price_data['cena_otwarcia'])
                    close_price = float(price_data['cena_zamkniecia'])
                    inst['zmiana'] = close_price - open_price
                    if open_price > 0:
                        inst['zmiana_procent'] = ((close_price - open_price) / open_price) * 100
                    else:
                        inst['zmiana_procent'] = 0
                else:
                    inst['zmiana'] = 0
                    inst['zmiana_procent'] = 0
            else:
                inst['cena_zamkniecia'] = None
                inst['zmiana'] = None
                inst['zmiana_procent'] = None

        return instruments
