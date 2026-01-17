-- ============================================
--              SYMULATOR GIEŁDY
-- ============================================

-- CZĘŚĆ 1: TWORZENIE SEKWENCJI

CREATE SEQUENCE seq_uzytkownicy
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE SEQUENCE seq_gieldy
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE SEQUENCE seq_sektory
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE SEQUENCE seq_instrumenty
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE SEQUENCE seq_dane_dzienne
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE SEQUENCE seq_portfele
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE SEQUENCE seq_zlecenia
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE SEQUENCE seq_transakcje
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE SEQUENCE seq_pozycje
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

CREATE SEQUENCE seq_kursy_walut
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- CZĘŚĆ 2: TWORZENIE TABEL

-- Tabela: UZYTKOWNICY
-- Przechowuje dane użytkowników systemu
CREATE TABLE UZYTKOWNICY (
    user_id NUMBER DEFAULT seq_uzytkownicy.NEXTVAL PRIMARY KEY,
    login VARCHAR2(50) UNIQUE NOT NULL,
    haslo VARCHAR2(255) NOT NULL,
    email VARCHAR2(100) UNIQUE NOT NULL,
    imie VARCHAR2(50),
    nazwisko VARCHAR2(50),
    data_rejestracji DATE DEFAULT SYSDATE,
    waluta_bazowa VARCHAR2(3) DEFAULT 'PLN'
);
-- Tabela: GIELDY
-- Przechowuje informacje o giełdach papierów wartościowych
CREATE TABLE GIELDY (
    exchange_id NUMBER DEFAULT seq_gieldy.NEXTVAL PRIMARY KEY,
    kod_gieldy VARCHAR2(10) UNIQUE NOT NULL,
    nazwa_pelna VARCHAR2(100) NOT NULL,
    kraj VARCHAR2(50),
    miasto VARCHAR2(50),
    strefa_czasowa VARCHAR2(50),
    waluta_podstawowa VARCHAR2(3) NOT NULL,
    godzina_otwarcia VARCHAR2(5),
    godzina_zamkniecia VARCHAR2(5)
);

-- Tabela: SEKTORY
-- Przechowuje informacje o sektorach gospodarki
CREATE TABLE SEKTORY (
    sector_id NUMBER DEFAULT seq_sektory.NEXTVAL PRIMARY KEY,
    kod_sektora VARCHAR2(20) UNIQUE NOT NULL,
    nazwa_sektora VARCHAR2(100) NOT NULL,
    nazwa_branza VARCHAR2(100),
    opis VARCHAR2(500)
);

-- Tabela: INSTRUMENTY
-- Przechowuje informacje o instrumentach finansowych
CREATE TABLE INSTRUMENTY (
    instrument_id NUMBER DEFAULT seq_instrumenty.NEXTVAL PRIMARY KEY,
    symbol VARCHAR2(20) NOT NULL,
    nazwa_pelna VARCHAR2(200) NOT NULL,
    exchange_id NUMBER REFERENCES GIELDY(exchange_id),
    sector_id NUMBER REFERENCES SEKTORY(sector_id),
    typ_instrumentu VARCHAR2(20) CHECK (typ_instrumentu IN ('AKCJE', 'ETF', 'INDEKS', 'OBLIGACJE')),
    waluta_notowania VARCHAR2(3) NOT NULL,
    status VARCHAR2(20) DEFAULT 'AKTYWNY' CHECK (status IN ('AKTYWNY', 'ZAWIESZONY', 'WYCOFANY'))
);

-- Tabela: DANE_DZIENNE
-- Przechowuje dzienne notowania instrumentów
CREATE TABLE DANE_DZIENNE (
    daily_data_id NUMBER DEFAULT seq_dane_dzienne.NEXTVAL PRIMARY KEY,
    instrument_id NUMBER NOT NULL REFERENCES INSTRUMENTY(instrument_id),
    data_notowan DATE NOT NULL,
    cena_otwarcia NUMBER(15,4),
    cena_max NUMBER(15,4),
    cena_min NUMBER(15,4),
    cena_zamkniecia NUMBER(15,4) NOT NULL,
    wolumen NUMBER(20),
    CONSTRAINT uk_dane_dzienne UNIQUE(instrument_id, data_notowan),
    CONSTRAINT chk_ceny CHECK (cena_min <= cena_max)
);

-- Tabela: PORTFELE
-- Przechowuje portfele inwestycyjne użytkowników
CREATE TABLE PORTFELE (
    portfolio_id NUMBER DEFAULT seq_portfele.NEXTVAL PRIMARY KEY,
    user_id NUMBER NOT NULL REFERENCES UZYTKOWNICY(user_id),
    nazwa_portfela VARCHAR2(100) NOT NULL,
    data_utworzenia DATE DEFAULT SYSDATE,
    saldo_gotowkowe NUMBER(15,2) DEFAULT 0 CHECK (saldo_gotowkowe >= 0),
    waluta_portfela VARCHAR2(3) NOT NULL
);

-- Tabela: ZLECENIA
-- Przechowuje zlecenia giełdowe
CREATE TABLE ZLECENIA (
    order_id NUMBER DEFAULT seq_zlecenia.NEXTVAL PRIMARY KEY,
    portfolio_id NUMBER NOT NULL REFERENCES PORTFELE(portfolio_id),
    instrument_id NUMBER NOT NULL REFERENCES INSTRUMENTY(instrument_id),
    typ_zlecenia VARCHAR2(20) NOT NULL CHECK (typ_zlecenia IN ('MARKET', 'LIMIT', 'STOP')),
    strona_zlecenia VARCHAR2(10) NOT NULL CHECK (strona_zlecenia IN ('KUPNO', 'SPRZEDAZ')),
    ilosc NUMBER(15,4) NOT NULL CHECK (ilosc > 0),
    limit_ceny NUMBER(15,4),
    stop_cena NUMBER(15,4),
    status VARCHAR2(20) DEFAULT 'OCZEKUJACE' CHECK (status IN ('OCZEKUJACE', 'WYKONANE', 'ANULOWANE', 'CZESCIOWE')),
    data_utworzenia TIMESTAMP NOT NULL,
    data_wygasniecia DATE,
    data_wykonania TIMESTAMP
);

-- Tabela: TRANSAKCJE
-- Przechowuje wykonane transakcje
-- UWAGA: Relacja tylko z ZLECENIA (zgodnie ze specyfikacją)
CREATE TABLE TRANSAKCJE (
    transaction_id NUMBER DEFAULT seq_transakcje.NEXTVAL PRIMARY KEY,
    order_id NUMBER NOT NULL REFERENCES ZLECENIA(order_id),
    typ_transakcji VARCHAR2(10) NOT NULL CHECK (typ_transakcji IN ('KUPNO', 'SPRZEDAZ')),
    ilosc NUMBER(15,4) NOT NULL CHECK (ilosc > 0),
    cena_jednostkowa NUMBER(15,4) NOT NULL CHECK (cena_jednostkowa > 0),
    wartosc_transakcji NUMBER(15,2),
    prowizja NUMBER(10,2) DEFAULT 0,
    data_transakcji TIMESTAMP NOT NULL,
    waluta_transakcji VARCHAR2(3) NOT NULL
);

-- Tabela: POZYCJE
-- Przechowuje aktualne pozycje w portfelu
CREATE TABLE POZYCJE (
    position_id NUMBER DEFAULT seq_pozycje.NEXTVAL PRIMARY KEY,
    portfolio_id NUMBER NOT NULL REFERENCES PORTFELE(portfolio_id),
    instrument_id NUMBER NOT NULL REFERENCES INSTRUMENTY(instrument_id),
    ilosc_akcji NUMBER(15,4) NOT NULL CHECK (ilosc_akcji >= 0),
    srednia_cena_zakupu NUMBER(15,4) NOT NULL,
    wartosc_zakupu NUMBER(15,2),
    wartosc_biezaca NUMBER(15,2),
    zysk_strata NUMBER(15,2),
    zysk_strata_procent NUMBER(10,4),
    data_pierwszego_zakupu DATE,
    data_ostatniej_zmiany TIMESTAMP,
    CONSTRAINT uk_pozycje UNIQUE(portfolio_id, instrument_id)
);

-- Tabela: KURSY_WALUT
-- Przechowuje kursy wymiany walut
CREATE TABLE KURSY_WALUT (
    rate_id NUMBER DEFAULT seq_kursy_walut.NEXTVAL PRIMARY KEY,
    waluta_bazowa VARCHAR2(3) NOT NULL,
    waluta_docelowa VARCHAR2(3) NOT NULL,
    data_kursu DATE NOT NULL,
    kurs_kupna NUMBER(10,6),
    kurs_sprzedazy NUMBER(10,6),
    kurs_sredni NUMBER(10,6),
    data_aktualizacji TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT uk_kursy_walut UNIQUE(waluta_bazowa, waluta_docelowa, data_kursu),
    CONSTRAINT chk_kursy CHECK (kurs_kupna <= kurs_sprzedazy)
);

-- CZĘŚĆ 3: TWORZENIE INDEKSÓW

CREATE INDEX idx_instrumenty_symbol ON INSTRUMENTY(symbol);
CREATE INDEX idx_instrumenty_exchange ON INSTRUMENTY(exchange_id);
CREATE INDEX idx_dane_dzienne_data ON DANE_DZIENNE(data_notowan);
CREATE INDEX idx_portfele_user ON PORTFELE(user_id);
CREATE INDEX idx_zlecenia_portfolio ON ZLECENIA(portfolio_id);
CREATE INDEX idx_zlecenia_status ON ZLECENIA(status);
CREATE INDEX idx_transakcje_order ON TRANSAKCJE(order_id);
CREATE INDEX idx_transakcje_data ON TRANSAKCJE(data_transakcji);
CREATE INDEX idx_pozycje_portfolio ON POZYCJE(portfolio_id);


-- CZĘŚĆ 4: PAKIET Z PODPROGRAMAMI SKŁADOWANYMI

-- Specyfikacja pakietu
CREATE OR REPLACE PACKAGE pkg_gielda AS
    
    -- Stała: domyślna stawka prowizji (0.39%)
    c_prowizja_domyslna CONSTANT NUMBER := 0.0039;
    
    -- FUNKCJA: Oblicza całkowitą wartość portfela (gotówka + pozycje)
    FUNCTION oblicz_wartosc_portfela(
        p_portfolio_id IN NUMBER
    ) RETURN NUMBER;
    
    -- FUNKCJA: Oblicza procentowy zysk/stratę dla pozycji
    FUNCTION oblicz_zysk_procent(
        p_wartosc_zakupu IN NUMBER,
        p_wartosc_biezaca IN NUMBER
    ) RETURN NUMBER;
    
    -- FUNKCJA: Pobiera aktualną cenę instrumentu (ostatnia cena zamknięcia)
    FUNCTION pobierz_aktualna_cene(
        p_instrument_id IN NUMBER
    ) RETURN NUMBER;
    
    -- PROCEDURA: Realizuje zlecenie kupna
    PROCEDURE wykonaj_zlecenie_kupna(
        p_order_id IN NUMBER,
        p_cena_wykonania IN NUMBER,
        p_data_symulacji IN TIMESTAMP DEFAULT NULL,
        p_wynik OUT VARCHAR2
    );
    
    -- PROCEDURA: Realizuje zlecenie sprzedaży
    PROCEDURE wykonaj_zlecenie_sprzedazy(
        p_order_id IN NUMBER,
        p_cena_wykonania IN NUMBER,
        p_data_symulacji IN TIMESTAMP DEFAULT NULL,
        p_wynik OUT VARCHAR2
    );
    
    -- PROCEDURA: Aktualizuje wartości bieżące wszystkich pozycji w portfelu
    PROCEDURE aktualizuj_pozycje_portfela(
        p_portfolio_id IN NUMBER
    );
    
    -- PROCEDURA: Wpłata środków na portfel
    PROCEDURE wplac_srodki(
        p_portfolio_id IN NUMBER,
        p_kwota IN NUMBER,
        p_wynik OUT VARCHAR2
    );
    
END pkg_gielda;
/

CREATE OR REPLACE PACKAGE BODY pkg_gielda AS

    -- FUNKCJA: oblicz_wartosc_portfela
    FUNCTION oblicz_wartosc_portfela(
        p_portfolio_id IN NUMBER
    ) RETURN NUMBER IS
        v_wartosc_pozycji NUMBER := 0;
        v_saldo_gotowkowe NUMBER := 0;
        v_wartosc_calkowita NUMBER := 0;
    BEGIN
        -- Pobierz sumę wartości bieżących wszystkich pozycji
        SELECT NVL(SUM(wartosc_biezaca), 0)
        INTO v_wartosc_pozycji
        FROM POZYCJE
        WHERE portfolio_id = p_portfolio_id
          AND ilosc_akcji > 0;
        
        -- Pobierz saldo gotówkowe portfela
        SELECT NVL(saldo_gotowkowe, 0)
        INTO v_saldo_gotowkowe
        FROM PORTFELE
        WHERE portfolio_id = p_portfolio_id;
        
        -- Oblicz całkowitą wartość
        v_wartosc_calkowita := v_wartosc_pozycji + v_saldo_gotowkowe;
        
        RETURN ROUND(v_wartosc_calkowita, 2);
        
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 0;
        WHEN OTHERS THEN
            RAISE_APPLICATION_ERROR(-20001, 'Błąd podczas obliczania wartości portfela: ' || SQLERRM);
    END oblicz_wartosc_portfela;

    -- FUNKCJA: oblicz_zysk_procent
    FUNCTION oblicz_zysk_procent(
        p_wartosc_zakupu IN NUMBER,
        p_wartosc_biezaca IN NUMBER
    ) RETURN NUMBER IS
        v_zysk_procent NUMBER;
    BEGIN
        IF p_wartosc_zakupu IS NULL OR p_wartosc_zakupu = 0 THEN
            RETURN 0;
        END IF;
        
        v_zysk_procent := ((p_wartosc_biezaca - p_wartosc_zakupu) / p_wartosc_zakupu) * 100;
        
        RETURN ROUND(v_zysk_procent, 4);
        
    EXCEPTION
        WHEN OTHERS THEN
            RETURN 0;
    END oblicz_zysk_procent;

    -- FUNKCJA: pobierz_aktualna_cene

    FUNCTION pobierz_aktualna_cene(
        p_instrument_id IN NUMBER
    ) RETURN NUMBER IS
        v_cena NUMBER;
    BEGIN
        SELECT cena_zamkniecia
        INTO v_cena
        FROM DANE_DZIENNE
        WHERE instrument_id = p_instrument_id
          AND data_notowan = (
              SELECT MAX(data_notowan)
              FROM DANE_DZIENNE
              WHERE instrument_id = p_instrument_id
          );
        
        RETURN v_cena;
        
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN NULL;
        WHEN OTHERS THEN
            RAISE_APPLICATION_ERROR(-20002, 'Błąd podczas pobierania ceny: ' || SQLERRM);
    END pobierz_aktualna_cene;

    -- PROCEDURA: wykonaj_zlecenie_kupna
    PROCEDURE wykonaj_zlecenie_kupna(
        p_order_id IN NUMBER,
        p_cena_wykonania IN NUMBER,
        p_data_symulacji IN TIMESTAMP DEFAULT NULL,
        p_wynik OUT VARCHAR2
    ) IS
        v_portfolio_id NUMBER;
        v_instrument_id NUMBER;
        v_ilosc NUMBER;
        v_wartosc_transakcji NUMBER;
        v_prowizja NUMBER;
        v_koszt_calkowity NUMBER;
        v_saldo_portfela NUMBER;
        v_waluta VARCHAR2(3);
        v_pozycja_istnieje NUMBER;
        v_stara_ilosc NUMBER;
        v_stara_srednia NUMBER;
        v_nowa_ilosc NUMBER;
        v_nowa_srednia NUMBER;
        v_data_wykonania TIMESTAMP;
    BEGIN
        -- Użyj podanej daty lub aktualnego czasu
        v_data_wykonania := NVL(p_data_symulacji, SYSTIMESTAMP);
        -- Pobierz dane zlecenia
        SELECT portfolio_id, instrument_id, ilosc
        INTO v_portfolio_id, v_instrument_id, v_ilosc
        FROM ZLECENIA
        WHERE order_id = p_order_id 
          AND status = 'OCZEKUJACE'
          AND strona_zlecenia = 'KUPNO';
        
        -- Oblicz wartość i prowizję
        v_wartosc_transakcji := v_ilosc * p_cena_wykonania;
        v_prowizja := ROUND(v_wartosc_transakcji * c_prowizja_domyslna, 2);
        v_koszt_calkowity := v_wartosc_transakcji + v_prowizja;
        
        -- Pobierz saldo i walutę portfela
        SELECT saldo_gotowkowe, waluta_portfela
        INTO v_saldo_portfela, v_waluta
        FROM PORTFELE
        WHERE portfolio_id = v_portfolio_id;
        
        -- Sprawdź czy wystarczające środki
        IF v_saldo_portfela < v_koszt_calkowity THEN
            p_wynik := 'BŁĄD: Niewystarczające środki na koncie. Wymagane: ' || 
                       TO_CHAR(v_koszt_calkowity, '999999999.99') || ' ' || v_waluta;
            RETURN;
        END IF;
        
        -- Aktualizuj saldo portfela
        UPDATE PORTFELE
        SET saldo_gotowkowe = saldo_gotowkowe - v_koszt_calkowity
        WHERE portfolio_id = v_portfolio_id;
        
        -- Dodaj transakcję (bez portfolio_id i instrument_id - dane dostępne przez JOIN z ZLECENIA)
        INSERT INTO TRANSAKCJE (
            order_id, typ_transakcji,
            ilosc, cena_jednostkowa, wartosc_transakcji, prowizja,
            data_transakcji, waluta_transakcji
        ) VALUES (
            p_order_id, 'KUPNO',
            v_ilosc, p_cena_wykonania, v_wartosc_transakcji, v_prowizja,
            v_data_wykonania, v_waluta
        );
        
        -- Sprawdź czy istnieje pozycja
        SELECT COUNT(*), NVL(MAX(ilosc_akcji), 0), NVL(MAX(srednia_cena_zakupu), 0)
        INTO v_pozycja_istnieje, v_stara_ilosc, v_stara_srednia
        FROM POZYCJE
        WHERE portfolio_id = v_portfolio_id 
          AND instrument_id = v_instrument_id;
        
        IF v_pozycja_istnieje > 0 THEN
            -- Aktualizuj istniejącą pozycję (średnia ważona)
            v_nowa_ilosc := v_stara_ilosc + v_ilosc;
            v_nowa_srednia := ((v_stara_ilosc * v_stara_srednia) + (v_ilosc * p_cena_wykonania)) / v_nowa_ilosc;
            
            UPDATE POZYCJE
            SET ilosc_akcji = v_nowa_ilosc,
                srednia_cena_zakupu = ROUND(v_nowa_srednia, 4),
                wartosc_zakupu = ROUND(v_nowa_ilosc * v_nowa_srednia, 2),
                wartosc_biezaca = ROUND(v_nowa_ilosc * p_cena_wykonania, 2),
                zysk_strata = ROUND(v_nowa_ilosc * (p_cena_wykonania - v_nowa_srednia), 2),
                zysk_strata_procent = oblicz_zysk_procent(v_nowa_ilosc * v_nowa_srednia, v_nowa_ilosc * p_cena_wykonania),
                data_ostatniej_zmiany = v_data_wykonania
            WHERE portfolio_id = v_portfolio_id 
              AND instrument_id = v_instrument_id;
        ELSE
            -- Utwórz nową pozycję
            INSERT INTO POZYCJE (
                portfolio_id, instrument_id, ilosc_akcji, srednia_cena_zakupu,
                wartosc_zakupu, wartosc_biezaca, zysk_strata, zysk_strata_procent,
                data_pierwszego_zakupu, data_ostatniej_zmiany
            ) VALUES (
                v_portfolio_id, v_instrument_id, v_ilosc, p_cena_wykonania,
                v_wartosc_transakcji, v_wartosc_transakcji, 0, 0,
                TRUNC(v_data_wykonania), v_data_wykonania
            );
        END IF;
        
        -- Aktualizuj status zlecenia
        UPDATE ZLECENIA
        SET status = 'WYKONANE',
            data_wykonania = v_data_wykonania
        WHERE order_id = p_order_id;
        
        COMMIT;
        
        p_wynik := 'OK: Zlecenie kupna wykonane. Kupiono ' || v_ilosc || 
                   ' szt. po ' || p_cena_wykonania || ' ' || v_waluta ||
                   '. Prowizja: ' || v_prowizja || ' ' || v_waluta;
        
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            p_wynik := 'BŁĄD: Nie znaleziono oczekującego zlecenia kupna o podanym ID';
            ROLLBACK;
        WHEN OTHERS THEN
            p_wynik := 'BŁĄD: ' || SQLERRM;
            ROLLBACK;
    END wykonaj_zlecenie_kupna;

    -- PROCEDURA: wykonaj_zlecenie_sprzedazy
    PROCEDURE wykonaj_zlecenie_sprzedazy(
        p_order_id IN NUMBER,
        p_cena_wykonania IN NUMBER,
        p_data_symulacji IN TIMESTAMP DEFAULT NULL,
        p_wynik OUT VARCHAR2
    ) IS
        v_portfolio_id NUMBER;
        v_instrument_id NUMBER;
        v_ilosc NUMBER;
        v_wartosc_transakcji NUMBER;
        v_prowizja NUMBER;
        v_przychod_netto NUMBER;
        v_waluta VARCHAR2(3);
        v_posiadana_ilosc NUMBER;
        v_srednia_cena NUMBER;
        v_data_wykonania TIMESTAMP;
    BEGIN
        -- Użyj podanej daty lub aktualnego czasu
        v_data_wykonania := NVL(p_data_symulacji, SYSTIMESTAMP);
        -- Pobierz dane zlecenia
        SELECT portfolio_id, instrument_id, ilosc
        INTO v_portfolio_id, v_instrument_id, v_ilosc
        FROM ZLECENIA
        WHERE order_id = p_order_id 
          AND status = 'OCZEKUJACE'
          AND strona_zlecenia = 'SPRZEDAZ';
        
        -- Pobierz walutę portfela
        SELECT waluta_portfela
        INTO v_waluta
        FROM PORTFELE
        WHERE portfolio_id = v_portfolio_id;
        
        -- Sprawdź czy mamy wystarczającą ilość akcji
        BEGIN
            SELECT ilosc_akcji, srednia_cena_zakupu
            INTO v_posiadana_ilosc, v_srednia_cena
            FROM POZYCJE
            WHERE portfolio_id = v_portfolio_id 
              AND instrument_id = v_instrument_id;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                p_wynik := 'BŁĄD: Brak pozycji w tym instrumencie';
                RETURN;
        END;
        
        IF v_posiadana_ilosc < v_ilosc THEN
            p_wynik := 'BŁĄD: Niewystarczająca ilość akcji. Posiadasz: ' || v_posiadana_ilosc;
            RETURN;
        END IF;
        
        -- Oblicz wartość i prowizję
        v_wartosc_transakcji := v_ilosc * p_cena_wykonania;
        v_prowizja := ROUND(v_wartosc_transakcji * c_prowizja_domyslna, 2);
        v_przychod_netto := v_wartosc_transakcji - v_prowizja;
        
        -- Aktualizuj saldo portfela
        UPDATE PORTFELE
        SET saldo_gotowkowe = saldo_gotowkowe + v_przychod_netto
        WHERE portfolio_id = v_portfolio_id;
        
        -- Dodaj transakcję (bez portfolio_id i instrument_id - dane dostępne przez JOIN z ZLECENIA)
        INSERT INTO TRANSAKCJE (
            order_id, typ_transakcji,
            ilosc, cena_jednostkowa, wartosc_transakcji, prowizja,
            data_transakcji, waluta_transakcji
        ) VALUES (
            p_order_id, 'SPRZEDAZ',
            v_ilosc, p_cena_wykonania, v_wartosc_transakcji, v_prowizja,
            v_data_wykonania, v_waluta
        );
        
        -- Aktualizuj pozycję
        IF v_posiadana_ilosc = v_ilosc THEN
            -- Sprzedaż całej pozycji - usuń rekord
            DELETE FROM POZYCJE
            WHERE portfolio_id = v_portfolio_id 
              AND instrument_id = v_instrument_id;
        ELSE
            -- Częściowa sprzedaż - aktualizuj ilość
            UPDATE POZYCJE
            SET ilosc_akcji = ilosc_akcji - v_ilosc,
                wartosc_zakupu = ROUND((ilosc_akcji - v_ilosc) * srednia_cena_zakupu, 2),
                wartosc_biezaca = ROUND((ilosc_akcji - v_ilosc) * p_cena_wykonania, 2),
                zysk_strata = ROUND((ilosc_akcji - v_ilosc) * (p_cena_wykonania - srednia_cena_zakupu), 2),
                data_ostatniej_zmiany = v_data_wykonania
            WHERE portfolio_id = v_portfolio_id 
              AND instrument_id = v_instrument_id;
        END IF;
        
        -- Aktualizuj status zlecenia
        UPDATE ZLECENIA
        SET status = 'WYKONANE',
            data_wykonania = v_data_wykonania
        WHERE order_id = p_order_id;
        
        COMMIT;
        
        p_wynik := 'OK: Zlecenie sprzedaży wykonane. Sprzedano ' || v_ilosc || 
                   ' szt. po ' || p_cena_wykonania || ' ' || v_waluta ||
                   '. Przychód netto: ' || v_przychod_netto || ' ' || v_waluta;
        
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            p_wynik := 'BŁĄD: Nie znaleziono oczekującego zlecenia sprzedaży o podanym ID';
            ROLLBACK;
        WHEN OTHERS THEN
            p_wynik := 'BŁĄD: ' || SQLERRM;
            ROLLBACK;
    END wykonaj_zlecenie_sprzedazy;

    -- PROCEDURA: aktualizuj_pozycje_portfela
    PROCEDURE aktualizuj_pozycje_portfela(
        p_portfolio_id IN NUMBER
    ) IS
        v_aktualna_cena NUMBER;
    BEGIN
        -- Aktualizuj każdą pozycję w portfelu
        FOR pozycja IN (
            SELECT position_id, instrument_id, ilosc_akcji, srednia_cena_zakupu
            FROM POZYCJE
            WHERE portfolio_id = p_portfolio_id
              AND ilosc_akcji > 0
        ) LOOP
            -- Pobierz aktualną cenę
            v_aktualna_cena := pobierz_aktualna_cene(pozycja.instrument_id);
            
            IF v_aktualna_cena IS NOT NULL THEN
                UPDATE POZYCJE
                SET wartosc_biezaca = ROUND(pozycja.ilosc_akcji * v_aktualna_cena, 2),
                    zysk_strata = ROUND(pozycja.ilosc_akcji * (v_aktualna_cena - pozycja.srednia_cena_zakupu), 2),
                    zysk_strata_procent = oblicz_zysk_procent(
                        pozycja.ilosc_akcji * pozycja.srednia_cena_zakupu,
                        pozycja.ilosc_akcji * v_aktualna_cena
                    ),
                    data_ostatniej_zmiany = SYSTIMESTAMP
                WHERE position_id = pozycja.position_id;
            END IF;
        END LOOP;
        
        COMMIT;
        
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE_APPLICATION_ERROR(-20003, 'Błąd podczas aktualizacji pozycji: ' || SQLERRM);
    END aktualizuj_pozycje_portfela;

    -- PROCEDURA: wplac_srodki

    PROCEDURE wplac_srodki(
        p_portfolio_id IN NUMBER,
        p_kwota IN NUMBER,
        p_wynik OUT VARCHAR2
    ) IS
        v_waluta VARCHAR2(3);
    BEGIN
        IF p_kwota <= 0 THEN
            p_wynik := 'BŁĄD: Kwota wpłaty musi być większa od zera';
            RETURN;
        END IF;
        
        UPDATE PORTFELE
        SET saldo_gotowkowe = saldo_gotowkowe + p_kwota
        WHERE portfolio_id = p_portfolio_id
        RETURNING waluta_portfela INTO v_waluta;
        
        IF SQL%ROWCOUNT = 0 THEN
            p_wynik := 'BŁĄD: Nie znaleziono portfela o podanym ID';
            RETURN;
        END IF;
        
        COMMIT;
        
        p_wynik := 'OK: Wpłacono ' || TO_CHAR(p_kwota, '999999999.99') || ' ' || v_waluta;
        
    EXCEPTION
        WHEN OTHERS THEN
            p_wynik := 'BŁĄD: ' || SQLERRM;
            ROLLBACK;
    END wplac_srodki;

END pkg_gielda;
/
