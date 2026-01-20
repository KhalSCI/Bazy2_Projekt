# Dokumentacja Pakietu `pkg_gielda`

## Spis treści

1. [Opis ogólny](#opis-ogólny)
2. [Stałe](#stałe)
3. [Funkcje](#funkcje)
   - [oblicz_wartosc_portfela](#oblicz_wartosc_portfela)
   - [oblicz_zysk_procent](#oblicz_zysk_procent)
   - [pobierz_aktualna_cene](#pobierz_aktualna_cene)
4. [Procedury](#procedury)
   - [wykonaj_zlecenie_kupna](#wykonaj_zlecenie_kupna)
   - [wykonaj_zlecenie_sprzedazy](#wykonaj_zlecenie_sprzedazy)
   - [aktualizuj_pozycje_portfela](#aktualizuj_pozycje_portfela)
   - [wplac_srodki](#wplac_srodki)
5. [Tabele referencyjne](#tabele-referencyjne)
6. [Reguły biznesowe](#reguły-biznesowe)

---

## Opis ogólny

Pakiet `pkg_gielda` stanowi **rdzeń logiki biznesowej** symulatora giełdy. Zawiera podstawowe procedury i funkcje niezbędne do:

- Realizacji transakcji kupna i sprzedaży instrumentów finansowych
- Obliczania wartości portfela inwestycyjnego
- Aktualizacji pozycji portfelowych na podstawie aktualnych cen rynkowych
- Zarządzania saldem gotówkowym portfela

Pakiet jest zaprojektowany z myślą o **edukacyjnym symulatorze giełdy** i implementuje pełny cykl życia zlecenia od utworzenia do realizacji.

### Architektura

```
Warstwa prezentacji (Streamlit)
        ↓
Warstwa serwisowa (Python)
        ↓
    pkg_gielda  ← Jesteś tutaj
        ↓
   Baza danych Oracle
```

---

## Stałe

### `c_prowizja_domyslna`

| Atrybut | Wartość |
|---------|---------|
| **Typ** | `NUMBER` |
| **Wartość** | `0.0039` (0,39%) |
| **Opis** | Domyślna stawka prowizji dla wszystkich transakcji kupna i sprzedaży |

**Zastosowanie:**
- Prowizja jest naliczana od wartości każdej transakcji
- Przy kupnie: prowizja zwiększa całkowity koszt
- Przy sprzedaży: prowizja zmniejsza przychód netto

**Przykład kalkulacji:**
```
Wartość transakcji: 10 000 PLN
Prowizja: 10 000 × 0.0039 = 39 PLN
```

---

## Funkcje

### `oblicz_wartosc_portfela`

Oblicza całkowitą wartość portfela inwestycyjnego (gotówka + wartość pozycji).

#### Sygnatura

```sql
FUNCTION oblicz_wartosc_portfela(
    p_portfolio_id IN NUMBER
) RETURN NUMBER;
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_portfolio_id` | `NUMBER` | IN | Identyfikator portfela |

#### Wartość zwracana

| Typ | Opis |
|-----|------|
| `NUMBER` | Całkowita wartość portfela zaokrąglona do 2 miejsc po przecinku |

#### Logika biznesowa

1. Sumuje bieżącą wartość (`wartosc_biezaca`) wszystkich pozycji w portfelu gdzie `ilosc_akcji > 0`
2. Dodaje saldo gotówkowe portfela (`saldo_gotowkowe`)
3. Zaokrągla wynik do 2 miejsc po przecinku
4. Zwraca 0 jeśli portfel nie istnieje lub nie ma danych

#### Przykład użycia

```sql
DECLARE
    v_wartosc NUMBER;
BEGIN
    v_wartosc := pkg_gielda.oblicz_wartosc_portfela(p_portfolio_id => 1);
    DBMS_OUTPUT.PUT_LINE('Wartość portfela: ' || v_wartosc);
END;
```

#### Obsługa błędów

| Wyjątek | Reakcja |
|---------|---------|
| `NO_DATA_FOUND` | Zwraca 0 |
| Inne wyjątki | Podnosi błąd z komunikatem SQLERRM |

---

### `oblicz_zysk_procent`

Oblicza procentowy zysk lub stratę na pozycji.

#### Sygnatura

```sql
FUNCTION oblicz_zysk_procent(
    p_wartosc_zakupu  IN NUMBER,
    p_wartosc_biezaca IN NUMBER
) RETURN NUMBER;
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_wartosc_zakupu` | `NUMBER` | IN | Wartość zakupu (koszt bazowy) |
| `p_wartosc_biezaca` | `NUMBER` | IN | Bieżąca wartość rynkowa |

#### Wartość zwracana

| Typ | Opis |
|-----|------|
| `NUMBER` | Procentowy zysk/strata zaokrąglony do 4 miejsc po przecinku |

#### Logika biznesowa

**Wzór:**
```
zysk_procent = ((wartosc_biezaca - wartosc_zakupu) / wartosc_zakupu) × 100
```

**Przypadki brzegowe:**
- Jeśli `p_wartosc_zakupu` jest NULL lub 0, zwraca 0
- W przypadku wyjątku zwraca 0

#### Przykład użycia

```sql
DECLARE
    v_zysk NUMBER;
BEGIN
    -- Zakup za 1000, obecnie warte 1250 = +25%
    v_zysk := pkg_gielda.oblicz_zysk_procent(
        p_wartosc_zakupu  => 1000,
        p_wartosc_biezaca => 1250
    );
    DBMS_OUTPUT.PUT_LINE('Zysk: ' || v_zysk || '%'); -- Wynik: 25.0000%
END;
```

---

### `pobierz_aktualna_cene`

Pobiera najnowszą cenę zamknięcia dla instrumentu finansowego.

#### Sygnatura

```sql
FUNCTION pobierz_aktualna_cene(
    p_instrument_id IN NUMBER
) RETURN NUMBER;
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_instrument_id` | `NUMBER` | IN | Identyfikator instrumentu finansowego |

#### Wartość zwracana

| Typ | Opis |
|-----|------|
| `NUMBER` | Cena zamknięcia z najnowszej sesji lub NULL jeśli brak danych |

#### Logika biznesowa

1. Wyszukuje w tabeli `DANE_DZIENNE` rekord z maksymalną datą notowań dla danego instrumentu
2. Zwraca wartość `cena_zamkniecia` z tego rekordu
3. Zwraca NULL jeśli nie znaleziono danych

#### Przykład użycia

```sql
DECLARE
    v_cena NUMBER;
BEGIN
    v_cena := pkg_gielda.pobierz_aktualna_cene(p_instrument_id => 1);
    IF v_cena IS NOT NULL THEN
        DBMS_OUTPUT.PUT_LINE('Aktualna cena: ' || v_cena);
    ELSE
        DBMS_OUTPUT.PUT_LINE('Brak danych cenowych');
    END IF;
END;
```

---

## Procedury

### `wykonaj_zlecenie_kupna`

Realizuje zlecenie kupna instrumentu finansowego.

#### Sygnatura

```sql
PROCEDURE wykonaj_zlecenie_kupna(
    p_order_id        IN NUMBER,
    p_cena_wykonania  IN NUMBER,
    p_data_symulacji  IN TIMESTAMP DEFAULT SYSTIMESTAMP,
    p_wynik           OUT VARCHAR2
);
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_order_id` | `NUMBER` | IN | Identyfikator zlecenia do wykonania |
| `p_cena_wykonania` | `NUMBER` | IN | Cena po której zostanie zrealizowane zlecenie |
| `p_data_symulacji` | `TIMESTAMP` | IN | Data/czas symulacji (domyślnie: SYSTIMESTAMP) |
| `p_wynik` | `VARCHAR2` | OUT | Komunikat wynikowy ("OK: ..." lub "BŁĄD: ...") |

#### Logika biznesowa

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Pobierz dane zlecenia                                    │
│    (portfolio_id, instrument_id, ilość)                     │
│    Warunek: status = 'OCZEKUJACE' AND strona = 'KUPNO'      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Oblicz koszty                                            │
│    wartosc_transakcji = ilość × cena_wykonania              │
│    prowizja = wartosc_transakcji × 0.0039                   │
│    koszt_calkowity = wartosc_transakcji + prowizja          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Sprawdź środki                                           │
│    saldo_gotowkowe >= koszt_calkowity?                      │
│    NIE → Błąd "Niewystarczające środki"                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Aktualizuj saldo portfela                                │
│    saldo_gotowkowe -= koszt_calkowity                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Utwórz rekord transakcji w tabeli TRANSAKCJE             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Aktualizuj/Utwórz pozycję w POZYCJE                      │
│    - Istniejąca: oblicz średnią ważoną cenę zakupu          │
│    - Nowa: utwórz rekord pozycji                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Oznacz zlecenie jako 'WYKONANE'                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. COMMIT                                                   │
└─────────────────────────────────────────────────────────────┘
```

#### Średnia ważona cena zakupu

Przy dokupowaniu akcji tego samego instrumentu:

```
nowa_srednia_cena = (stara_ilosc × stara_cena + nowa_ilosc × nowa_cena) / (stara_ilosc + nowa_ilosc)
```

#### Przykład użycia

```sql
DECLARE
    v_wynik VARCHAR2(4000);
BEGIN
    pkg_gielda.wykonaj_zlecenie_kupna(
        p_order_id       => 123,
        p_cena_wykonania => 150.50,
        p_wynik          => v_wynik
    );
    DBMS_OUTPUT.PUT_LINE(v_wynik);
END;
```

#### Obsługa błędów

| Komunikat | Przyczyna |
|-----------|-----------|
| `BŁĄD: Nie znaleziono oczekującego zlecenia kupna o podanym ID` | Zlecenie nie istnieje lub nie jest w statusie OCZEKUJACE |
| `BŁĄD: Niewystarczające środki na koncie...` | Saldo portfela jest mniejsze niż całkowity koszt transakcji |
| `BŁĄD: [SQLERRM]` | Inny błąd bazy danych |

---

### `wykonaj_zlecenie_sprzedazy`

Realizuje zlecenie sprzedaży instrumentu finansowego.

#### Sygnatura

```sql
PROCEDURE wykonaj_zlecenie_sprzedazy(
    p_order_id        IN NUMBER,
    p_cena_wykonania  IN NUMBER,
    p_data_symulacji  IN TIMESTAMP DEFAULT SYSTIMESTAMP,
    p_wynik           OUT VARCHAR2
);
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_order_id` | `NUMBER` | IN | Identyfikator zlecenia do wykonania |
| `p_cena_wykonania` | `NUMBER` | IN | Cena po której zostanie zrealizowane zlecenie |
| `p_data_symulacji` | `TIMESTAMP` | IN | Data/czas symulacji (domyślnie: SYSTIMESTAMP) |
| `p_wynik` | `VARCHAR2` | OUT | Komunikat wynikowy |

#### Logika biznesowa

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Pobierz dane zlecenia                                    │
│    (portfolio_id, instrument_id, ilość)                     │
│    Warunek: status = 'OCZEKUJACE' AND strona = 'SPRZEDAZ'   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Sprawdź pozycję w portfelu                               │
│    - Czy pozycja istnieje?                                  │
│    - Czy ilosc_akcji >= zlecona ilość?                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Oblicz przychód                                          │
│    wartosc_transakcji = ilość × cena_wykonania              │
│    prowizja = wartosc_transakcji × 0.0039                   │
│    przychod_netto = wartosc_transakcji - prowizja           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Aktualizuj saldo portfela                                │
│    saldo_gotowkowe += przychod_netto                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Utwórz rekord transakcji                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Aktualizuj pozycję                                       │
│    - Sprzedaż całości: DELETE pozycji                       │
│    - Sprzedaż części: UPDATE ilości                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Oznacz zlecenie jako 'WYKONANE'                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. COMMIT                                                   │
└─────────────────────────────────────────────────────────────┘
```

#### Przykład użycia

```sql
DECLARE
    v_wynik VARCHAR2(4000);
BEGIN
    pkg_gielda.wykonaj_zlecenie_sprzedazy(
        p_order_id       => 124,
        p_cena_wykonania => 165.00,
        p_wynik          => v_wynik
    );
    DBMS_OUTPUT.PUT_LINE(v_wynik);
END;
```

#### Obsługa błędów

| Komunikat | Przyczyna |
|-----------|-----------|
| `BŁĄD: Nie znaleziono oczekującego zlecenia sprzedaży o podanym ID` | Zlecenie nie istnieje lub nie jest w statusie OCZEKUJACE |
| `BŁĄD: Brak pozycji w tym instrumencie` | Użytkownik nie posiada akcji tego instrumentu |
| `BŁĄD: Niewystarczająca ilość akcji. Posiadasz: X` | Próba sprzedaży większej ilości niż posiadana |
| `BŁĄD: [SQLERRM]` | Inny błąd bazy danych |

---

### `aktualizuj_pozycje_portfela`

Aktualizuje wartości bieżące wszystkich pozycji w portfelu na podstawie aktualnych cen rynkowych.

#### Sygnatura

```sql
PROCEDURE aktualizuj_pozycje_portfela(
    p_portfolio_id IN NUMBER
);
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_portfolio_id` | `NUMBER` | IN | Identyfikator portfela do aktualizacji |

#### Logika biznesowa

Dla każdej pozycji w portfelu gdzie `ilosc_akcji > 0`:

1. Pobierz aktualną cenę instrumentu (`pobierz_aktualna_cene`)
2. Jeśli cena jest dostępna, zaktualizuj:
   - `wartosc_biezaca = ilosc_akcji × aktualna_cena`
   - `zysk_strata = ilosc_akcji × (aktualna_cena - srednia_cena_zakupu)`
   - `zysk_strata_procent = oblicz_zysk_procent(...)`
   - `data_ostatniej_zmiany = SYSTIMESTAMP`

3. Zatwierdź zmiany (COMMIT)

#### Przykład użycia

```sql
BEGIN
    pkg_gielda.aktualizuj_pozycje_portfela(p_portfolio_id => 1);
    DBMS_OUTPUT.PUT_LINE('Pozycje zaktualizowane');
END;
```

#### Obsługa błędów

| Komunikat | Przyczyna |
|-----------|-----------|
| `-20003: Błąd podczas aktualizacji pozycji: [szczegóły]` | Błąd podczas aktualizacji (wykonywany ROLLBACK) |

#### Zastosowanie

Procedurę należy wywołać przed wyświetleniem portfela użytkownikowi, aby wartości P&L (Profit & Loss) były aktualne.

---

### `wplac_srodki`

Wpłaca środki pieniężne na portfel inwestycyjny.

#### Sygnatura

```sql
PROCEDURE wplac_srodki(
    p_portfolio_id IN NUMBER,
    p_kwota        IN NUMBER,
    p_wynik        OUT VARCHAR2
);
```

#### Parametry

| Parametr | Typ | Kierunek | Opis |
|----------|-----|----------|------|
| `p_portfolio_id` | `NUMBER` | IN | Identyfikator portfela |
| `p_kwota` | `NUMBER` | IN | Kwota do wpłaty |
| `p_wynik` | `VARCHAR2` | OUT | Komunikat wynikowy |

#### Logika biznesowa

1. Walidacja: kwota musi być większa od 0
2. Zwiększenie `saldo_gotowkowe` o wpłacaną kwotę
3. Pobranie waluty portfela (RETURNING)
4. Zatwierdzenie transakcji (COMMIT)

#### Przykład użycia

```sql
DECLARE
    v_wynik VARCHAR2(4000);
BEGIN
    pkg_gielda.wplac_srodki(
        p_portfolio_id => 1,
        p_kwota        => 10000,
        p_wynik        => v_wynik
    );
    DBMS_OUTPUT.PUT_LINE(v_wynik);
    -- Wynik: OK: Wpłacono 10000 USD
END;
```

#### Obsługa błędów

| Komunikat | Przyczyna |
|-----------|-----------|
| `BŁĄD: Kwota wpłaty musi być większa od zera` | Podano kwotę <= 0 |
| `BŁĄD: Nie znaleziono portfela` | Portfel o podanym ID nie istnieje |
| `BŁĄD: [SQLERRM]` | Inny błąd bazy danych |

---

## Tabele referencyjne

Pakiet `pkg_gielda` operuje na następujących tabelach:

| Tabela | Operacje | Opis |
|--------|----------|------|
| `PORTFELE` | SELECT, UPDATE | Saldo gotówkowe, waluta portfela |
| `POZYCJE` | SELECT, INSERT, UPDATE, DELETE | Pozycje inwestycyjne (akcje) |
| `ZLECENIA` | SELECT, UPDATE | Zlecenia giełdowe |
| `TRANSAKCJE` | INSERT | Historia transakcji |
| `DANE_DZIENNE` | SELECT | Dane cenowe (OHLCV) |
| `INSTRUMENTY` | SELECT (pośrednio przez POZYCJE) | Informacje o instrumentach |

---

## Reguły biznesowe

### 1. Prowizja
- Stała stawka 0,39% od wartości każdej transakcji
- Naliczana zarówno przy kupnie jak i sprzedaży

### 2. Średnia cena zakupu
- Przy dokupowaniu akcji obliczana jest średnia ważona
- Służy do kalkulacji zysku/straty

### 3. Saldo nieujemne
- Saldo gotówkowe portfela nie może spaść poniżej 0
- Constraint na poziomie tabeli: `saldo_gotowkowe >= 0`

### 4. Pozycje
- Jedna pozycja na instrument w ramach portfela (UNIQUE constraint)
- Sprzedaż całości akcji powoduje usunięcie rekordu pozycji
- Ilość akcji w pozycji musi być >= 0

### 5. Zlecenia
- Można wykonać tylko zlecenia w statusie `OCZEKUJACE`
- Po wykonaniu status zmienia się na `WYKONANE`

### 6. Symulacja czasowa
- Parametr `p_data_symulacji` pozwala na wykonanie transakcji z historyczną datą
- Używane w funkcji "time travel" symulatora

### 7. Atomowość operacji
- Wszystkie procedury używają COMMIT/ROLLBACK
- Gwarantuje spójność danych przy błędach

### 8. Waluta
- Każdy portfel ma przypisaną walutę (`waluta_portfela`)
- Transakcje zapisywane z walutą instrumentu (`waluta_transakcji`)
