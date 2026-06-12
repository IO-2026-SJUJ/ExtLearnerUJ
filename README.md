# ExtLearnerUJ

Otwartoźródłowa platforma webowa przygotowująca studentów Uniwersytetu
Jagiellońskiego do egzaminu eksternistycznego **B2+ z języka angielskiego**.
Projekt zrealizowany w ramach laboratorium *Inżynieria oprogramowania*
(semestr letni 2025/2026) przez zespół **SJUJ**.

## Co potrafi aplikacja

Student rejestruje się (z weryfikacją adresu e-mail), rozwiązuje **test
diagnostyczny** z raportem procentowym per obszar językowy i dostaje
**rekomendacje materiałów** dopasowane do najsłabszych wyników. Może ćwiczyć
na **symulacji egzaminu z twardym limitem czasu** (deadline pilnowany po
stronie serwera, autozapis odpowiedzi), zbierać punkty i porównywać się
w rankingu najaktywniejszych. Społeczność **dodaje własne materiały**, głosuje
na oczekujące pozycje i zgłasza nadużycia; nad jakością czuwają
**moderatorzy** (rekrutowani przez wniosek z testem kwalifikacyjnym —
wynik poniżej 50% odrzuca wniosek automatycznie), którzy weryfikują materiały
oraz **oceniają prace pisemne** w interaktywnym edytorze z kolorowym
zaznaczaniem błędów i oceną CEFR. Rozliczenie za sprawdzenie pracy odbywa się
**indywidualnie** między zleceniodawcą a sprawdzającym (platforma nie pobiera
marży), a student po otrzymaniu oceny może wystawić sprawdzającemu **ocenę
1–5 ★**. Administrator zarządza zgłoszeniami, wnioskami, rolami i blokadami
kont; użytkownik w każdej chwili może **trwale usunąć konto wraz ze wszystkimi
danymi** (RODO). Powiadomienia z sekcją „Pokaż szczegóły" spinają całość.

## Stack technologiczny

Python 3.11+ · Django 5 · SQLite (dev) · własna warstwa sesji i ról
(multi-table inheritance) · Argon2 (hashowanie haseł) · czysty JS bez
frameworków (timer egzaminu, autozapis, edytor zaznaczeń) · testy: Django
TestCase (**247 testów**).

## Struktura repozytorium

```
README.md            <- ten plik
docs/zadanie1..8/    <- dokumentacja projektu
src/                 <- kod źródłowy aplikacji
tests/               <- testy jednostkowe fazy RED
```

Właściwe testy aplikacji rozwijane w sprintach znajdują się — zgodnie
z konwencją Django — w `src/ExtLearnerUJ/tests/`.

## Instalacja i uruchomienie

Wymagania: Python 3.11+, pip, Git.

```bash
git clone https://github.com/<organizacja>/<repozytorium>.git
cd <repozytorium>

# 1. Środowisko wirtualne
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# 2. Zależności
pip install -r src/requirements.txt

# 3. Konfiguracja (defaulty wystarczają do dev)
cd src
copy .env.example .env        # Windows;  cp na Linux/macOS

# 4. Baza + dane startowe
python manage.py migrate
python manage.py seed_diagnostic
python manage.py seed_materials
python manage.py seed_packages
python manage.py seed_exam
python manage.py seed_admin

# 5. Start
python manage.py runserver
```

Aplikacja działa pod `http://127.0.0.1:8000/`.

**Konto startowe administratora:** `admin@uj.edu.pl` / `AdminHaslo123`
(zmień hasło po pierwszym logowaniu — funkcja „Nie pamiętam hasła").
Konta studenckie zakładasz przez rejestrację w aplikacji.

### Wysyłka e-maili

Bez konfiguracji SMTP kody weryfikacyjne i linki resetu hasła wypisują się
w konsoli, w której działa `runserver` (wygodne w dev). Aby wysyłać prawdziwe
maile, uzupełnij w `src/.env` zmienne `EMAIL_HOST`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD` itd. — wzór i opis w `src/.env.example` (dla Gmaila
wymagane jest hasło aplikacji, nie zwykłe hasło). Plik `.env` zawiera dane
dostępowe i **nie może trafić do repozytorium**.

## Jak uruchomić testy

```bash
cd src
python manage.py test ExtLearnerUJ.tests
```

Zestaw obejmuje 247 testów jednostkowych i integracyjnych (auth, diagnostyka,
materiały, moderacja, prace, egzamin, panel admina, RODO). Raport pokrycia:

```bash
coverage run manage.py test ExtLearnerUJ.tests && coverage report
```

## Zespół

**SJUJ** — Julia Łapiuk (frontend, UX, komponenty JS) · Seweryn Olejnik
(backend, modele danych, testy).