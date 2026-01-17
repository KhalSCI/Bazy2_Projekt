-- ============================================
--     SYMULATOR GIEŁDY - ROZSZERZONY PAKIET
-- ============================================
-- Ten plik zawiera dodatkowe procedury i funkcje
-- rozszerzające pakiet pkg_gielda

-- Specyfikacja rozszerzonego pakietu
CREATE OR REPLACE PACKAGE pkg_gielda_ext AS

    -- Stała: domyślna stawka prowizji (0.39%)
    c_prowizja_domyslna CONSTANT NUMBER := 0.0039;

    -- =========================================
    -- PROCEDURY UŻYTKOWNIKA I PORTFELA
    -- =========================================

    -- Tworzy nowego użytkownika
    PROCEDURE utworz_uzytkownika(
        p_login IN VARCHAR2,
        p_haslo IN VARCHAR2,
        p_email IN VARCHAR2,
        p_imie IN VARCHAR2 DEFAULT NULL,
        p_nazwisko IN VARCHAR2 DEFAULT NULL,
        p_user_id OUT NUMBER,
        p_wynik OUT VARCHAR2
    );

    -- Tworzy nowy portfel dla użytkownika
    PROCEDURE utworz_portfel(
        p_user_id IN NUMBER,
        p_nazwa IN VARCHAR2,
        p_waluta IN VARCHAR2,
        p_saldo_poczatkowe IN NUMBER DEFAULT 0,
        p_portfolio_id OUT NUMBER,
        p_wynik OUT VARCHAR2
    );

    -- Wypłaca środki z portfela
    PROCEDURE wyplac_srodki(
        p_portfolio_id IN NUMBER,
        p_kwota IN NUMBER,
        p_wynik OUT VARCHAR2
    );

    -- =========================================
    -- PROCEDURY ZLECEŃ
    -- =========================================

    -- Tworzy nowe zlecenie (kupna lub sprzedaży)
    PROCEDURE utworz_zlecenie(
        p_portfolio_id IN NUMBER,
        p_instrument_id IN NUMBER,
        p_typ_zlecenia IN VARCHAR2,
        p_strona_zlecenia IN VARCHAR2,
        p_ilosc IN NUMBER,
        p_limit_ceny IN NUMBER DEFAULT NULL,
        p_data_wygasniecia IN DATE DEFAULT NULL,
        p_order_id OUT NUMBER,
        p_wynik OUT VARCHAR2
    );

    -- Anuluje oczekujące zlecenie
    PROCEDURE anuluj_zlecenie(
        p_order_id IN NUMBER,
        p_wynik OUT VARCHAR2
    );

    -- Przetwarza oczekujące zlecenia z limitem ceny
    PROCEDURE przetworz_zlecenia_limit(
        p_portfolio_id IN NUMBER,
        p_data_symulacji IN DATE,
        p_wynik OUT VARCHAR2
    );

    -- =========================================
    -- FUNKCJE POBIERANIA CEN (TIME TRAVEL)
    -- =========================================

    -- Pobiera cenę instrumentu dla określonej daty
    FUNCTION pobierz_cene_dla_daty(
        p_instrument_id IN NUMBER,
        p_data IN DATE
    ) RETURN NUMBER;

    -- Oblicza wartość portfela dla określonej daty (time travel)
    FUNCTION oblicz_wartosc_portfela_dla_daty(
        p_portfolio_id IN NUMBER,
        p_data IN DATE
    ) RETURN NUMBER;

    -- =========================================
    -- FUNKCJE POMOCNICZE
    -- =========================================

    -- Sprawdza czy użytkownik o podanym loginie istnieje
    FUNCTION czy_login_istnieje(
        p_login IN VARCHAR2
    ) RETURN BOOLEAN;

    -- Sprawdza czy email jest już używany
    FUNCTION czy_email_istnieje(
        p_email IN VARCHAR2
    ) RETURN BOOLEAN;

    -- Weryfikuje hasło użytkownika
    FUNCTION weryfikuj_haslo(
        p_login IN VARCHAR2,
        p_haslo IN VARCHAR2
    ) RETURN NUMBER;  -- Zwraca user_id lub NULL

    -- Oblicza prowizję dla transakcji
    FUNCTION oblicz_prowizje(
        p_wartosc IN NUMBER,
        p_stawka IN NUMBER DEFAULT c_prowizja_domyslna
    ) RETURN NUMBER;

END pkg_gielda_ext;
/

-- Ciało rozszerzonego pakietu
CREATE OR REPLACE PACKAGE BODY pkg_gielda_ext AS

    -- =========================================
    -- PROCEDURA: utworz_uzytkownika
    -- =========================================
    PROCEDURE utworz_uzytkownika(
        p_login IN VARCHAR2,
        p_haslo IN VARCHAR2,
        p_email IN VARCHAR2,
        p_imie IN VARCHAR2 DEFAULT NULL,
        p_nazwisko IN VARCHAR2 DEFAULT NULL,
        p_user_id OUT NUMBER,
        p_wynik OUT VARCHAR2
    ) IS
        v_count NUMBER;
    BEGIN
        -- Sprawdź czy login jest unikalny
        SELECT COUNT(*) INTO v_count
        FROM UZYTKOWNICY
        WHERE login = p_login;

        IF v_count > 0 THEN
            p_user_id := NULL;
            p_wynik := 'BŁĄD: Login jest już zajęty';
            RETURN;
        END IF;

        -- Sprawdź czy email jest unikalny
        SELECT COUNT(*) INTO v_count
        FROM UZYTKOWNICY
        WHERE email = p_email;

        IF v_count > 0 THEN
            p_user_id := NULL;
            p_wynik := 'BŁĄD: Email jest już używany';
            RETURN;
        END IF;

        -- Utwórz użytkownika
        INSERT INTO UZYTKOWNICY (login, haslo, email, imie, nazwisko)
        VALUES (p_login, p_haslo, p_email, p_imie, p_nazwisko)
        RETURNING user_id INTO p_user_id;

        COMMIT;

        p_wynik := 'OK: Użytkownik utworzony pomyślnie';

    EXCEPTION
        WHEN OTHERS THEN
            p_user_id := NULL;
            p_wynik := 'BŁĄD: ' || SQLERRM;
            ROLLBACK;
    END utworz_uzytkownika;

    -- =========================================
    -- PROCEDURA: utworz_portfel
    -- =========================================
    PROCEDURE utworz_portfel(
        p_user_id IN NUMBER,
        p_nazwa IN VARCHAR2,
        p_waluta IN VARCHAR2,
        p_saldo_poczatkowe IN NUMBER DEFAULT 0,
        p_portfolio_id OUT NUMBER,
        p_wynik OUT VARCHAR2
    ) IS
        v_user_exists NUMBER;
    BEGIN
        -- Sprawdź czy użytkownik istnieje
        SELECT COUNT(*) INTO v_user_exists
        FROM UZYTKOWNICY
        WHERE user_id = p_user_id;

        IF v_user_exists = 0 THEN
            p_portfolio_id := NULL;
            p_wynik := 'BŁĄD: Użytkownik nie istnieje';
            RETURN;
        END IF;

        -- Sprawdź czy saldo jest nieujemne
        IF p_saldo_poczatkowe < 0 THEN
            p_portfolio_id := NULL;
            p_wynik := 'BŁĄD: Saldo początkowe nie może być ujemne';
            RETURN;
        END IF;

        -- Utwórz portfel
        INSERT INTO PORTFELE (user_id, nazwa_portfela, waluta_portfela, saldo_gotowkowe)
        VALUES (p_user_id, p_nazwa, UPPER(p_waluta), p_saldo_poczatkowe)
        RETURNING portfolio_id INTO p_portfolio_id;

        COMMIT;

        p_wynik := 'OK: Portfel utworzony pomyślnie';

    EXCEPTION
        WHEN OTHERS THEN
            p_portfolio_id := NULL;
            p_wynik := 'BŁĄD: ' || SQLERRM;
            ROLLBACK;
    END utworz_portfel;

    -- =========================================
    -- PROCEDURA: wyplac_srodki
    -- =========================================
    PROCEDURE wyplac_srodki(
        p_portfolio_id IN NUMBER,
        p_kwota IN NUMBER,
        p_wynik OUT VARCHAR2
    ) IS
        v_saldo NUMBER;
        v_waluta VARCHAR2(3);
    BEGIN
        IF p_kwota <= 0 THEN
            p_wynik := 'BŁĄD: Kwota wypłaty musi być większa od zera';
            RETURN;
        END IF;

        -- Pobierz aktualne saldo
        SELECT saldo_gotowkowe, waluta_portfela
        INTO v_saldo, v_waluta
        FROM PORTFELE
        WHERE portfolio_id = p_portfolio_id;

        IF v_saldo < p_kwota THEN
            p_wynik := 'BŁĄD: Niewystarczające środki. Dostępne: ' ||
                       TO_CHAR(v_saldo, '999999999.99') || ' ' || v_waluta;
            RETURN;
        END IF;

        -- Wykonaj wypłatę
        UPDATE PORTFELE
        SET saldo_gotowkowe = saldo_gotowkowe - p_kwota
        WHERE portfolio_id = p_portfolio_id;

        COMMIT;

        p_wynik := 'OK: Wypłacono ' || TO_CHAR(p_kwota, '999999999.99') || ' ' || v_waluta;

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            p_wynik := 'BŁĄD: Nie znaleziono portfela';
        WHEN OTHERS THEN
            p_wynik := 'BŁĄD: ' || SQLERRM;
            ROLLBACK;
    END wyplac_srodki;

    -- =========================================
    -- PROCEDURA: utworz_zlecenie
    -- =========================================
    PROCEDURE utworz_zlecenie(
        p_portfolio_id IN NUMBER,
        p_instrument_id IN NUMBER,
        p_typ_zlecenia IN VARCHAR2,
        p_strona_zlecenia IN VARCHAR2,
        p_ilosc IN NUMBER,
        p_limit_ceny IN NUMBER DEFAULT NULL,
        p_data_wygasniecia IN DATE DEFAULT NULL,
        p_order_id OUT NUMBER,
        p_wynik OUT VARCHAR2
    ) IS
        v_portfolio_exists NUMBER;
        v_instrument_exists NUMBER;
    BEGIN
        -- Walidacja typu zlecenia
        IF p_typ_zlecenia NOT IN ('MARKET', 'LIMIT', 'STOP') THEN
            p_order_id := NULL;
            p_wynik := 'BŁĄD: Nieprawidłowy typ zlecenia';
            RETURN;
        END IF;

        -- Walidacja strony zlecenia
        IF p_strona_zlecenia NOT IN ('KUPNO', 'SPRZEDAZ') THEN
            p_order_id := NULL;
            p_wynik := 'BŁĄD: Nieprawidłowa strona zlecenia';
            RETURN;
        END IF;

        -- Walidacja ilości
        IF p_ilosc <= 0 THEN
            p_order_id := NULL;
            p_wynik := 'BŁĄD: Ilość musi być większa od zera';
            RETURN;
        END IF;

        -- Sprawdź czy portfel istnieje
        SELECT COUNT(*) INTO v_portfolio_exists
        FROM PORTFELE
        WHERE portfolio_id = p_portfolio_id;

        IF v_portfolio_exists = 0 THEN
            p_order_id := NULL;
            p_wynik := 'BŁĄD: Portfel nie istnieje';
            RETURN;
        END IF;

        -- Sprawdź czy instrument istnieje
        SELECT COUNT(*) INTO v_instrument_exists
        FROM INSTRUMENTY
        WHERE instrument_id = p_instrument_id
          AND status = 'AKTYWNY';

        IF v_instrument_exists = 0 THEN
            p_order_id := NULL;
            p_wynik := 'BŁĄD: Instrument nie istnieje lub jest nieaktywny';
            RETURN;
        END IF;

        -- Dla zleceń LIMIT wymagana jest cena limitu
        IF p_typ_zlecenia = 'LIMIT' AND p_limit_ceny IS NULL THEN
            p_order_id := NULL;
            p_wynik := 'BŁĄD: Zlecenie LIMIT wymaga podania ceny limitu';
            RETURN;
        END IF;

        -- Utwórz zlecenie
        INSERT INTO ZLECENIA (
            portfolio_id, instrument_id, typ_zlecenia, strona_zlecenia,
            ilosc, limit_ceny, data_wygasniecia
        ) VALUES (
            p_portfolio_id, p_instrument_id, p_typ_zlecenia, p_strona_zlecenia,
            p_ilosc, p_limit_ceny, p_data_wygasniecia
        )
        RETURNING order_id INTO p_order_id;

        COMMIT;

        p_wynik := 'OK: Zlecenie utworzone (ID: ' || p_order_id || ')';

    EXCEPTION
        WHEN OTHERS THEN
            p_order_id := NULL;
            p_wynik := 'BŁĄD: ' || SQLERRM;
            ROLLBACK;
    END utworz_zlecenie;

    -- =========================================
    -- PROCEDURA: anuluj_zlecenie
    -- =========================================
    PROCEDURE anuluj_zlecenie(
        p_order_id IN NUMBER,
        p_wynik OUT VARCHAR2
    ) IS
        v_status VARCHAR2(20);
    BEGIN
        -- Sprawdź status zlecenia
        SELECT status INTO v_status
        FROM ZLECENIA
        WHERE order_id = p_order_id;

        IF v_status != 'OCZEKUJACE' THEN
            p_wynik := 'BŁĄD: Można anulować tylko oczekujące zlecenia. Aktualny status: ' || v_status;
            RETURN;
        END IF;

        -- Anuluj zlecenie
        UPDATE ZLECENIA
        SET status = 'ANULOWANE',
            data_wykonania = SYSTIMESTAMP
        WHERE order_id = p_order_id;

        COMMIT;

        p_wynik := 'OK: Zlecenie anulowane';

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            p_wynik := 'BŁĄD: Nie znaleziono zlecenia';
        WHEN OTHERS THEN
            p_wynik := 'BŁĄD: ' || SQLERRM;
            ROLLBACK;
    END anuluj_zlecenie;

    -- =========================================
    -- PROCEDURA: przetworz_zlecenia_limit
    -- =========================================
    PROCEDURE przetworz_zlecenia_limit(
        p_portfolio_id IN NUMBER,
        p_data_symulacji IN DATE,
        p_wynik OUT VARCHAR2
    ) IS
        v_cena NUMBER;
        v_wykonane NUMBER := 0;
        v_wynik_zlecenia VARCHAR2(500);
    BEGIN
        -- Przetwórz każde oczekujące zlecenie LIMIT
        FOR zlecenie IN (
            SELECT order_id, instrument_id, strona_zlecenia, limit_ceny
            FROM ZLECENIA
            WHERE portfolio_id = p_portfolio_id
              AND status = 'OCZEKUJACE'
              AND typ_zlecenia = 'LIMIT'
              AND (data_wygasniecia IS NULL OR data_wygasniecia >= p_data_symulacji)
        ) LOOP
            -- Pobierz cenę dla daty symulacji
            v_cena := pobierz_cene_dla_daty(zlecenie.instrument_id, p_data_symulacji);

            IF v_cena IS NOT NULL THEN
                -- Sprawdź warunki wykonania
                IF zlecenie.strona_zlecenia = 'KUPNO' AND v_cena <= zlecenie.limit_ceny THEN
                    -- Wykonaj zlecenie kupna
                    pkg_gielda.wykonaj_zlecenie_kupna(zlecenie.order_id, v_cena, v_wynik_zlecenia);
                    IF v_wynik_zlecenia LIKE 'OK%' THEN
                        v_wykonane := v_wykonane + 1;
                    END IF;
                ELSIF zlecenie.strona_zlecenia = 'SPRZEDAZ' AND v_cena >= zlecenie.limit_ceny THEN
                    -- Wykonaj zlecenie sprzedaży
                    pkg_gielda.wykonaj_zlecenie_sprzedazy(zlecenie.order_id, v_cena, v_wynik_zlecenia);
                    IF v_wynik_zlecenia LIKE 'OK%' THEN
                        v_wykonane := v_wykonane + 1;
                    END IF;
                END IF;
            END IF;
        END LOOP;

        p_wynik := 'OK: Przetworzono zlecenia. Wykonano: ' || v_wykonane;

    EXCEPTION
        WHEN OTHERS THEN
            p_wynik := 'BŁĄD: ' || SQLERRM;
    END przetworz_zlecenia_limit;

    -- =========================================
    -- FUNKCJA: pobierz_cene_dla_daty
    -- =========================================
    FUNCTION pobierz_cene_dla_daty(
        p_instrument_id IN NUMBER,
        p_data IN DATE
    ) RETURN NUMBER IS
        v_cena NUMBER;
    BEGIN
        SELECT cena_zamkniecia INTO v_cena
        FROM DANE_DZIENNE
        WHERE instrument_id = p_instrument_id
          AND data_notowan <= p_data
        ORDER BY data_notowan DESC
        FETCH FIRST 1 ROW ONLY;

        RETURN v_cena;

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN NULL;
        WHEN OTHERS THEN
            RETURN NULL;
    END pobierz_cene_dla_daty;

    -- =========================================
    -- FUNKCJA: oblicz_wartosc_portfela_dla_daty
    -- =========================================
    FUNCTION oblicz_wartosc_portfela_dla_daty(
        p_portfolio_id IN NUMBER,
        p_data IN DATE
    ) RETURN NUMBER IS
        v_wartosc_pozycji NUMBER := 0;
        v_saldo_gotowkowe NUMBER := 0;
        v_cena NUMBER;
    BEGIN
        -- Pobierz saldo gotówkowe
        SELECT NVL(saldo_gotowkowe, 0)
        INTO v_saldo_gotowkowe
        FROM PORTFELE
        WHERE portfolio_id = p_portfolio_id;

        -- Oblicz wartość pozycji dla podanej daty
        FOR pozycja IN (
            SELECT instrument_id, ilosc_akcji
            FROM POZYCJE
            WHERE portfolio_id = p_portfolio_id
              AND ilosc_akcji > 0
        ) LOOP
            v_cena := pobierz_cene_dla_daty(pozycja.instrument_id, p_data);
            IF v_cena IS NOT NULL THEN
                v_wartosc_pozycji := v_wartosc_pozycji + (pozycja.ilosc_akcji * v_cena);
            END IF;
        END LOOP;

        RETURN ROUND(v_saldo_gotowkowe + v_wartosc_pozycji, 2);

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 0;
        WHEN OTHERS THEN
            RETURN 0;
    END oblicz_wartosc_portfela_dla_daty;

    -- =========================================
    -- FUNKCJA: czy_login_istnieje
    -- =========================================
    FUNCTION czy_login_istnieje(
        p_login IN VARCHAR2
    ) RETURN BOOLEAN IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count
        FROM UZYTKOWNICY
        WHERE login = p_login;

        RETURN v_count > 0;
    END czy_login_istnieje;

    -- =========================================
    -- FUNKCJA: czy_email_istnieje
    -- =========================================
    FUNCTION czy_email_istnieje(
        p_email IN VARCHAR2
    ) RETURN BOOLEAN IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_count
        FROM UZYTKOWNICY
        WHERE email = p_email;

        RETURN v_count > 0;
    END czy_email_istnieje;

    -- =========================================
    -- FUNKCJA: weryfikuj_haslo
    -- =========================================
    FUNCTION weryfikuj_haslo(
        p_login IN VARCHAR2,
        p_haslo IN VARCHAR2
    ) RETURN NUMBER IS
        v_user_id NUMBER;
        v_haslo_db VARCHAR2(255);
    BEGIN
        SELECT user_id, haslo
        INTO v_user_id, v_haslo_db
        FROM UZYTKOWNICY
        WHERE login = p_login;

        -- Proste porównanie haseł (w produkcji użyć hashowania)
        IF v_haslo_db = p_haslo THEN
            RETURN v_user_id;
        ELSE
            RETURN NULL;
        END IF;

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN NULL;
        WHEN OTHERS THEN
            RETURN NULL;
    END weryfikuj_haslo;

    -- =========================================
    -- FUNKCJA: oblicz_prowizje
    -- =========================================
    FUNCTION oblicz_prowizje(
        p_wartosc IN NUMBER,
        p_stawka IN NUMBER DEFAULT c_prowizja_domyslna
    ) RETURN NUMBER IS
    BEGIN
        RETURN ROUND(p_wartosc * p_stawka, 2);
    END oblicz_prowizje;

END pkg_gielda_ext;
/
