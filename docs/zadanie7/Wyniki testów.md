# Wyniki testów funkcjonalnych (Zadanie 7)

**Projekt:** ExtLearnerUJ · **Zespół:** SJUJ · **Data wykonania:** 11.06.2026
**Środowisko:** Windows, Python 3.x, Django 5.2, SQLite, przeglądarka Chromium

Testy wykonano ręcznie według scenariuszy z `przypadki-testowe.md`.
Screenshoty z wykonania znajdują się w katalogu `screenshoty/` (nazwy plików
odpowiadają identyfikatorom przypadków).

| ID | Wymaganie | Rzeczywisty rezultat | Screenshot | Wynik |
| :--- | :--- | :--- | :--- | :---: |
| TC-01 | FR-01 | Po rejestracji wymagany kod; po jego wpisaniu konto aktywne, logowanie prowadzi na panel | `screenshoty/tc-01.png` | OK |
| TC-02 | FR-01 | Logowanie niezweryfikowanym kontem przekierowuje na ekran weryfikacji; „Wyślij kod ponownie" wysyła nowy kod | `screenshoty/tc-02.png` | OK |
| TC-03 | FR-02 | Wniosek z certyfikatem PDF i wynikiem testu widoczny u admina | `screenshoty/tc-03.png` | OK |
| TC-04 | FR-02 | Plik .zip odrzucony z komunikatem walidacji; wniosek nieutworzony | `screenshoty/tc-04.png` | OK |
| TC-05 | FR-03 | Konto i powiązane dane usunięte; logowanie niemożliwe; materiały zniknęły | `screenshoty/tc-05.png` | OK |
| TC-06 | FR-03 | Błędne hasło → komunikat, konto nietknięte | `screenshoty/tc-06.png` | OK |
| TC-07 | FR-04 | Raport procentowy per kategoria z wypełnionymi paskami | `screenshoty/tc-07.png` | OK |
| TC-08 | FR-04 | Obszary < 50% wyróżnione kolorem akcentu i wskazane do nauki | `screenshoty/tc-08.png` | OK |
| TC-09 | FR-05 | Sekcja „Rekomendowane dla Ciebie" z materiałami ze słabych kategorii | `screenshoty/tc-09.png` | OK |
| TC-10 | FR-05 | Brak rekomendacji bez słabych obszarów | `screenshoty/tc-10.png` | OK |
| TC-11 | FR-06 | Zegar odlicza; zakończenie przed czasem pokazuje wynik | `screenshoty/tc-11.png` | OK |
| TC-12 | FR-06 | Po 0:00 odpowiedzi odrzucane serwerowo; podejście zamknięte i ocenione automatycznie | `screenshoty/tc-12.png` | OK |
| TC-13 | FR-07 | Punkty wzrosły po ukończonym teście | `screenshoty/tc-13.png` | OK |
| TC-14 | FR-07 | „Najaktywniejsi użytkownicy": top 10 malejąco + pozycja zalogowanego | `screenshoty/tc-14.png` | OK |
| TC-15 | FR-08 | Materiał zapisany ze statusem „Oczekuje", widoczny w filtrach „Oczekujące" i „Moje" | `screenshoty/tc-15.png` | OK |
| TC-16 | FR-08 | Za duży / zły typ pliku odrzucony z komunikatem | `screenshoty/tc-16.png` | OK |
| TC-17 | FR-09 | Materiał z 2 głosami wyżej w kolejce moderatora | `screenshoty/tc-17.png` | OK |
| TC-18 | FR-09 | Drugi głos tego samego użytkownika nie zwiększa licznika | `screenshoty/tc-18.png` | OK |
| TC-19 | FR-10 | Pełny cykl: rezerwacja → zaznaczenia + komentarze + ocena → publikacja; student widzi feedback i może ocenić sprawdzającego | `screenshoty/tc-19.png` | OK |
| TC-20 | FR-10 | Drugi moderator nie może przejąć zarezerwowanej pracy; jedno powiadomienie o rezerwacji | `screenshoty/tc-20.png` | OK |
| TC-21 | FR-11 | Blokada 7 dni: sesje unieważnione, przy logowaniu komunikat z datą końca | `screenshoty/tc-21.png` | OK |
| TC-22 | FR-11 | Po upływie terminu blokady logowanie udane (auto-odblokowanie) | `screenshoty/tc-22.png` | OK |
| TC-23 | FR-12 | Akceptacja wniosku → rola Moderator, panel Moderacja dostępny | `screenshoty/tc-23.png` | OK |
| TC-24 | FR-12 | „Zabierz moderatora" wraca rolę Student, powiadomienie wysłane | `screenshoty/tc-24.png` | OK |
| TC-25 | FR-12 | Wynik < 50% → automatyczne odrzucenie; wniosek niewidoczny u admina | `screenshoty/tc-25.png` | OK |
| TC-26 | FR-13 | Zgłoszenie w kolejce admina, licznik wzrósł, link do profilu autora | `screenshoty/tc-26.png` | OK |
| TC-27 | FR-13 | Decyzja „zasadne" usuwa materiał; autor i zgłaszający powiadomieni | `screenshoty/tc-27.png` | OK |
| TC-28 | FR-14 | Panel zarobków: liczba prac i suma = pełna cena pakietu (bez marży) | `screenshoty/tc-28.png` | OK |
| TC-29 | FR-14 | Kolumna „Zarobek" przy pracy w kolejce | `screenshoty/tc-29.png` | OK |
| TC-30 | FR-15 | Praca w kolejce moderatora dopiero po zatwierdzeniu rozliczenia | `screenshoty/tc-30.png` | OK |
| TC-31 | FR-15 | Bramki wyszarzone „niedostępne"; wymuszony BLIK odrzucony serwerowo | `screenshoty/tc-31.png` | OK |
| TC-32 | FR-15 | Powiadomienie o rezerwacji z e-mailem sprawdzającego; kontakt w edytorze | `screenshoty/tc-32.png` | OK |

**Podsumowanie:** 32 przypadków · 32 OK · 0 NOK.

## Wykryte anomalie i ich obsługa

| Lp. | Wymaganie | Rozbieżność | Status |
| :--- | :--- | :--- | :--- |
| A-1 | FR-01 | Kod weryfikacyjny zamiast linku aktywacyjnego | Zaakceptowane — rozwiązanie funkcjonalnie równoważne (konto nieaktywne do potwierdzenia adresu); kryterium spełnione |
| A-2 | FR-14 | Brak zlecania wypłat i faktur — panel pokazuje wyłącznie statystyki zarobków | Zmiana wymagania decyzją zespołu (rozliczenia poza platformą, zerowa marża); testy zaktualizowane (TC-28/29) |
| A-3 | FR-15 | Bramka płatności zastąpiona rozliczeniem indywidualnym | Zmiana wymagania decyzją zespołu; kryterium „praca u moderatora dopiero po opłaceniu" zachowane w formie „po zatwierdzeniu rozliczenia" (TC-30/31/32) |
