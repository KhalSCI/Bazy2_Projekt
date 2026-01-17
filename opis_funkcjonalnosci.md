# Opis funkcjonalności aplikacji – System Symulacji Giełdy

## 1. Cel aplikacji

Celem aplikacji jest umożliwienie użytkownikom symulacji inwestycji giełdowych poprzez
zarządzanie wirtualnym portfelem inwestycyjnym oraz składanie zleceń kupna i sprzedaży
akcji spółek notowanych na rynku.

Aplikacja ma charakter edukacyjno-symulacyjny i pozwala:

* analizować historyczne dane rynkowe,
* symulować strategie inwestycyjne,
* obserwować wpływ decyzji inwestycyjnych na wartość portfela w czasie.

---

## 2. Główne funkcjonalności

### 2.1. Widok portfela inwestycyjnego

Główny ekran aplikacji prezentujący kompleksowy przegląd sytuacji finansowej użytkownika.

#### 2.1.1. Podsumowanie portfela

Wyświetlane informacje:

* Aktualna wartość całkowita portfela (gotówka + wartość posiadanych akcji)
* Dostępne saldo gotówkowe
* Całkowity zysk lub strata od początku symulacji:

  * w PLN
  * w procentach (%)

Wartości te są obliczane na podstawie danych rynkowych z aktualnie wybranej daty
(symulowany „dzień bieżący”).

---

#### 2.1.2. Lista posiadanych akcji

Tabela prezentująca aktualne pozycje w portfelu. Dla każdej spółki wyświetlane są:

* Ticker spółki
* Pełna nazwa spółki
* Liczba posiadanych akcji
* Średnia cena zakupu
* Cena rynkowa z wybranej daty
* Wartość pozycji (liczba akcji × cena rynkowa)
* Zysk lub strata:

  * w PLN
  * w procentach (%)
* Wskaźnik trendu cenowego:

  * ↑ (kolor zielony) – wzrost ceny
  * ↓ (kolor czerwony) – spadek ceny

---

#### 2.1.3. Funkcjonalności widoku portfela

* Sortowanie tabeli według dowolnej kolumny
* Przycisk **„Sprzedaj”** przy każdej pozycji, przekierowujący do formularza sprzedaży
* Wykres zmian wartości portfela w czasie (dla aktualnego zakresu dat)

---

#### 2.1.4. Funkcja „Podróż w czasie” (Time Travel)

Widok portfela umożliwia symulację stanu inwestycji w przeszłości.

Funkcjonalność obejmuje:

* Kalendarz lub suwak czasowy umożliwiający wybór daty historycznej
* Po wybraniu daty aplikacja:

  * prezentuje stan portfela na wybrany dzień,
  * wyświetla historyczne ceny akcji z tej daty,
  * przelicza wartość portfela oraz zysk/stratę na podstawie danych historycznych

Po „przeniesieniu się w czasie” użytkownik może:

* składać zlecenia kupna i sprzedaży tak, jakby wybrana data była dniem bieżącym,
* symulować alternatywne decyzje inwestycyjne („co by było, gdyby…”).

Funkcja ta ma charakter symulacyjny i nie modyfikuje rzeczywistych danych historycznych.

---

### 2.2. Formularz transakcji kupna i sprzedaży (zlecenia)

Wszystkie operacje kupna i sprzedaży akcji realizowane są wyłącznie poprzez **zlecenia**.

---

#### 2.2.1. Formularz zlecenia kupna akcji

##### Pola formularza

* **Spółka**

  * Lista rozwijana zawierająca wszystkie dostępne spółki
  * Wyświetlane informacje:

    * ticker spółki (np. `TECH`)
    * pełna nazwa
    * cena rynkowa dla wybranej daty

* **Data transakcji**

  * Data bieżąca (domyślna)
  * Data historyczna (w trybie „time travel”)

* **Typ zlecenia**

  * Zlecenie rynkowe (market)
  * Zlecenie z limitem ceny (limit)

* **Cena limitowa**

  * Pole aktywne tylko dla zlecenia typu limit
  * Określa maksymalną cenę zakupu

* **Liczba akcji**

  * Pole numeryczne (wartość dodatnia)

* **Cena jednostkowa**

  * Automatycznie pobierana z bazy:

    * dla zlecenia market – aktualna cena rynkowa
    * dla zlecenia limit – cena limitowa

* **Wartość transakcji**

  * Automatycznie wyliczana (liczba akcji × cena)

* **Prowizja**

  * Opcjonalna
  * Domyślnie 0

* **Dostępne środki**

  * Informacyjne pole pokazujące aktualne saldo gotówkowe

---

##### Walidacje i kontrole

* Sprawdzenie, czy użytkownik posiada wystarczające środki finansowe
* Kontrola, czy liczba akcji > 0
* Weryfikacja poprawności ceny limitowej (dla zlecenia limit)
* Sprawdzenie, czy spółka istniała i była notowana w wybranej dacie
* Dodatkowe kontrole logiczne i biznesowe realizowane w bazie danych

---

#### 2.2.2. Formularz zlecenia sprzedaży akcji

##### Pola formularza

* **Spółka**

  * Lista rozwijana zawierająca wyłącznie akcje posiadane w portfelu
  * Wyświetlane informacje:

    * ticker i nazwa spółki
    * liczba posiadanych akcji
    * średnia cena zakupu
    * aktualna cena rynkowa

* **Data transakcji**

  * Data bieżąca lub historyczna

* **Typ zlecenia**

  * Zlecenie rynkowe (market)
  * Zlecenie z limitem ceny (limit)

* **Cena limitowa**

  * Pole aktywne tylko dla zlecenia limit
  * Określa minimalną cenę sprzedaży

* **Liczba akcji do sprzedaży**

  * Pole numeryczne
  * Maksymalna wartość = liczba posiadanych akcji

* **Cena jednostkowa**

  * Automatycznie pobierana z bazy dla wybranej daty

* **Wartość sprzedaży**

  * Automatycznie wyliczana

* **Zysk / strata**

  * Wyliczana według wzoru:

    ```
    (cena sprzedaży − średnia cena zakupu) × liczba akcji
    ```

---

##### Walidacje

* Sprawdzenie, czy użytkownik posiada wystarczającą liczbę akcji
* Kontrola, czy liczba akcji > 0 oraz ≤ liczba posiadanych
* Walidacja ceny limitowej
* Dodatkowe kontrole logiczne realizowane po stronie bazy danych

---

## 3. Obsługa zleceń

* Zlecenia rynkowe realizowane są natychmiast dla wybranej daty
* Zlecenia z limitem ceny:

  * pozostają aktywne do momentu spełnienia warunku cenowego,
  * są realizowane automatycznie, gdy cena rynkowa osiągnie wymagany poziom
* Aplikacja umożliwia przegląd:

  * zleceń aktywnych,
  * zleceń zrealizowanych,
  * zleceń anulowanych

Cała logika realizacji zleceń, aktualizacji portfela, prowizji oraz walidacji integralności
jest realizowana przez procedury i funkcje składowane w bazie danych.
