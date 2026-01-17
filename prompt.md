Zaimplementuj kompletną aplikację webową w Pythonie z wykorzystaniem Streamlit, współpracującą z bazą danych OracleDB. Aplikacja musi być zgodna z dostarczonym schematem relacyjnym, diagramem ER oraz pakietem PL/SQL `pkg_gielda`.

---

## Zakres funkcjonalny aplikacji

Aplikacja ma umożliwiać naiwnemu użytkownikowi pełne zarządzanie danymi w całym schemacie bazy danych poprzez wiele logicznych ekranów:

* **Portfel użytkownika**
* **Kupno i sprzedaż akcji**
* **Rynek (notowania spółek)**
* **Historia transakcji i zleceń**
* **Ustawienia użytkownika**

Użytkownik musi mieć możliwość przeglądania, wyszukiwania, dodawania, modyfikowania oraz usuwania danych, z zachowaniem integralności referencyjnej oraz walidacji biznesowej.

---

## Dane rynkowe

Dzienne ceny akcji mają być pobierane z zewnętrznego API (np. Yahoo Finance) i zapisywane do bazy danych. Wystarczy obsłużyć dane historyczne obejmujące **rok 2025**.

W projekcie istnieje katalog **`utils/`**, który zawiera gotowe pliki Python służące do:

* pobierania danych z Yahoo Finance,
* wstępnego przetwarzania notowań,
* zapisu danych do bazy danych.

Pliki te:

* **należy ponownie wykorzystać** w aplikacji,
* mogą wymagać **niewielkich modyfikacji lub dostosowania interfejsu**,
* są poprawne logicznie i działają zgodnie z założeniami projektu.

Nie należy pisać importu danych rynkowych od zera, jeżeli możliwe jest użycie lub rozszerzenie istniejących modułów w katalogu `utils`.

Dane rynkowe stanowią podstawę do:

* realizacji zleceń,
* wyceny portfela,
* symulacji historycznych (time travel).

---

## Mechanizm kupna i sprzedaży (kluczowe wymaganie)

Każda operacja kupna lub sprzedaży akcji **musi odbywać się wyłącznie poprzez zlecenia**.

W systemie należy zaimplementować co najmniej dwa typy zleceń:

### 1. Zlecenie rynkowe (market)

* Wykonywane natychmiast po aktualnej cenie rynkowej (dla wybranej daty).

### 2. Zlecenie z limitem ceny (limit order)

* Użytkownik podaje:

  * maksymalną cenę kupna lub
  * minimalną cenę sprzedaży.
* Zlecenie realizuje się **wyłącznie w momencie**, gdy cena danej spółki:

  * dla kupna: jest **równa lub niższa** od ceny limitowej,
  * dla sprzedaży: jest **równa lub wyższa** od ceny limitowej.
* Do momentu spełnienia warunku cenowego zlecenie pozostaje aktywne.

Realizacja zleceń, aktualizacja portfela, naliczanie prowizji oraz obsługa środków pieniężnych muszą być realizowane po stronie bazy danych.

---

## Logika biznesowa i PL/SQL

* **Wszystkie operacje biznesowe** (kupno, sprzedaż, realizacja zleceń, obliczanie wartości portfela, prowizje, walidacje) muszą wykorzystywać **procedury i funkcje składowane** w OracleDB.
* Aplikacja Streamlit pełni wyłącznie rolę warstwy prezentacji i wywołuje logikę bazy danych.
* Pakiet `pkg_gielda` może być:

  * rozszerzany,
  * modyfikowany,
    jeżeli brakuje wymaganej logiki biznesowej.
* **Nie wolno zmieniać ani usuwać nazw istniejących tabel**.
* **Nie wolno dodawać nowych kluczy obcych** – aplikacja oraz procedury muszą operować wyłącznie na aktualnie istniejących relacjach.
* Należy poprawnie obsługiwać:

  * sekwencje,
  * transakcje,
  * błędy integralności i wyjątki Oracle.

---

## Funkcja „Time Travel” (symulacja podróży w czasie)

Aplikacja musi umożliwiać symulację stanu portfela w przeszłości.

* Z poziomu widoku **portfela** użytkownik może wybrać datę historyczną (np. 1 stycznia 2025).
* Po „przeniesieniu się w czasie”:

  * wszystkie operacje (kupno, sprzedaż, realizacja zleceń) odbywają się **z wykorzystaniem danych rynkowych z wybranej daty**,
  * użytkownik może sprawdzić historyczną wartość portfela oraz procentowy zysk lub stratę,
  * możliwe jest kupowanie i sprzedawanie akcji tak, jakby wybrana data była „aktualnym dniem”.
* Funkcja ma charakter **symulacyjny**:

  * nie modyfikuje rzeczywistych danych historycznych,
  * operuje na nich wyłącznie w kontekście wybranego punktu w czasie.

---

## Interfejs użytkownika

* Formularze z podpowiedziami:

  * listy rozwijane (selectbox),
  * wartości domyślne,
  * dynamiczne podpowiedzi.
* Walidacja danych:

  * po stronie aplikacji,
  * po stronie bazy danych.
* Czytelne i przyjazne komunikaty błędów biznesowych zamiast surowych komunikatów Oracle.
* Jasne rozróżnienie między:

  * zleceniami aktywnymi,
  * zleceniami zrealizowanymi,
  * zleceniami anulowanymi.

---

Celem jest stworzenie kompletnej, spójnej aplikacji giełdowej, w której Streamlit pełni rolę warstwy prezentacji, a cała logika biznesowa, integralność danych oraz przetwarzanie transakcji są egzekwowane przez OracleDB i pakiet PL/SQL `pkg_gielda`.
