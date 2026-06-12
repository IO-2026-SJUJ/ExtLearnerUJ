# Przypadki testowe — testy funkcjonalne

**Projekt:** ExtLearnerUJ · **Zespół:** SJUJ (Julia Łapiuk, Seweryn Olejnik)

Przypadki testowe pokrywają wymagania funkcjonalne FR-01…FR-15

**Środowisko testowe (warunki wspólne):** świeżo sklonowane repo, `cd src`,
aktywny venv, `pip install -r requirements.txt`, `python manage.py migrate`,
seedy: `seed_diagnostic`, `seed_materials`, `seed_packages`, `seed_exam`,
`seed_admin`; serwer: `python manage.py runserver`. Konto administratora:
`admin@uj.edu.pl` / `AdminHaslo123`. Bez skonfigurowanego SMTP w `.env` treść
maili (kod weryfikacyjny, link resetu) wypisywana jest w konsoli serwera.

---

## I. Rejestracja i Zarządzanie Kontem

### TC-01 *(FR-01)* — Rejestracja z weryfikacją e-mail
**Opis:** Nowe konto pozostaje nieaktywne do czasu potwierdzenia adresu kodem z e-maila.
**Kroki:**
1. Wejdź na `/register/`, podaj imię, e-mail, hasło (≥8 znaków) i wyślij formularz.
2. Odczytaj kod weryfikacyjny z wiadomości e-mail (lub z konsoli serwera).
3. Na stronie weryfikacji wpisz kod i zatwierdź.
4. Zaloguj się podanym e-mailem i hasłem.\
**Oczekiwany rezultat:** Po rejestracji system żąda kodu; po wpisaniu poprawnego kodu konto staje się aktywne i logowanie kończy się wejściem na panel główny.

### TC-02 *(FR-01)* — Blokada logowania przed weryfikacją
**Kroki:**
1. Zarejestruj konto, ale NIE wpisuj kodu weryfikacyjnego.
2. Spróbuj się zalogować tym kontem.\
**Oczekiwany rezultat:** Logowanie nie wpuszcza do aplikacji — system przekierowuje na ekran weryfikacji z komunikatem o konieczności potwierdzenia adresu; działa przycisk „Wyślij kod ponownie".

### TC-03 *(FR-02)* — Upload certyfikatu we wniosku o rolę moderatora
**Kroki:**
1. Zaloguj się jako student, wejdź „Zostań moderatorem".
2. Wypełnij motywację, załącz plik PDF jako certyfikat, rozwiąż test kwalifikacyjny (poprawnie) i wyślij.
3. Zaloguj się jako admin → Wnioski moderatorskie → otwórz wniosek.\
**Oczekiwany rezultat:** Wniosek widoczny u admina wraz z motywacją, linkiem do certyfikatu i wynikiem testu kwalifikacyjnego.

### TC-04 *(FR-02)* — Odrzucenie niedozwolonego typu certyfikatu
**Kroki:**
1. W formularzu wniosku załącz plik `.zip` (lub inny spoza PDF/JPG/PNG) i wyślij.\
**Oczekiwany rezultat:** Formularz zwraca błąd walidacji przy polu certyfikatu; wniosek nie zostaje utworzony.

### TC-05 *(FR-03)* — Trwałe usunięcie konta i danych
**Kroki:**
1. Zaloguj się jako student, który ma ≥1 materiał, ≥1 powiadomienie i wynik diagnostyki.
2. Panel główny → „Usuń konto i moje dane" → potwierdź hasłem i zaakceptuj ostrzeżenie.
3. Spróbuj zalogować się usuniętym kontem; jako admin sprawdź listę użytkowników i listę materiałów.\
**Oczekiwany rezultat:** Następuje wylogowanie z komunikatem o usunięciu; logowanie niemożliwe; konto zniknęło z listy użytkowników, a jego materiały i dane — z aplikacji.

### TC-06 *(FR-03)* — Błędne hasło nie usuwa konta
**Kroki:**
1. Na stronie usuwania konta podaj nieprawidłowe hasło i zatwierdź.\
**Oczekiwany rezultat:** Komunikat o nieprawidłowym haśle; konto i dane pozostają nietknięte, sesja aktywna.

## II. Proces Nauki i Egzaminów

### TC-07 *(FR-04)* — Test diagnostyczny z raportem per kategoria
**Kroki:**
1. Jako zalogowany student wejdź „Diagnostyka" i rozpocznij test.
2. Odpowiedz na wszystkie pytania (część celowo błędnie) i zakończ test.\
**Oczekiwany rezultat:** Ekran wyniku pokazuje procentowy wynik dla każdej kategorii (gramatyka, czytanie itd.) wraz z wypełnionymi paskami postępu odpowiadającymi procentom.

### TC-08 *(FR-04)* — Wyróżnienie słabych obszarów (< 50%)
**Kroki:**
1. Rozwiąż diagnostykę tak, aby w jednej kategorii uzyskać wynik < 50%, a w innej ≥ 50%.\
**Oczekiwany rezultat:** Obszary z wynikiem < 50% są wyróżnione (kolor akcentu) i wskazane jako te, od których warto zacząć naukę.

### TC-09 *(FR-05)* — Rekomendacje na podstawie słabych wyników
**Kroki:**
1. Uzyskaj w diagnostyce wynik < 50% w kategorii, w której istnieją zweryfikowane materiały (np. grammar).
2. Wejdź na panel główny.\
**Oczekiwany rezultat:** Sekcja „Rekomendowane dla Ciebie" zawiera linki do zweryfikowanych materiałów z najsłabszych kategorii.

### TC-10 *(FR-05)* — Brak rekomendacji bez słabych obszarów
**Kroki:**
1. Na świeżym koncie (bez diagnostyki) lub po diagnostyce z wynikami ≥ 50% wejdź na panel główny.\
**Oczekiwany rezultat:** Sekcja rekomendacji nie pokazuje materiałów „naprawczych" (jest pusta lub nie występuje) — brak fałszywych rekomendacji.

### TC-11 *(FR-06)* — Symulacja egzaminu zakończona przed czasem
**Kroki:**
1. Wejdź „Egzamin" → rozpocznij symulację.
2. Obserwuj zegar odliczający; odpowiedz na pytania i zakończ przed upływem czasu.\
**Oczekiwany rezultat:** Widoczny licznik czasu; po zakończeniu system pokazuje wynik egzaminu (punkty/procenty per obszar).

### TC-12 *(FR-06)* — Automatyczne zakończenie po upływie czasu
**Kroki:**
1. Rozpocznij egzamin i odczekaj do upłynięcia limitu czasu (dla testu można w panelu bazy skrócić `deadline` trwającego `ExamAttempt` albo zmodyfikować czas trwania w seedzie).
2. Spróbuj wysłać odpowiedź po 0:00.\
**Oczekiwany rezultat:** Po upływie czasu system blokuje przyjmowanie odpowiedzi (kontrola po stronie serwera) i automatycznie zamyka oraz ocenia podejście.

### TC-13 *(FR-07)* — Punkty za aktywność
**Kroki:**
1. Zanotuj stan punktów (strona „Moje statystyki").
2. Ukończ test diagnostyczny lub egzamin.
3. Ponownie sprawdź punkty.\
**Oczekiwany rezultat:** Liczba punktów na profilu wzrosła po ukończonym teście.

### TC-14 *(FR-07)* — Ranking najaktywniejszych
**Kroki:**
1. Zdobądź punkty na 2-3 kontach.
2. Wejdź na stronę „Ranking".\
**Oczekiwany rezultat:** Strona „Najaktywniejsi użytkownicy" pokazuje do 10 osób z najwyższym wynikiem w kolejności malejącej oraz pozycję zalogowanego użytkownika.

## III. Współdzielenie Treści i Moderacja

### TC-15 *(FR-08)* — Dodanie materiału ze statusem „Oczekuje"
**Kroki:**
1. Jako student: Materiały → „Dodaj materiał"; wypełnij tytuł, kategorię, treść; opcjonalnie załącz PDF; zapisz.
2. Otwórz listę materiałów z filtrem „Oczekujące" oraz filtrem „Moje".\
**Oczekiwany rezultat:** Materiał zapisany ze statusem „Oczekuje na weryfikację", widoczny w obu filtrach; trafia do kolejki moderatora.

### TC-16 *(FR-08)* — Walidacja załącznika materiału
**Kroki:**
1. W formularzu dodawania materiału załącz plik > 10 MB lub o niedozwolonym typie (np. `.exe`).\
**Oczekiwany rezultat:** Formularz odrzuca plik z czytelnym komunikatem; materiał nie zostaje zapisany.

### TC-17 *(FR-09)* — Głos podbija priorytet w kolejce moderatora
**Kroki:**
1. Jako studenci A i B zagłosuj na materiał M2 (2 głosy); materiał M1 zostaw bez głosów.
2. Zaloguj się jako moderator → kolejka weryfikacji.\
**Oczekiwany rezultat:** M2 znajduje się w kolejce wyżej niż M1 (sortowanie po priorytecie z głosów).

### TC-18 *(FR-09)* — Idempotentność głosu
**Kroki:**
1. Jako ten sam student kliknij „głosuj" na ten sam materiał dwukrotnie.\
**Oczekiwany rezultat:** Licznik głosów rośnie tylko raz; ponowny głos nie zwiększa priorytetu (przycisk oznaczony jako oddany głos).

### TC-19 *(FR-10)* — Pełny cykl oceny pracy przez moderatora
**Kroki:**
1. Student wysyła pracę (TC-30) — praca w kolejce.
2. Moderator: „Prace do oceny" → Rezerwuj → edytor: zaznacz fragment tekstu (błąd/czerwony), dodaj komentarz do zaznaczenia, ustaw ocenę CEFR, komentarz ogólny → Publikuj.
3. Student otwiera szczegóły pracy.\
**Oczekiwany rezultat:** Student widzi status „Sprawdzone", ocenę, komentarz ogólny i zaznaczenia z komentarzami; dostaje powiadomienie z komentarzem w „Pokaż szczegóły"; może wystawić ocenę 1–5 ★ sprawdzającemu.

### TC-20 *(FR-10)* — Rezerwacja blokuje pracę dla innych
**Kroki:**
1. Moderator A rezerwuje pracę.
2. Moderator B próbuje zarezerwować tę samą pracę.\
**Oczekiwany rezultat:** B dostaje komunikat o niepowodzeniu („ktoś mógł Cię wyprzedzić"); praca pozostaje przypisana do A; zleceniodawca dostał JEDNO powiadomienie o rezerwacji.

## IV. Administracja i Bezpieczeństwo

### TC-21 *(FR-11)* — Blokada użytkownika na 7 dni
**Kroki:**
1. Admin → Użytkownicy → szczegóły studenta → blokada „7 dni" z powodem (≥10 znaków).
2. Zablokowany użytkownik próbuje się zalogować.\
**Oczekiwany rezultat:** Sesje użytkownika unieważnione; przy logowaniu komunikat „konto zablokowane do <data>"; użytkownik dostał powiadomienie z powodem (po odblokowaniu widoczny w „Pokaż szczegóły").

### TC-22 *(FR-11)* — Automatyczne wygaśnięcie blokady czasowej
**Kroki:**
1. Zablokuj konto na 1 dzień, następnie (dla celów testu) ustaw `blockedUntil` w przeszłości (shell/baza) — symulacja upływu terminu.
2. Użytkownik loguje się ponownie.\
**Oczekiwany rezultat:** Logowanie udane — konto automatycznie odblokowane po terminie (status wraca do aktywnego).

### TC-23 *(FR-12)* — Akceptacja wniosku nadaje rolę moderatora
**Kroki:**
1. Student składa wniosek z zaliczonym testem (≥50%).
2. Admin → Wnioski moderatorskie → otwórz → Akceptuj.
3. Kandydat loguje się ponownie.\
**Oczekiwany rezultat:** Kandydat dostał powiadomienie o akceptacji; po zalogowaniu widzi panel „Moderacja"; admin widzi go na liście z rolą Moderator.

### TC-24 *(FR-12)* — Odebranie roli moderatora
**Kroki:**
1. Admin → Użytkownicy → filtr „Moderatorzy" → przy moderatorze kliknij „Zabierz moderatora".\
**Oczekiwany rezultat:** Użytkownik wraca do roli Student (znika z filtra moderatorów), dostaje powiadomienie o cofnięciu uprawnień; traci dostęp do panelu Moderacja.

### TC-25 *(FR-12)* — Automatyczne odrzucenie wniosku przy wyniku < 50%
**Kroki:**
1. Student składa wniosek, celowo odpowiadając błędnie w teście kwalifikacyjnym.
2. Sprawdź powiadomienia studenta oraz (jako admin) licznik i listę wniosków.\
**Oczekiwany rezultat:** Wniosek odrzucony automatycznie z podanym wynikiem; kandydat powiadomiony; wniosek NIE pojawia się w kolejce admina ani w liczniku oczekujących.

### TC-26 *(FR-13)* — Zgłoszenie materiału trafia do admina
**Kroki:**
1. Student otwiera materiał → „Zgłoś błąd / spam" → wypełnia powód → wysyła.
2. Admin otwiera dashboard i kolejkę zgłoszeń.\
**Oczekiwany rezultat:** Licznik zgłoszeń na dashboardzie wzrósł; zgłoszenie widoczne w kolejce z powodem, podglądem materiału i linkiem do profilu autora.

### TC-27 *(FR-13)* — Uznanie zgłoszenia usuwa materiał
**Kroki:**
1. Admin otwiera zgłoszenie → decyzja „zasadne" (RESOLVED) z komentarzem.
2. Sprawdź listę materiałów oraz powiadomienia autora i zgłaszającego.\
**Oczekiwany rezultat:** Materiał usunięty z aplikacji; autor dostał powiadomienie o usunięciu (komentarz w „Pokaż szczegóły"); zgłaszający — o uznaniu zgłoszenia.

## V. Monetyzacja i Premium

### TC-28 *(FR-14)* — Panel zarobków sprawdzającego
**Kroki:**
1. Moderator publikuje ocenę pracy z pakietu 25 zł (TC-19).
2. Wejdź Moderacja → Zarobki.\
**Oczekiwany rezultat:** Panel pokazuje liczbę sprawdzonych prac i sumę zarobków równą pełnej cenie pakietu (25,0 zł — bez marży platformy); brak przycisków wypłaty/faktur (rozliczenie poza platformą — patrz nota N-2).

### TC-29 *(FR-14)* — Zarobek widoczny przy doborze pracy
**Kroki:**
1. W kolejce „Prace do oceny" obejrzyj wiersz pracy z pakietu 25 zł.\
**Oczekiwany rezultat:** Kolumna „Zarobek" pokazuje 25,0 zł przy tej pracy — moderator przed rezerwacją wie, ile zarobi.

### TC-30 *(FR-15)* — Zgłoszenie pracy przez rozliczenie indywidualne
**Kroki:**
1. Student: Moje prace → Nowa praca → treść + pakiet → dalej.
2. Na ekranie rozliczenia wybierz „Rozliczenie indywidualne" i zatwierdź.
3. Zaloguj się jako moderator i sprawdź kolejkę prac.\
**Oczekiwany rezultat:** Praca pojawia się w kolejce moderatora dopiero po zatwierdzeniu rozliczenia (wcześniej status „oczekuje na rozliczenie"); student widzi komunikat o dalszych krokach.

### TC-31 *(FR-15)* — Bramki płatności niedostępne
**Kroki:**
1. Na ekranie rozliczenia obejrzyj opcje BLIK / karta / przelew.
2. Spróbuj wysłać żądanie z metodą `BLIK` (np. przez narzędzia deweloperskie przeglądarki).\
**Oczekiwany rezultat:** Opcje bramek są wyszarzone, nieklikalne, z etykietą „niedostępne"; wymuszone żądanie z metodą bramki jest odrzucane po stronie serwera z komunikatem, a praca nie zmienia statusu.

### TC-32 *(FR-15)* — Powiadomienie o rezerwacji z kontaktem
**Kroki:**
1. Po TC-30 moderator rezerwuje pracę.
2. Student otwiera powiadomienia; moderator otwiera edytor pracy.\
**Oczekiwany rezultat:** Student dostał powiadomienie z imieniem i adresem e-mail sprawdzającego (szczegóły płatności w „Pokaż szczegóły"); moderator widzi w edytorze wiersz „Zleceniodawca (kontakt ws. płatności): <e-mail>".

---

## Nota: świadome odstępstwa od pierwotnych wymagań

* **N-1 (FR-01):** zamiast linku aktywacyjnego system wysyła **kod weryfikacyjny** wpisywany na stronie — funkcjonalnie równoważne (konto nieaktywne do potwierdzenia adresu).
* **N-2 (FR-14):** decyzją zespołu panel finansowy pokazuje wyłącznie **statystyki zarobków** (pełna cena pakietu, bez marży); zlecanie wypłat i faktury wyłączone — rozliczenia odbywają się poza platformą.
* **N-3 (FR-15):** decyzją zespołu integrację z bramką płatności zastąpiono **rozliczeniem indywidualnym** (kontakt zleceniodawca ↔ sprawdzający); kryterium „praca u moderatora dopiero po opłaceniu" pozostaje spełnione — praca trafia do kolejki dopiero po zatwierdzeniu rozliczenia.
Testy TC-28…TC-32 weryfikują aktualną, obowiązującą wersję wymagań.
