"""
Data loader service for loading Yahoo Finance data into the database.
"""

from typing import Optional, List, Dict, Tuple
from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import get_db_connection, execute_query_dict, execute_dml
from utils.yahoo_finance import (
    get_default_stocks, get_sector_definitions, fetch_multiple_stocks,
    get_2025_date_range
)


class DataLoader:
    """Service for loading market data into the database."""

    @staticmethod
    def initialize_exchange(code: str = 'NYSE', name: str = 'New York Stock Exchange',
                           country: str = 'USA', city: str = 'New York',
                           timezone: str = 'America/New_York', currency: str = 'USD',
                           open_time: str = '09:30', close_time: str = '16:00') -> Tuple[bool, str, Optional[int]]:
        """
        Initialize exchange in database.

        Returns:
            Tuple of (success, message, exchange_id)
        """
        try:
            # Check if exchange exists
            existing = execute_query_dict(
                "SELECT exchange_id FROM GIELDY WHERE kod_gieldy = :code",
                {'code': code}
            )

            if existing:
                return True, f"Giełda {code} już istnieje", existing[0]['exchange_id']

            # Insert new exchange
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO GIELDY (kod_gieldy, nazwa_pelna, kraj, miasto,
                                       strefa_czasowa, waluta_podstawowa,
                                       godzina_otwarcia, godzina_zamkniecia)
                    VALUES (:code, :name, :country, :city, :timezone,
                            :currency, :open_time, :close_time)
                    RETURNING exchange_id INTO :exchange_id
                """, {
                    'code': code, 'name': name, 'country': country,
                    'city': city, 'timezone': timezone, 'currency': currency,
                    'open_time': open_time, 'close_time': close_time,
                    'exchange_id': cursor.var(int)
                })
                exchange_id = cursor.var(int).getvalue()
                conn.commit()

                # Get the ID
                result = execute_query_dict(
                    "SELECT exchange_id FROM GIELDY WHERE kod_gieldy = :code",
                    {'code': code}
                )
                exchange_id = result[0]['exchange_id'] if result else None

                return True, f"Utworzono giełdę {code}", exchange_id

        except Exception as e:
            return False, f"Błąd podczas tworzenia giełdy: {str(e)}", None

    @staticmethod
    def initialize_sectors() -> Tuple[bool, str, Dict[str, int]]:
        """
        Initialize sectors from sector definitions.

        Returns:
            Tuple of (success, message, sector_id_map)
        """
        try:
            sectors = get_sector_definitions()
            sector_ids = {}
            created = 0
            existing = 0

            for code, (name, description) in sectors.items():
                # Check if exists
                result = execute_query_dict(
                    "SELECT sector_id FROM SEKTORY WHERE kod_sektora = :code",
                    {'code': code}
                )

                if result:
                    sector_ids[code] = result[0]['sector_id']
                    existing += 1
                else:
                    # Insert new sector
                    execute_dml("""
                        INSERT INTO SEKTORY (kod_sektora, nazwa_sektora, opis)
                        VALUES (:code, :name, :description)
                    """, {'code': code, 'name': name, 'description': description})

                    # Get ID
                    result = execute_query_dict(
                        "SELECT sector_id FROM SEKTORY WHERE kod_sektora = :code",
                        {'code': code}
                    )
                    if result:
                        sector_ids[code] = result[0]['sector_id']
                        created += 1

            message = f"Sektory: utworzono {created}, istniejące {existing}"
            return True, message, sector_ids

        except Exception as e:
            return False, f"Błąd podczas tworzenia sektorów: {str(e)}", {}

    @staticmethod
    def initialize_instruments(exchange_id: int, sector_ids: Dict[str, int]) -> Tuple[bool, str, Dict[str, int]]:
        """
        Initialize instruments from default stocks.

        Returns:
            Tuple of (success, message, instrument_id_map)
        """
        try:
            stocks = get_default_stocks()
            instrument_ids = {}
            created = 0
            existing = 0

            for symbol, (name, sector_code) in stocks.items():
                # Check if exists
                result = execute_query_dict(
                    "SELECT instrument_id FROM INSTRUMENTY WHERE symbol = :symbol",
                    {'symbol': symbol}
                )

                if result:
                    instrument_ids[symbol] = result[0]['instrument_id']
                    existing += 1
                else:
                    # Get sector ID
                    sector_id = sector_ids.get(sector_code)

                    # Insert new instrument
                    execute_dml("""
                        INSERT INTO INSTRUMENTY (symbol, nazwa_pelna, exchange_id,
                                                sector_id, typ_instrumentu,
                                                waluta_notowania, status)
                        VALUES (:symbol, :name, :exchange_id, :sector_id,
                                'AKCJE', 'USD', 'AKTYWNY')
                    """, {
                        'symbol': symbol,
                        'name': name,
                        'exchange_id': exchange_id,
                        'sector_id': sector_id
                    })

                    # Get ID
                    result = execute_query_dict(
                        "SELECT instrument_id FROM INSTRUMENTY WHERE symbol = :symbol",
                        {'symbol': symbol}
                    )
                    if result:
                        instrument_ids[symbol] = result[0]['instrument_id']
                        created += 1

            message = f"Instrumenty: utworzono {created}, istniejące {existing}"
            return True, message, instrument_ids

        except Exception as e:
            return False, f"Błąd podczas tworzenia instrumentów: {str(e)}", {}

    @staticmethod
    def load_price_data(instrument_ids: Dict[str, int],
                       start_date: str = None, end_date: str = None,
                       progress_callback=None) -> Tuple[bool, str]:
        """
        Load price data from Yahoo Finance.

        Args:
            instrument_ids: Map of symbol to instrument_id
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            progress_callback: Optional callback(current, total, symbol)

        Returns:
            Tuple of (success, message)
        """
        try:
            if not start_date or not end_date:
                start_date, end_date = get_2025_date_range()

            symbols = list(instrument_ids.keys())
            total = len(symbols)
            loaded_count = 0
            records_inserted = 0

            # Fetch data from Yahoo Finance
            stock_data = fetch_multiple_stocks(symbols, start_date, end_date)

            for idx, (symbol, df) in enumerate(stock_data.items()):
                if progress_callback:
                    progress_callback(idx + 1, total, symbol)

                instrument_id = instrument_ids.get(symbol)
                if not instrument_id:
                    continue

                # Insert each row
                for _, row in df.iterrows():
                    try:
                        # Check if data exists
                        existing = execute_query_dict("""
                            SELECT daily_data_id FROM DANE_DZIENNE
                            WHERE instrument_id = :instrument_id
                              AND data_notowan = :data_notowan
                        """, {
                            'instrument_id': instrument_id,
                            'data_notowan': row['data']
                        })

                        if not existing:
                            execute_dml("""
                                INSERT INTO DANE_DZIENNE (instrument_id, data_notowan,
                                    cena_otwarcia, cena_max, cena_min,
                                    cena_zamkniecia, wolumen)
                                VALUES (:instrument_id, :data_notowan,
                                    :open, :high, :low, :close, :volume)
                            """, {
                                'instrument_id': instrument_id,
                                'data_notowan': row['data'],
                                'open': float(row['open']),
                                'high': float(row['high']),
                                'low': float(row['low']),
                                'close': float(row['close']),
                                'volume': int(row['volume'])
                            })
                            records_inserted += 1

                    except Exception as row_error:
                        # Skip individual row errors
                        continue

                loaded_count += 1

            message = f"Załadowano dane dla {loaded_count}/{total} instrumentów. Dodano {records_inserted} rekordów."
            return True, message

        except Exception as e:
            return False, f"Błąd podczas ładowania danych: {str(e)}"

    @staticmethod
    def initialize_all(progress_callback=None) -> Tuple[bool, List[str]]:
        """
        Initialize all data (exchange, sectors, instruments, prices).

        Args:
            progress_callback: Optional callback(step, message)

        Returns:
            Tuple of (success, list of messages)
        """
        messages = []

        # Step 1: Initialize exchange
        if progress_callback:
            progress_callback(1, "Tworzenie giełdy...")
        success, msg, exchange_id = DataLoader.initialize_exchange()
        messages.append(msg)
        if not success:
            return False, messages

        # Step 2: Initialize sectors
        if progress_callback:
            progress_callback(2, "Tworzenie sektorów...")
        success, msg, sector_ids = DataLoader.initialize_sectors()
        messages.append(msg)
        if not success:
            return False, messages

        # Step 3: Initialize instruments
        if progress_callback:
            progress_callback(3, "Tworzenie instrumentów...")
        success, msg, instrument_ids = DataLoader.initialize_instruments(exchange_id, sector_ids)
        messages.append(msg)
        if not success:
            return False, messages

        # Step 4: Load price data
        if progress_callback:
            progress_callback(4, "Ładowanie danych cenowych...")

        def price_progress(current, total, symbol):
            if progress_callback:
                progress_callback(4, f"Ładowanie danych: {symbol} ({current}/{total})")

        success, msg = DataLoader.load_price_data(instrument_ids, progress_callback=price_progress)
        messages.append(msg)
        if not success:
            return False, messages

        return True, messages

    @staticmethod
    def check_data_status() -> Dict:
        """
        Check status of loaded data.

        Returns dict with:
        - exchanges_count: Number of exchanges
        - sectors_count: Number of sectors
        - instruments_count: Number of instruments
        - price_records_count: Number of price records
        - date_range: (min_date, max_date) or None
        """
        status = {}

        try:
            # Count exchanges
            result = execute_query_dict("SELECT COUNT(*) as cnt FROM GIELDY")
            status['exchanges_count'] = result[0]['cnt'] if result else 0

            # Count sectors
            result = execute_query_dict("SELECT COUNT(*) as cnt FROM SEKTORY")
            status['sectors_count'] = result[0]['cnt'] if result else 0

            # Count instruments
            result = execute_query_dict("SELECT COUNT(*) as cnt FROM INSTRUMENTY WHERE status = 'AKTYWNY'")
            status['instruments_count'] = result[0]['cnt'] if result else 0

            # Count price records
            result = execute_query_dict("SELECT COUNT(*) as cnt FROM DANE_DZIENNE")
            status['price_records_count'] = result[0]['cnt'] if result else 0

            # Get date range
            result = execute_query_dict("""
                SELECT MIN(data_notowan) as min_date, MAX(data_notowan) as max_date
                FROM DANE_DZIENNE
            """)
            if result and result[0]['min_date']:
                status['date_range'] = (result[0]['min_date'], result[0]['max_date'])
            else:
                status['date_range'] = None

            status['is_initialized'] = (
                status['exchanges_count'] > 0 and
                status['sectors_count'] > 0 and
                status['instruments_count'] > 0
            )

            status['has_price_data'] = status['price_records_count'] > 0

        except Exception as e:
            status['error'] = str(e)
            status['is_initialized'] = False
            status['has_price_data'] = False

        return status
