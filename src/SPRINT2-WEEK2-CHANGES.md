# Sprint 2 · Tydzień 2 — co się zmieniło

Drugi tydzień Sprintu 2. Zamyka sprint dowiezieniem wszystkich pozostałych
Must have z zakresu ekosystemu treści, moderacji i monetyzacji.

## Nowe funkcjonalności

### Prace pisemne — flow pełny (FR-15, UC19, UC20, UC21)
- Student wysyła pracę (tekst lub załączony PDF/DOCX/TXT)
- 3 pakiety cenowe: Podstawowy 15zł · Rozszerzony 25zł · Ekspresowy 40zł
- Mockowana bramka płatności (BLIK / karta / przelew) — w demo zawsze sukces
- Lista moich prac z kolorowym statusem (oczekuje → opłacone → sprawdzane → gotowe)

### Edytor oceny moderatora (FR-10, UC38–UC42)
- Kolejka prac posortowana po dacie zgłoszenia
- Rezerwacja pracy (idempotentna — drugi moderator dostaje błąd)
- **Interaktywny edytor z kolorowym zaznaczaniem:**
  - Czerwone — błędy gramatyczne
  - Żółte — nienaturalne sformułowania
  - Zielone — pochwały
- Zaznaczanie działa przez zwykłe zaznaczenie myszą w tekście + wybór koloru
- Przy dodaniu zaznaczenia prompt o opcjonalny komentarz
- Pole ocen CEFR (A1–C2) + komentarz ogólny
- Zapis szkicu (w dowolnym momencie) lub publikacja (wysyła notyfikację studentowi)

### Panel admina (FR-11, UC46, UC47, UC48)
- Dashboard z 7 metrykami (userzy, studenci, moderatorzy, materiały pending/zweryfikowane, otwarte zgłoszenia, prace w trakcie)
- Rozpatrywanie zgłoszeń — uznaj za zasadne / odrzuć, zgłaszający dostaje notyfikację o decyzji
- Lista wszystkich userów ze statusami
- Szczegóły konta: historia (materiały, zgłoszenia wysłane, zgłoszenia przeciw), blokada na 1/7/30 dni lub permanent, odblokowanie
- Blokada powoduje: unieważnienie wszystkich sesji usera + notyfikację do niego

### Drobne poprawki
- Stopka bez "Sprint 1"
- Context processor `media` w settings — linki do plików działają
- Kliknięcie w pliku w szczegółach materiału otwiera go w nowej karcie
- Dashboard ma aktywne linki zamiast skreślonych TODO
- Po złożeniu zgłoszenia user dostaje notyfikację potwierdzającą
- Link "Administracja" w navbarze dla adminów

## Setup

### Jeśli kontynuujesz ze Sprintu 2/w1:

```bash
source venv/bin/activate
python manage.py migrate          # migracja 0003_sprint2_week2
python manage.py seed_packages    # 3 pakiety cenowe
```

### Jak przetestować panel admina

Admin nie rejestruje się przez formularz — tworzy go admin bazy danych albo
skrypt inicjalizacyjny. Do testów:

```bash
python manage.py shell
```

```python
from ExtLearnerUJ.models import Admin, User
from django.contrib.auth.hashers import make_password

Admin.objects.create(
    email='admin@uj.edu.pl',
    password=make_password('AdminHaslo123'),
    name='Maria Admin',
    status=User.STATUS_ACTIVE,
    emailVerified=True,
)
```

Logujesz się jako `admin@uj.edu.pl` / `AdminHaslo123`, w navbarze widzisz link **Administracja**.

### Jak przetestować flow prac pisemnych

1. Zaloguj się jako student
2. **Moje prace** → **+ Wyślij nową pracę**
3. Wybierz pakiet, napisz tytuł, wklej treść (albo załącz plik)
4. **Przejdź do płatności →**
5. Wybierz metodę, kliknij **Zapłać**
6. Praca jest widoczna w **Moich pracach** jako "W kolejce"

Potem jako moderator:

1. Zaloguj się jako moderator
2. **Moderacja** → (w panelu dashboard jest link **Prace do sprawdzenia** lub `/moderator/works/`)
3. Kliknij **Zarezerwuj** przy pracy
4. W edytorze:
   - Zaznacz fragment tekstu myszą
   - Kliknij jeden z 3 kolorów po prawej
   - Wpisz komentarz w prompcie (lub pomiń przez Cancel)
5. Wypełnij ocenę CEFR i komentarz ogólny
6. **Opublikuj ocenę**

Student w **Moich pracach** widzi teraz status "Gotowe" i po kliknięciu — pełny feedback.

### Jak przetestować panel admina

Zarejestruj konto studenta, zaloguj się, zgłoś jakiś materiał
(`materials/<id>/report/`).

Teraz jako admin:
1. **Administracja** → dashboard
2. **Zgłoszenia** → klik na zgłoszenie
3. Wybierz "Uznaj za zasadne" lub "Odrzuć"
4. Student dostaje notyfikację o decyzji

Blokada usera:
1. **Administracja** → **Użytkownicy**
2. Klik na dowolnego usera → **Szczegóły**
3. Wypełnij formularz blokady po prawej, zapisz
4. User zostaje natychmiast wylogowany i nie może się zalogować

## Testy

```bash
python manage.py test ExtLearnerUJ.tests -v 2
```

Nowy plik `test_sprint2_week2.py` (~40 testów) + wszystkie poprzednie.
Łącznie powinno być **ok. 130 testów na zielono**.

Pokrycie coverage:

```bash
coverage run --source=ExtLearnerUJ manage.py test ExtLearnerUJ.tests
coverage report -m
```

Cel: ≥70%, obecnie ok. 85–90% (dzięki szerokim testom integracyjnym).

## Koniec Sprintu 2

Po tym tygodniu aplikacja jest **funkcjonalnie kompletna w warstwie Must have**:
- FR-01 ... FR-04, FR-06, FR-08, FR-09, FR-10, FR-11, FR-13, FR-15 — wszystkie zaimplementowane
- Brakuje tylko Should/Could have, które przechodzą do Sprintu 3

Co dalej w Sprincie 3:
- FR-05 (rekomendacje materiałów po wynikach testu)
- FR-06 rozbudowa (symulacja egzaminu z twardym timerem)
- FR-07 (ranking, gamifikacja)
- FR-12 (admin przyznaje rolę moderatora + formularz aplikacji)
- FR-14 (wypłaty moderatorów z fakturami)
- UC15 (generowanie raportu PDF z okresu nauki)
- Testy obciążeniowe (NFR-08)
- Beta testy ze znajomymi (R7.1)
- Dokumentacja końcowa i prezentacja
