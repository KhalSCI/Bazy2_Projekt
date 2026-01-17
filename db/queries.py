"""
SQL query templates for SELECT operations.
"""


class Queries:
    """SQL SELECT query templates."""

    # ===================
    # USER QUERIES
    # ===================

    GET_USER_BY_LOGIN = """
        SELECT user_id, login, haslo, email, imie, nazwisko,
               data_rejestracji, waluta_bazowa
        FROM UZYTKOWNICY
        WHERE login = :login
    """

    GET_USER_BY_ID = """
        SELECT user_id, login, haslo, email, imie, nazwisko,
               data_rejestracji, waluta_bazowa
        FROM UZYTKOWNICY
        WHERE user_id = :user_id
    """

    GET_ALL_USERS = """
        SELECT user_id, login, email, imie, nazwisko,
               data_rejestracji, waluta_bazowa
        FROM UZYTKOWNICY
        ORDER BY login
    """

    # ===================
    # PORTFOLIO QUERIES
    # ===================

    GET_PORTFOLIOS_BY_USER = """
        SELECT portfolio_id, user_id, nazwa_portfela, data_utworzenia,
               saldo_gotowkowe, waluta_portfela
        FROM PORTFELE
        WHERE user_id = :user_id
        ORDER BY data_utworzenia DESC
    """

    GET_PORTFOLIO_BY_ID = """
        SELECT portfolio_id, user_id, nazwa_portfela, data_utworzenia,
               saldo_gotowkowe, waluta_portfela
        FROM PORTFELE
        WHERE portfolio_id = :portfolio_id
    """

    GET_PORTFOLIO_SUMMARY = """
        SELECT p.portfolio_id, p.nazwa_portfela, p.saldo_gotowkowe,
               p.waluta_portfela, p.data_utworzenia,
               NVL(SUM(poz.wartosc_biezaca), 0) as wartosc_pozycji,
               NVL(SUM(poz.zysk_strata), 0) as zysk_strata_pozycji,
               COUNT(poz.position_id) as liczba_pozycji
        FROM PORTFELE p
        LEFT JOIN POZYCJE poz ON p.portfolio_id = poz.portfolio_id AND poz.ilosc_akcji > 0
        WHERE p.portfolio_id = :portfolio_id
        GROUP BY p.portfolio_id, p.nazwa_portfela, p.saldo_gotowkowe,
                 p.waluta_portfela, p.data_utworzenia
    """

    # ===================
    # POSITION QUERIES
    # ===================

    GET_POSITIONS_BY_PORTFOLIO = """
        SELECT poz.position_id, poz.portfolio_id, poz.instrument_id,
               poz.ilosc_akcji, poz.srednia_cena_zakupu, poz.wartosc_zakupu,
               poz.wartosc_biezaca, poz.zysk_strata, poz.zysk_strata_procent,
               poz.data_pierwszego_zakupu, poz.data_ostatniej_zmiany,
               i.symbol, i.nazwa_pelna, i.waluta_notowania
        FROM POZYCJE poz
        JOIN INSTRUMENTY i ON poz.instrument_id = i.instrument_id
        WHERE poz.portfolio_id = :portfolio_id
          AND poz.ilosc_akcji > 0
        ORDER BY poz.wartosc_biezaca DESC
    """

    GET_POSITION_BY_INSTRUMENT = """
        SELECT poz.position_id, poz.portfolio_id, poz.instrument_id,
               poz.ilosc_akcji, poz.srednia_cena_zakupu, poz.wartosc_zakupu,
               poz.wartosc_biezaca, poz.zysk_strata, poz.zysk_strata_procent,
               i.symbol, i.nazwa_pelna
        FROM POZYCJE poz
        JOIN INSTRUMENTY i ON poz.instrument_id = i.instrument_id
        WHERE poz.portfolio_id = :portfolio_id
          AND poz.instrument_id = :instrument_id
          AND poz.ilosc_akcji > 0
    """

    # ===================
    # INSTRUMENT QUERIES
    # ===================

    GET_ALL_INSTRUMENTS = """
        SELECT i.instrument_id, i.symbol, i.nazwa_pelna, i.exchange_id,
               i.sector_id, i.typ_instrumentu, i.waluta_notowania, i.status,
               g.kod_gieldy, g.nazwa_pelna as nazwa_gieldy,
               s.kod_sektora, s.nazwa_sektora
        FROM INSTRUMENTY i
        LEFT JOIN GIELDY g ON i.exchange_id = g.exchange_id
        LEFT JOIN SEKTORY s ON i.sector_id = s.sector_id
        WHERE i.status = 'AKTYWNY'
        ORDER BY i.symbol
    """

    GET_INSTRUMENT_BY_ID = """
        SELECT i.instrument_id, i.symbol, i.nazwa_pelna, i.exchange_id,
               i.sector_id, i.typ_instrumentu, i.waluta_notowania, i.status,
               g.kod_gieldy, s.nazwa_sektora
        FROM INSTRUMENTY i
        LEFT JOIN GIELDY g ON i.exchange_id = g.exchange_id
        LEFT JOIN SEKTORY s ON i.sector_id = s.sector_id
        WHERE i.instrument_id = :instrument_id
    """

    GET_INSTRUMENT_BY_SYMBOL = """
        SELECT i.instrument_id, i.symbol, i.nazwa_pelna, i.exchange_id,
               i.sector_id, i.typ_instrumentu, i.waluta_notowania, i.status
        FROM INSTRUMENTY i
        WHERE i.symbol = :symbol
    """

    GET_INSTRUMENTS_BY_SECTOR = """
        SELECT i.instrument_id, i.symbol, i.nazwa_pelna, i.waluta_notowania,
               s.nazwa_sektora
        FROM INSTRUMENTY i
        JOIN SEKTORY s ON i.sector_id = s.sector_id
        WHERE s.sector_id = :sector_id
          AND i.status = 'AKTYWNY'
        ORDER BY i.symbol
    """

    # ===================
    # PRICE DATA QUERIES
    # ===================

    GET_LATEST_PRICE = """
        SELECT cena_zamkniecia, data_notowan, cena_otwarcia,
               cena_max, cena_min, wolumen
        FROM DANE_DZIENNE
        WHERE instrument_id = :instrument_id
          AND data_notowan = (
              SELECT MAX(data_notowan)
              FROM DANE_DZIENNE
              WHERE instrument_id = :instrument_id
          )
    """

    GET_PRICE_FOR_DATE = """
        SELECT cena_zamkniecia, data_notowan, cena_otwarcia,
               cena_max, cena_min, wolumen
        FROM DANE_DZIENNE
        WHERE instrument_id = :instrument_id
          AND data_notowan <= :data_notowan
        ORDER BY data_notowan DESC
        FETCH FIRST 1 ROW ONLY
    """

    GET_PRICE_HISTORY = """
        SELECT data_notowan, cena_otwarcia, cena_max, cena_min,
               cena_zamkniecia, wolumen
        FROM DANE_DZIENNE
        WHERE instrument_id = :instrument_id
          AND data_notowan BETWEEN :start_date AND :end_date
        ORDER BY data_notowan
    """

    GET_ALL_PRICES_FOR_DATE = """
        SELECT d.instrument_id, i.symbol, i.nazwa_pelna,
               d.cena_zamkniecia, d.cena_otwarcia, d.cena_max, d.cena_min,
               d.wolumen, d.data_notowan
        FROM DANE_DZIENNE d
        JOIN INSTRUMENTY i ON d.instrument_id = i.instrument_id
        WHERE d.data_notowan = (
            SELECT MAX(d2.data_notowan)
            FROM DANE_DZIENNE d2
            WHERE d2.instrument_id = d.instrument_id
              AND d2.data_notowan <= :data_notowan
        )
          AND i.status = 'AKTYWNY'
        ORDER BY i.symbol
    """

    GET_AVAILABLE_DATES = """
        SELECT DISTINCT data_notowan
        FROM DANE_DZIENNE
        ORDER BY data_notowan DESC
    """

    GET_DATE_RANGE = """
        SELECT MIN(data_notowan) as min_date, MAX(data_notowan) as max_date
        FROM DANE_DZIENNE
    """

    # ===================
    # ORDER QUERIES
    # ===================

    GET_ORDERS_BY_PORTFOLIO = """
        SELECT z.order_id, z.portfolio_id, z.instrument_id, z.typ_zlecenia,
               z.strona_zlecenia, z.ilosc, z.limit_ceny, z.stop_cena,
               z.status, z.data_utworzenia, z.data_wygasniecia, z.data_wykonania,
               i.symbol, i.nazwa_pelna
        FROM ZLECENIA z
        JOIN INSTRUMENTY i ON z.instrument_id = i.instrument_id
        WHERE z.portfolio_id = :portfolio_id
        ORDER BY z.data_utworzenia DESC
    """

    GET_PENDING_ORDERS = """
        SELECT z.order_id, z.portfolio_id, z.instrument_id, z.typ_zlecenia,
               z.strona_zlecenia, z.ilosc, z.limit_ceny, z.stop_cena,
               z.status, z.data_utworzenia, z.data_wygasniecia,
               i.symbol, i.nazwa_pelna
        FROM ZLECENIA z
        JOIN INSTRUMENTY i ON z.instrument_id = i.instrument_id
        WHERE z.portfolio_id = :portfolio_id
          AND z.status = 'OCZEKUJACE'
        ORDER BY z.data_utworzenia DESC
    """

    GET_EXECUTED_ORDERS = """
        SELECT z.order_id, z.portfolio_id, z.instrument_id, z.typ_zlecenia,
               z.strona_zlecenia, z.ilosc, z.limit_ceny, z.status,
               z.data_utworzenia, z.data_wykonania,
               i.symbol, i.nazwa_pelna
        FROM ZLECENIA z
        JOIN INSTRUMENTY i ON z.instrument_id = i.instrument_id
        WHERE z.portfolio_id = :portfolio_id
          AND z.status = 'WYKONANE'
        ORDER BY z.data_wykonania DESC
    """

    GET_ORDER_BY_ID = """
        SELECT z.order_id, z.portfolio_id, z.instrument_id, z.typ_zlecenia,
               z.strona_zlecenia, z.ilosc, z.limit_ceny, z.stop_cena,
               z.status, z.data_utworzenia, z.data_wygasniecia, z.data_wykonania,
               i.symbol, i.nazwa_pelna
        FROM ZLECENIA z
        JOIN INSTRUMENTY i ON z.instrument_id = i.instrument_id
        WHERE z.order_id = :order_id
    """

    # ===================
    # TRANSACTION QUERIES
    # ===================

    GET_TRANSACTIONS_BY_PORTFOLIO = """
        SELECT t.transaction_id, t.order_id, t.typ_transakcji, t.ilosc,
               t.cena_jednostkowa, t.wartosc_transakcji, t.prowizja,
               t.data_transakcji, t.waluta_transakcji,
               z.instrument_id, i.symbol, i.nazwa_pelna
        FROM TRANSAKCJE t
        JOIN ZLECENIA z ON t.order_id = z.order_id
        JOIN INSTRUMENTY i ON z.instrument_id = i.instrument_id
        WHERE z.portfolio_id = :portfolio_id
        ORDER BY t.data_transakcji DESC
    """

    GET_TRANSACTIONS_BY_DATE_RANGE = """
        SELECT t.transaction_id, t.order_id, t.typ_transakcji, t.ilosc,
               t.cena_jednostkowa, t.wartosc_transakcji, t.prowizja,
               t.data_transakcji, t.waluta_transakcji,
               z.instrument_id, i.symbol, i.nazwa_pelna
        FROM TRANSAKCJE t
        JOIN ZLECENIA z ON t.order_id = z.order_id
        JOIN INSTRUMENTY i ON z.instrument_id = i.instrument_id
        WHERE z.portfolio_id = :portfolio_id
          AND TRUNC(t.data_transakcji) BETWEEN :start_date AND :end_date
        ORDER BY t.data_transakcji DESC
    """

    # ===================
    # SECTOR QUERIES
    # ===================

    GET_ALL_SECTORS = """
        SELECT sector_id, kod_sektora, nazwa_sektora, nazwa_branza, opis
        FROM SEKTORY
        ORDER BY nazwa_sektora
    """

    GET_SECTOR_BY_CODE = """
        SELECT sector_id, kod_sektora, nazwa_sektora, nazwa_branza, opis
        FROM SEKTORY
        WHERE kod_sektora = :kod_sektora
    """

    # ===================
    # EXCHANGE QUERIES
    # ===================

    GET_ALL_EXCHANGES = """
        SELECT exchange_id, kod_gieldy, nazwa_pelna, kraj, miasto,
               strefa_czasowa, waluta_podstawowa, godzina_otwarcia, godzina_zamkniecia
        FROM GIELDY
        ORDER BY kod_gieldy
    """

    GET_EXCHANGE_BY_CODE = """
        SELECT exchange_id, kod_gieldy, nazwa_pelna, kraj, miasto,
               strefa_czasowa, waluta_podstawowa
        FROM GIELDY
        WHERE kod_gieldy = :kod_gieldy
    """

    # ===================
    # STATISTICS QUERIES
    # ===================

    GET_PORTFOLIO_PERFORMANCE = """
        SELECT
            TRUNC(t.data_transakcji) as dzien,
            SUM(CASE WHEN t.typ_transakcji = 'KUPNO'
                THEN t.wartosc_transakcji + t.prowizja ELSE 0 END) as wydatki,
            SUM(CASE WHEN t.typ_transakcji = 'SPRZEDAZ'
                THEN t.wartosc_transakcji - t.prowizja ELSE 0 END) as przychody,
            SUM(t.prowizja) as prowizje
        FROM TRANSAKCJE t
        JOIN ZLECENIA z ON t.order_id = z.order_id
        WHERE z.portfolio_id = :portfolio_id
        GROUP BY TRUNC(t.data_transakcji)
        ORDER BY dzien
    """

    GET_INSTRUMENT_COUNT_BY_SECTOR = """
        SELECT s.nazwa_sektora, COUNT(i.instrument_id) as liczba_instrumentow
        FROM SEKTORY s
        LEFT JOIN INSTRUMENTY i ON s.sector_id = i.sector_id AND i.status = 'AKTYWNY'
        GROUP BY s.nazwa_sektora
        ORDER BY liczba_instrumentow DESC
    """

    # ===================
    # TRADING DAYS QUERIES
    # ===================

    GET_TRADING_DAYS_BETWEEN = """
        SELECT DISTINCT data_notowan
        FROM DANE_DZIENNE
        WHERE data_notowan > :start_date
          AND data_notowan <= :end_date
        ORDER BY data_notowan ASC
    """
