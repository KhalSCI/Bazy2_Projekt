# Dokumentacja Pakietu `pkg_gielda_ext`

## Spis treści

1. [Opis ogólny](#opis-ogólny)
2. [Zależności](#zależności)
3. [Stałe](#stałe)
4. [Procedury](#procedury)
   - [utworz_uzytkownika](#utworz_uzytkownika)
   - [utworz_portfel](#utworz_portfel)
   - [wyplac_srodki](#wyplac_srodki)
   - [utworz_zlecenie](#utworz_zlecenie)
   - [anuluj_zlecenie](#anuluj_zlecenie)
   - [przetworz_zlecenia_limit](#przetworz_zlecenia_limit)
5. [Funkcje](#funkcje)
   - [pobierz_cene_dla_daty](#pobierz_cene_dla_daty)
   - [oblicz_wartosc_portfela_dla_daty](#oblicz_wartosc_portfela_dla_daty)
   - [czy_login_istnieje](#czy_login_istnieje)
   - [czy_email_istnieje](#czy_email_istnieje)
   - [weryfikuj_haslo](#weryfikuj_haslo)
   - [oblicz_prowizje](#oblicz_prowizje)
6. [Tabele referencyjne](#tabele-referencyjne)
7. [Reguły biznesowe](#reguły-biznesowe)

---

## Opis ogólny

Pakiet `pkg_gielda_ext` (Extended) jest **rozszerzeniem pakietu podstawowego** `pkg_gielda`. Zawiera dodatkowe procedury i funkcje obsługujące:

- **Zarządzanie użytkownikami** - rejestracja, uwierzytelnianie
- **Zarządzanie portfelami** - tworzenie, wypłaty
- **Zarządzanie zleceniami** - tworzenie, anulowanie, automatyczne przetwarzanie zleceń limitowanych
- **Funkcję Time Travel** - wycena portfela i pobieranie cen dla dowolnej daty historycznej

### Architektura

```
Warstwa prezentacji (Streamlit)
        ↓
Warstwa serwisowa (Python)
        ↓
   pkg_gielda_ext  ← Jesteś tutaj
        ↓
     pkg_gielda    (pakiet podstawowy)
        ↓
   Baza danych Oracle
```

---

## Zależności

Pakiet `pkg_gielda_ext` wykorzystuje procedury z pakietu podstawowego `pkg_gielda`:

| Procedura wywoływana | Kontekst użycia |
|---------------------|-----------------|
| `pkg_gielda.wykonaj_zlecenie_kupna` | Realizacja zleceń limitowanych typu KUPNO |
| `pkg_gielda.wykonaj_zlecenie_sprzedazy` | Realizacja zleceń limitowanych typu SPRZEDAZ |

---

## Stałe

### `c_prowizja_domyslna`

| Atrybut | Wartość |
|---------|---------|
| **Typ** | `NUMBER` |
| **Wartość** | `0.0039` (0,39%) |
| **Opis** | Domyślna stawka prowizji używana w funkcji `oblicz_prowizje` |

---

## Procedury

### `utworz_uzytkownika`

Tworzy nowe konto użytkownika w systemie.

#### Sygnatura

```sql
PROCEDURE utworz_uzytkownika(
    p_login     IN VARCHAR2,
    p_haslo     IN VARCHAR2,
    p_email     IN VARCHAR2,
    p_imie      IN VARCHAR2 DEFAULT NULL,
    p_nazwisko  IN VARCHAR2 DEFAULT NULL,
    p_user_id   OUT NUMBER,
    p_wynik     OUT VARCHAR2
);
```

#### Parametry

| Parametr | Typ | Kierunek | Obowiązkowy | Opis |
|----------|-----|----------|-------------|------|
| `p_login` | `VARCHAR2` | IN | Tak | Login użytkownika (musi być unikalny) |
| `p_haslo` | `VARCHAR2` | IN | Tak | Hasło użytkownika |
| `p_email` | `VARCHAR2` | IN | Tak | Adres email (musi być unikalny) |
| `p_imie` | `VARCHAR2` | IN | Nie | Imię użytkownika |
| `p_nazwisko` | `VARCHAR2` | IN | Nie | Nazwisko użytkownika |
| `p_user_id` | `NUMBER` | OUT | - | Zwrócony identyfikator nowego użytkownika |
| `p_wynik` | `VARCHAR2` | OUT | - | Komunikat wynikowy |

#### Logika biznesowa

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Sprawdź czy login jest unikalny                          │
│    Warunek: czy_login_istnieje(p_login) = FALSE             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Sprawdź czy email jest unikalny                          │
│    Warunek: czy_email_istnieje(p_email) = FALSE             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Wstaw rekord do tabeli UZYTKOWNICY                       │
│    - user_id z sekwencji seq_uzytkownicy                    │
│    - data_rejestracji = SYSDATE                             │
│    - waluta_bazowa = 'USD' (domyślnie)                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. COMMIT i zwróć user_id                                   │
└─────────────────────────────────────────────────────────────┘
```

#### Przykład użycia

```sql
DECLARE
    v_user_id NUMBER;
    v_wynik   VARCHAR2(4000);
BEGIN
    pkg_gielda_ext.utworz_uzytkownika(
        p_login    => 'jan_kowalski',
        p_haslo    => 'SecurePass123!',
        p_email    => 'jan@example.com',
        p_imie     => 'Jan',
        p_nazwisko => 'Kowalski',
        p_user_id  => v_user_id,
        p_wynik    => v_wynik
    );

    IF v_wynik LIKE 'OK:%' THEN
        DBMS_OUTPUT.PUT_LINE('Utworzono użytkownika ID: ' || v_user_id);
    ELSE
        DBMS_OUTPUT.PUT_LINE(v_wynik);
    END IF;
END;
```

#### Obsługa błędów

| Komunikat | Przyczyna |
|-----------|-----------|
| `BŁĄD: Login jest już zajęty` | Istnieje użytkownik o takim loginie |
| `BŁĄD: Email jest już używany` | Istnieje użytkownik o takim emailu |
| `BŁĄD: [SQLERRM]` | Inny błąd bazy danych |

---

### `utworz_portfel`

Tworzy nowy portfel inwestycyjny dla użytkownika.

#### Sygnatura

```sql
PROCEDURE utworz_portfel(
    p_user_id          IN NUMBER,
    p_nazwa            IN VARCHAR2,
    p_waluta           IN VARCHAR2,
    p_saldo_poczatkowe IN NUMBER DEFAULT 0,
    p_portfolio_id     OUT NUMBER,
    p_wynik            OUT VARCHAR2
);
```

#### Parametry

| Parametr | Typ | Kierunek | Obowiązkowy | Opis |
|----------|-----|----------|-------------|------|
| `p_user_id` | `NUMBER` | IN | Tak | ID użytkownika (właściciela portfela) |
| `p_nazwa` | `VARCHAR2` | IN | Tak | Nazwa portfela |
| `p_waluta` | `VARCHAR2` | IN | Tak | Kod waluty (np. USD, PLN, EUR) |
| `p_saldo_poczatkowe` | `NUMBER` | IN | Nie | Początkowe saldo gotówkowe (domyślnie: 0) |
| `p_portfolio_id` | `NUMBER` | OUT | - | Zwrócony identyfikator portfela |
| `p_wynik` | `VARCHAR2` | OUT | - | Komunikat wynikowy |

#### Logika biznesowa

1. Sprawdzenie czy użytkownik istnieje w tabeli `UZYTKOWNICY`
2. Walidacja: saldo początkowe >= 0
3. Konwersja waluty do wielkich liter (UPPER)
4. Wstawienie rekordu do tabeli `PORTFELE`
5. COMMIT i zwrócenie `portfolio_id`

#### Przykład użycia

```sql
DECLARE
    v_portfolio_id NUMBER;
    v_wynik        VARCHAR2(4000);
BEGIN
    pkg_gielda_ext.utworz_portfel(
        p_user_id          => 1,
        p_nazwa            => 'Mój pierwszy portfel',
        p_waluta           => 'usd',  -- zostanie przekonwertowane na 'USD'
        p_saldo_poczatkowe => 10000,
        p_portfolio_id     => v_portfolio_id,
        p_wynik            => v_wynik
    );
    DBMS_OUTPUT.PUT_LINE(v_wynik);
    -- Wynik: OK: Utworzono portfel o ID 1
END;
```

#### Obsługa błędów

| Komunikat | Przyczyna |
|-----------|-----------|
| `BŁĄD: Użytkownik nie istnieje` | Nie znaleziono użytkownika o podanym ID |
| `BŁĄD: Saldo początkowe nie może być ujemne` | Podano ujemną wartość salda |
| `BŁĄD: [SQLERRM]` | Inny błąd bazy danych |

---

### `wyplac_srodki`

Wypłaca środki pieniężne z portfela inwestycyjnego.

#### Sygnatura

```sql
PROCEDURE wyplac_srodki(
    p_portfolio_id IN NUMBER,
    p_kwota        IN NUMBER,
    p_wynik        OUT VARCHAR2
);
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_portfolio_id` | `NUMBER` | IN | Identyfikator portfela |
| `p_kwota` | `NUMBER` | IN | Kwota do wypłaty |
| `p_wynik` | `VARCHAR2` | OUT | Komunikat wynikowy |

#### Logika biznesowa

1. Walidacja: kwota > 0
2. Pobranie aktualnego salda i waluty portfela
3. Sprawdzenie czy wystarczające środki (`saldo_gotowkowe >= p_kwota`)
4. Zmniejszenie salda o kwotę wypłaty
5. COMMIT

#### Przykład użycia

```sql
DECLARE
    v_wynik VARCHAR2(4000);
BEGIN
    pkg_gielda_ext.wyplac_srodki(
        p_portfolio_id => 1,
        p_kwota        => 5000,
        p_wynik        => v_wynik
    );
    DBMS_OUTPUT.PUT_LINE(v_wynik);
    -- Wynik: OK: Wypłacono 5000 USD
END;
```

#### Obsługa błędów

| Komunikat | Przyczyna |
|-----------|-----------|
| `BŁĄD: Kwota wypłaty musi być większa od zera` | Podano kwotę <= 0 |
| `BŁĄD: Niewystarczające środki. Dostępne: X [waluta]` | Saldo niższe niż kwota wypłaty |
| `BŁĄD: Nie znaleziono portfela` | Portfel o podanym ID nie istnieje |
| `BŁĄD: [SQLERRM]` | Inny błąd bazy danych |

---

### `utworz_zlecenie`

Tworzy nowe zlecenie giełdowe (kupna lub sprzedaży).

#### Sygnatura

```sql
PROCEDURE utworz_zlecenie(
    p_portfolio_id     IN NUMBER,
    p_instrument_id    IN NUMBER,
    p_typ_zlecenia     IN VARCHAR2,
    p_strona_zlecenia  IN VARCHAR2,
    p_ilosc            IN NUMBER,
    p_limit_ceny       IN NUMBER DEFAULT NULL,
    p_data_wygasniecia IN DATE DEFAULT NULL,
    p_data_utworzenia  IN TIMESTAMP DEFAULT NULL,
    p_order_id         OUT NUMBER,
    p_wynik            OUT VARCHAR2
);
```

#### Parametry

| Parametr | Typ | Kierunek | Obowiązkowy | Opis |
|----------|-----|----------|-------------|------|
| `p_portfolio_id` | `NUMBER` | IN | Tak | ID portfela składającego zlecenie |
| `p_instrument_id` | `NUMBER` | IN | Tak | ID instrumentu finansowego |
| `p_typ_zlecenia` | `VARCHAR2` | IN | Tak | Typ: `MARKET`, `LIMIT`, `STOP` |
| `p_strona_zlecenia` | `VARCHAR2` | IN | Tak | Strona: `KUPNO` lub `SPRZEDAZ` |
| `p_ilosc` | `NUMBER` | IN | Tak | Ilość jednostek do kupna/sprzedaży |
| `p_limit_ceny` | `NUMBER` | IN | Warunkowy | Cena limitu (wymagana dla LIMIT) |
| `p_data_wygasniecia` | `DATE` | IN | Nie | Data wygaśnięcia zlecenia |
| `p_data_utworzenia` | `TIMESTAMP` | IN | Nie | Data utworzenia (domyślnie: SYSTIMESTAMP) |
| `p_order_id` | `NUMBER` | OUT | - | Zwrócony identyfikator zlecenia |
| `p_wynik` | `VARCHAR2` | OUT | - | Komunikat wynikowy |

#### Typy zleceń

| Typ | Opis | Wymagane parametry |
|-----|------|-------------------|
| `MARKET` | Zlecenie rynkowe - wykonanie natychmiast po aktualnej cenie | - |
| `LIMIT` | Zlecenie z limitem ceny - wykonanie gdy cena osiągnie limit | `p_limit_ceny` |
| `STOP` | Zlecenie stop - aktywacja przy określonej cenie | `p_stop_cena` (w tabeli) |

#### Logika biznesowa

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Walidacja typu zlecenia                                  │
│    p_typ_zlecenia IN ('MARKET', 'LIMIT', 'STOP')            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Walidacja strony zlecenia                                │
│    p_strona_zlecenia IN ('KUPNO', 'SPRZEDAZ')               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Walidacja ilości                                         │
│    p_ilosc > 0                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Sprawdzenie istnienia portfela                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Sprawdzenie instrumentu                                  │
│    - Czy istnieje?                                          │
│    - Czy ma status 'AKTYWNY'?                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Dla zleceń LIMIT: wymóg p_limit_ceny IS NOT NULL         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Wstawienie zlecenia do tabeli ZLECENIA                   │
│    status = 'OCZEKUJACE'                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. COMMIT i zwróć order_id                                  │
└─────────────────────────────────────────────────────────────┘
```

#### Przykład użycia

```sql
-- Zlecenie rynkowe kupna
DECLARE
    v_order_id NUMBER;
    v_wynik    VARCHAR2(4000);
BEGIN
    pkg_gielda_ext.utworz_zlecenie(
        p_portfolio_id    => 1,
        p_instrument_id   => 5,  -- np. AAPL
        p_typ_zlecenia    => 'MARKET',
        p_strona_zlecenia => 'KUPNO',
        p_ilosc           => 10,
        p_order_id        => v_order_id,
        p_wynik           => v_wynik
    );
    DBMS_OUTPUT.PUT_LINE(v_wynik);
END;

-- Zlecenie limitowane sprzedaży
DECLARE
    v_order_id NUMBER;
    v_wynik    VARCHAR2(4000);
BEGIN
    pkg_gielda_ext.utworz_zlecenie(
        p_portfolio_id     => 1,
        p_instrument_id    => 5,
        p_typ_zlecenia     => 'LIMIT',
        p_strona_zlecenia  => 'SPRZEDAZ',
        p_ilosc            => 5,
        p_limit_ceny       => 200.00,  -- sprzedaj gdy cena >= 200
        p_data_wygasniecia => SYSDATE + 30,  -- ważne 30 dni
        p_order_id         => v_order_id,
        p_wynik            => v_wynik
    );
    DBMS_OUTPUT.PUT_LINE(v_wynik);
END;
```

#### Obsługa błędów

| Komunikat | Przyczyna |
|-----------|-----------|
| `BŁĄD: Nieprawidłowy typ zlecenia` | Typ nie jest MARKET, LIMIT ani STOP |
| `BŁĄD: Nieprawidłowa strona zlecenia` | Strona nie jest KUPNO ani SPRZEDAZ |
| `BŁĄD: Ilość musi być większa od zera` | Podano ilość <= 0 |
| `BŁĄD: Portfel nie istnieje` | Nie znaleziono portfela o podanym ID |
| `BŁĄD: Instrument nie istnieje lub jest nieaktywny` | Instrument nie istnieje lub ma status inny niż AKTYWNY |
| `BŁĄD: Zlecenie LIMIT wymaga podania ceny limitu` | Brak p_limit_ceny dla zlecenia LIMIT |
| `BŁĄD: [SQLERRM]` | Inny błąd bazy danych |

---

### `anuluj_zlecenie`

Anuluje oczekujące zlecenie giełdowe.

#### Sygnatura

```sql
PROCEDURE anuluj_zlecenie(
    p_order_id IN NUMBER,
    p_wynik    OUT VARCHAR2
);
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_order_id` | `NUMBER` | IN | Identyfikator zlecenia do anulowania |
| `p_wynik` | `VARCHAR2` | OUT | Komunikat wynikowy |

#### Logika biznesowa

1. Pobranie aktualnego statusu zlecenia
2. Sprawdzenie czy status = `OCZEKUJACE` (tylko takie można anulować)
3. Zmiana statusu na `ANULOWANE`
4. Ustawienie `data_wykonania = SYSTIMESTAMP`
5. COMMIT

#### Przykład użycia

```sql
DECLARE
    v_wynik VARCHAR2(4000);
BEGIN
    pkg_gielda_ext.anuluj_zlecenie(
        p_order_id => 123,
        p_wynik    => v_wynik
    );
    DBMS_OUTPUT.PUT_LINE(v_wynik);
    -- Wynik: OK: Zlecenie zostało anulowane
END;
```

#### Obsługa błędów

| Komunikat | Przyczyna |
|-----------|-----------|
| `BŁĄD: Można anulować tylko oczekujące zlecenia. Aktualny status: X` | Zlecenie jest już WYKONANE, ANULOWANE lub CZESCIOWE |
| `BŁĄD: Nie znaleziono zlecenia` | Zlecenie o podanym ID nie istnieje |
| `BŁĄD: [SQLERRM]` | Inny błąd bazy danych |

---

### `przetworz_zlecenia_limit`

Automatycznie przetwarza oczekujące zlecenia limitowane dla portfela na podstawie cen historycznych.

#### Sygnatura

```sql
PROCEDURE przetworz_zlecenia_limit(
    p_portfolio_id   IN NUMBER,
    p_data_symulacji IN DATE,
    p_wynik          OUT VARCHAR2
);
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_portfolio_id` | `NUMBER` | IN | Identyfikator portfela |
| `p_data_symulacji` | `DATE` | IN | Data dla której sprawdzane są warunki cenowe |
| `p_wynik` | `VARCHAR2` | OUT | Komunikat z liczbą wykonanych zleceń |

#### Logika biznesowa

```
┌─────────────────────────────────────────────────────────────┐
│ DLA KAŻDEGO zlecenia LIMIT w statusie OCZEKUJACE            │
│ gdzie portfolio_id = p_portfolio_id                         │
│ i (data_wygasniecia IS NULL lub data_wygasniecia >= data)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Pobierz cenę historyczną instrumentu dla daty symulacji     │
│ v_cena := pobierz_cene_dla_daty(instrument_id, data)        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ WARUNEK WYKONANIA:                                          │
│ - KUPNO: cena <= limit_ceny (kup gdy cena spadnie do limitu)│
│ - SPRZEDAZ: cena >= limit_ceny (sprzedaj gdy cena wzrośnie) │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Jeśli warunek spełniony:                                    │
│ - KUPNO: pkg_gielda.wykonaj_zlecenie_kupna(...)             │
│ - SPRZEDAZ: pkg_gielda.wykonaj_zlecenie_sprzedazy(...)      │
│ Inkrementuj licznik wykonanych                              │
└─────────────────────────────────────────────────────────────┘
```

#### Przykład użycia

```sql
DECLARE
    v_wynik VARCHAR2(4000);
BEGIN
    -- Przetwórz zlecenia limitowane na podstawie cen z 15 stycznia 2025
    pkg_gielda_ext.przetworz_zlecenia_limit(
        p_portfolio_id   => 1,
        p_data_symulacji => TO_DATE('2025-01-15', 'YYYY-MM-DD'),
        p_wynik          => v_wynik
    );
    DBMS_OUTPUT.PUT_LINE(v_wynik);
    -- Wynik: OK: Wykonano 3 zlecenia limitowane
END;
```

#### Zastosowanie

Procedura służy do **symulacji "time travel"** - użytkownik może sprawdzić jak zachowałyby się jego zlecenia limitowane w przeszłości, gdyby ceny osiągnęły określone poziomy.

---

## Funkcje

### `pobierz_cene_dla_daty`

Pobiera cenę zamknięcia instrumentu dla określonej daty historycznej.

#### Sygnatura

```sql
FUNCTION pobierz_cene_dla_daty(
    p_instrument_id IN NUMBER,
    p_data          IN DATE
) RETURN NUMBER;
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_instrument_id` | `NUMBER` | IN | Identyfikator instrumentu |
| `p_data` | `DATE` | IN | Data dla której szukamy ceny |

#### Wartość zwracana

| Typ | Opis |
|-----|------|
| `NUMBER` | Cena zamknięcia lub NULL jeśli brak danych |

#### Logika biznesowa

1. Wyszukuje w tabeli `DANE_DZIENNE` rekord dla podanego instrumentu
2. Wybiera cenę zamknięcia (`cena_zamkniecia`) z najnowszej daty **nie późniejszej** niż `p_data`
3. Jeśli brak danych dla tej daty, zwraca cenę z najbliższej wcześniejszej sesji

**Przykład:** Dla daty 2025-01-15 (środa) funkcja zwróci cenę z 2025-01-15.
Dla daty 2025-01-18 (sobota - brak sesji) funkcja zwróci cenę z 2025-01-17 (piątek).

#### Przykład użycia

```sql
DECLARE
    v_cena NUMBER;
BEGIN
    v_cena := pkg_gielda_ext.pobierz_cene_dla_daty(
        p_instrument_id => 1,  -- np. AAPL
        p_data          => TO_DATE('2025-01-10', 'YYYY-MM-DD')
    );

    IF v_cena IS NOT NULL THEN
        DBMS_OUTPUT.PUT_LINE('Cena AAPL na 10.01.2025: ' || v_cena);
    ELSE
        DBMS_OUTPUT.PUT_LINE('Brak danych cenowych');
    END IF;
END;
```

---

### `oblicz_wartosc_portfela_dla_daty`

Oblicza historyczną wartość portfela dla określonej daty.

#### Sygnatura

```sql
FUNCTION oblicz_wartosc_portfela_dla_daty(
    p_portfolio_id IN NUMBER,
    p_data         IN DATE
) RETURN NUMBER;
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_portfolio_id` | `NUMBER` | IN | Identyfikator portfela |
| `p_data` | `DATE` | IN | Data dla której liczymy wartość |

#### Wartość zwracana

| Typ | Opis |
|-----|------|
| `NUMBER` | Wartość portfela zaokrąglona do 2 miejsc po przecinku |

#### Logika biznesowa

```
wartosc_portfela = saldo_gotowkowe + Σ(ilosc_akcji × cena_historyczna)
```

Gdzie `cena_historyczna` jest pobierana funkcją `pobierz_cene_dla_daty` dla każdej pozycji.

#### Przykład użycia

```sql
DECLARE
    v_wartosc NUMBER;
BEGIN
    v_wartosc := pkg_gielda_ext.oblicz_wartosc_portfela_dla_daty(
        p_portfolio_id => 1,
        p_data         => TO_DATE('2025-01-01', 'YYYY-MM-DD')
    );
    DBMS_OUTPUT.PUT_LINE('Wartość portfela na 01.01.2025: ' || v_wartosc);
END;
```

#### Zastosowanie

Funkcja umożliwia **analizę historyczną** - użytkownik może sprawdzić jak wyglądała wartość jego portfela w dowolnym momencie w przeszłości.

---

### `czy_login_istnieje`

Sprawdza czy podany login jest już zajęty w systemie.

#### Sygnatura

```sql
FUNCTION czy_login_istnieje(
    p_login IN VARCHAR2
) RETURN BOOLEAN;
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_login` | `VARCHAR2` | IN | Login do sprawdzenia |

#### Wartość zwracana

| Typ | Wartość | Opis |
|-----|---------|------|
| `BOOLEAN` | `TRUE` | Login jest zajęty |
| `BOOLEAN` | `FALSE` | Login jest dostępny |

#### Przykład użycia

```sql
DECLARE
    v_zajety BOOLEAN;
BEGIN
    v_zajety := pkg_gielda_ext.czy_login_istnieje('jan_kowalski');

    IF v_zajety THEN
        DBMS_OUTPUT.PUT_LINE('Login jest już zajęty');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Login jest dostępny');
    END IF;
END;
```

---

### `czy_email_istnieje`

Sprawdza czy podany email jest już zarejestrowany w systemie.

#### Sygnatura

```sql
FUNCTION czy_email_istnieje(
    p_email IN VARCHAR2
) RETURN BOOLEAN;
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_email` | `VARCHAR2` | IN | Adres email do sprawdzenia |

#### Wartość zwracana

| Typ | Wartość | Opis |
|-----|---------|------|
| `BOOLEAN` | `TRUE` | Email jest już używany |
| `BOOLEAN` | `FALSE` | Email jest dostępny |

#### Przykład użycia

```sql
DECLARE
    v_zajety BOOLEAN;
BEGIN
    v_zajety := pkg_gielda_ext.czy_email_istnieje('jan@example.com');

    IF v_zajety THEN
        DBMS_OUTPUT.PUT_LINE('Email jest już zarejestrowany');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Email jest dostępny');
    END IF;
END;
```

---

### `weryfikuj_haslo`

Weryfikuje hasło użytkownika podczas logowania.

#### Sygnatura

```sql
FUNCTION weryfikuj_haslo(
    p_login IN VARCHAR2,
    p_haslo IN VARCHAR2
) RETURN NUMBER;
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_login` | `VARCHAR2` | IN | Login użytkownika |
| `p_haslo` | `VARCHAR2` | IN | Hasło do weryfikacji |

#### Wartość zwracana

| Typ | Wartość | Opis |
|-----|---------|------|
| `NUMBER` | `user_id` | Poprawne uwierzytelnienie - zwraca ID użytkownika |
| `NUMBER` | `NULL` | Niepoprawny login lub hasło |

#### Logika biznesowa

1. Pobiera rekord użytkownika na podstawie loginu
2. Porównuje podane hasło z zapisanym w bazie
3. Zwraca `user_id` jeśli hasła są zgodne, `NULL` w przeciwnym razie

> **Uwaga bezpieczeństwa:** Obecna implementacja używa prostego porównania tekstowego haseł. W środowisku produkcyjnym należy użyć hashowania (np. bcrypt, PBKDF2).

#### Przykład użycia

```sql
DECLARE
    v_user_id NUMBER;
BEGIN
    v_user_id := pkg_gielda_ext.weryfikuj_haslo(
        p_login => 'jan_kowalski',
        p_haslo => 'SecurePass123!'
    );

    IF v_user_id IS NOT NULL THEN
        DBMS_OUTPUT.PUT_LINE('Zalogowano pomyślnie. User ID: ' || v_user_id);
    ELSE
        DBMS_OUTPUT.PUT_LINE('Nieprawidłowy login lub hasło');
    END IF;
END;
```

---

### `oblicz_prowizje`

Oblicza wartość prowizji dla transakcji.

#### Sygnatura

```sql
FUNCTION oblicz_prowizje(
    p_wartosc IN NUMBER,
    p_stawka  IN NUMBER DEFAULT c_prowizja_domyslna
) RETURN NUMBER;
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_wartosc` | `NUMBER` | IN | Wartość transakcji |
| `p_stawka` | `NUMBER` | IN | Stawka prowizji (domyślnie: 0.0039 = 0.39%) |

#### Wartość zwracana

| Typ | Opis |
|-----|------|
| `NUMBER` | Kwota prowizji zaokrąglona do 2 miejsc po przecinku |

#### Wzór

```
prowizja = ROUND(p_wartosc × p_stawka, 2)
```

#### Przykład użycia

```sql
DECLARE
    v_prowizja NUMBER;
BEGIN
    -- Prowizja domyślna (0.39%)
    v_prowizja := pkg_gielda_ext.oblicz_prowizje(p_wartosc => 10000);
    DBMS_OUTPUT.PUT_LINE('Prowizja standardowa: ' || v_prowizja);
    -- Wynik: 39.00

    -- Prowizja niestandardowa (0.5%)
    v_prowizja := pkg_gielda_ext.oblicz_prowizje(
        p_wartosc => 10000,
        p_stawka  => 0.005
    );
    DBMS_OUTPUT.PUT_LINE('Prowizja 0.5%: ' || v_prowizja);
    -- Wynik: 50.00
END;
```

---

## Tabele referencyjne

Pakiet `pkg_gielda_ext` operuje na następujących tabelach:

| Tabela | Operacje | Opis |
|--------|----------|------|
| `UZYTKOWNICY` | SELECT, INSERT | Zarządzanie kontami użytkowników |
| `PORTFELE` | SELECT, INSERT, UPDATE | Zarządzanie portfelami |
| `INSTRUMENTY` | SELECT | Walidacja instrumentów finansowych |
| `ZLECENIA` | SELECT, INSERT, UPDATE | Zarządzanie zleceniami |
| `DANE_DZIENNE` | SELECT | Pobieranie cen historycznych |
| `POZYCJE` | SELECT | Kalkulacja wartości portfela |

---

## Reguły biznesowe

### 1. Unikalność danych użytkownika
- Login musi być unikalny w całym systemie
- Email musi być unikalny w całym systemie

### 2. Walidacja zleceń
- Typ zlecenia: MARKET, LIMIT lub STOP
- Strona zlecenia: KUPNO lub SPRZEDAZ
- Ilość musi być > 0
- Zlecenia LIMIT wymagają podania ceny limitu

### 3. Statusy zleceń
- `OCZEKUJACE` - nowe zlecenie, gotowe do realizacji
- `WYKONANE` - zlecenie zrealizowane
- `ANULOWANE` - zlecenie anulowane przez użytkownika
- `CZESCIOWE` - zlecenie częściowo zrealizowane

### 4. Anulowanie zleceń
- Można anulować tylko zlecenia w statusie OCZEKUJACE

### 5. Zlecenia limitowane
- KUPNO: wykonanie gdy cena <= limit (kupuj tanio)
- SPRZEDAZ: wykonanie gdy cena >= limit (sprzedaj drogo)

### 6. Time Travel
- Wszystkie funkcje związane z datą historyczną używają ostatniej dostępnej ceny nie późniejszej niż podana data
- Umożliwia analizę "what-if" na danych historycznych

### 7. Waluty
- Portfel ma przypisaną walutę przy tworzeniu
- Waluta jest automatycznie konwertowana do wielkich liter

### 8. Bezpieczeństwo haseł
- Obecnie: proste porównanie tekstowe
- Rekomendacja: wdrożenie hashowania w środowisku produkcyjnym
