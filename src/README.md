# ExtLearnerUJ

Platforma przygotowująca studentów UJ do egzaminu eksternistycznego B2+
z języka angielskiego. Projekt realizowany w ramach laboratorium Inżynierii
Oprogramowania — zespół **SJUJ** (Julia Łapiuk, Seweryn Olejnik).

## Stan — Sprint 1

Zaimplementowany rdzeń aplikacji:

- rejestracja studenta z weryfikacją e-mail (UC01, UC02, FR-01)
- logowanie i zarządzanie sesją przez własny middleware (UC03)
- usuwanie konta (FR-03, RODO O-01)
- test diagnostyczny z automatycznym ocenianiem per obszar (UC04, UC05, FR-04)
- lista materiałów z filtrami i szczegółowym widokiem (UC07, UC09)
- autozapis postępów testu (NFR-02)
- hashowanie Argon2 (NFR-03)
- wysoki kontrast i typografia serwowa (NFR-04)

Sprinty 2 i 3 dołożą: głosowanie, dodawanie materiałów, moderację, płatności,
panel admina, rekomendacje, ranking, raporty PDF.

## Uruchomienie lokalne

Wymagania: Python 3.11+, pip.

```bash
# 1. Klonowanie i środowisko
git clone <repo-url> extlearner-uj
cd extlearner-uj
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# 2. Zależności
pip install -r requirements.txt

# 3. Konfiguracja
cp .env.example .env
# (plik .env.example ma sensowne defaulty dla dev — można zostawić jak jest)

# 4. Baza + seedy
python manage.py migrate
python manage.py seed_diagnostic   # tworzy test diagnostyczny (20 pytań)
python manage.py seed_materials    # kilka przykładowych materiałów

# 5. Uruchomienie
python manage.py runserver
```

Aplikacja jest dostępna pod [http://localhost:8000](http://localhost:8000).

### Uwagi dev-only

- **Wiadomości e-mail** nie są wysyłane na zewnątrz — zapisują się w pamięci
  (`locmem.EmailBackend`). W dev przy rejestracji zajrzyj do konsoli testów
  lub odczytaj kod bezpośrednio z bazy w Django shellu:
  ```bash
  python manage.py shell
  >>> from ExtLearnerUJ.models import EmailVerificationToken
  >>> EmailVerificationToken.objects.last().token
  ```
- `/admin/` (Django admin) jest dostępne dla superuserów — tworzysz osobno
  przez `python manage.py createsuperuser`. **Superuser Django to inna tabela
  niż nasz `User`** — celowo, Sprint 3 ma własny panel admina aplikacji.

## Testy

```bash
# Wszystkie testy
python manage.py test ExtLearnerUJ.tests -v 2

# Z raportem pokrycia (wymaga coverage, jest w requirements.txt)
coverage run --source=ExtLearnerUJ manage.py test ExtLearnerUJ.tests
coverage report -m
coverage html   # generuje htmlcov/ z raportem do przeglądania w przeglądarce
```

Cel Sprintu 1: **≥70% pokrycia** w modułach `models`, `services`,
`middleware`, `views` (DŁ dla ryzyka R5.1).

## Struktura projektu

```
extlearner-uj/
├── manage.py                    # entry point Django
├── requirements.txt             # zależności
├── .env.example                 # szablon zmiennych środowiskowych
├── .gitignore
├── README.md
│
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions — testy na każdy PR
│
├── config/                      # pakiet konfiguracyjny projektu Django
│   ├── __init__.py
│   ├── settings.py              # konfiguracja (czyta z .env)
│   ├── urls.py                  # router główny
│   ├── wsgi.py                  # entry produkcyjny
│   └── asgi.py                  # entry ASGI (przyszłościowe)
│
├── ExtLearnerUJ/                # właściwa aplikacja
│   ├── __init__.py
│   ├── apps.py                  # konfiguracja aplikacji
│   ├── admin.py                 # (Sprint 3 — własny panel)
│   │
│   ├── models.py                # User, Student, Session, Material, Test, ...
│   ├── services.py              # GradingService (Strategy), stuby pod S2/S3
│   ├── middleware.py            # SessionAuthMiddleware (nasza auth, nie Django)
│   ├── decorators.py            # session_login_required, role_required
│   ├── context_processors.py    # udostępnia app_user szablonom
│   ├── forms.py                 # RegisterForm, LoginForm, VerifyEmailForm
│   ├── views.py                 # wszystkie widoki Sprintu 1
│   ├── urls.py                  # routing aplikacji
│   │
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py      # migracja spójna z models.py
│   │
│   ├── management/commands/
│   │   ├── __init__.py
│   │   ├── seed_diagnostic.py   # → python manage.py seed_diagnostic
│   │   ├── seed_materials.py    # → python manage.py seed_materials
│   │   └── cleanup_sessions.py  # cron: usuwa wygasłe sesje
│   │
│   ├── templates/ExtLearnerUJ/
│   │   ├── base.html            # główny layout
│   │   ├── landing.html         # strona powitalna
│   │   ├── dashboard.html       # panel użytkownika
│   │   ├── _form_field.html     # partial: pole formularza
│   │   ├── auth/
│   │   │   ├── register.html
│   │   │   ├── verify_email.html
│   │   │   └── login.html
│   │   ├── diagnostic/
│   │   │   ├── start.html       # intro do testu
│   │   │   ├── test.html        # właściwy test (z autozapisem)
│   │   │   └── result.html      # wyniki + wykres obszarów
│   │   └── materials/
│   │       ├── list.html        # lista z filtrami
│   │       └── detail.html      # szczegóły materiału
│   │
│   ├── static/
│   │   ├── css/
│   │   │   ├── tokens.css       # design tokens (kolory, fonty, odstępy)
│   │   │   └── base.css         # komponenty, layout, animacje
│   │   ├── js/
│   │   │   ├── diagnostic.js    # autozapis testu (NFR-02)
│   │   │   └── area-chart.js    # animowane słupki wyników
│   │   └── img/                 # (pusty; logotypy itp. w przyszłości)
│   │
│   ├── fixtures/                # (pusty; seedy robimy przez management commands)
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_auth.py         # User, Session, middleware, dekoratory, flow E2E
│       ├── test_diagnostic.py   # GradingService, Test, DiagnosticResult
│       └── test_materials.py    # widoki listy i szczegółów
│
└── media/                       # uploady użytkowników (gitignorowany)
```

## Architektura autentykacji

Nie używamy Django auth framework — mamy własny model `User` z rolami
`Student`/`Moderator`/`Admin` (multi-table inheritance, zgodnie z `classDiagram.md`
i zasadą LSP z `opis.md`).

Flow:

1. `POST /login/` → `User.authenticate()` sprawdza dane, tworzy `Session`
   z losowym UUID tokenem.
2. Widok ustawia ciasteczko `session_token` (HttpOnly, SameSite=Lax).
3. `SessionAuthMiddleware` na każdym request czyta ciasteczko, sprawdza
   `Session` w bazie, ustawia `request.app_user`. Odświeża wygaśnięcie
   jeśli zostało <1h.
4. Dekoratory `@session_login_required` i `@role_required(Student)`
   chronią widoki.

**Dlaczego nie AbstractUser Django?** Bo `classDiagram.md` jest
autorytatywny, macie już działający `User.register()`/`login()` pod ten
kontrakt, a AbstractUser wymusza pole `username` którego nie chcemy. Przy
skali 100–150 userów custom middleware to ~40 linii kodu.

## Mapowanie na wymagania (Sprint 1)

| Wymaganie        | Gdzie zaimplementowane                                           |
|------------------|------------------------------------------------------------------|
| FR-01 (rejestracja)    | `User.register()`, `views.register_view`, `forms.RegisterForm` |
| FR-03 (usuwanie konta) | `User.deleteAccount()` — kaskada Session + tokeny              |
| FR-04 (test diagnostyczny) | `DiagnosticTest`, `views.diagnostic_test`                  |
| UC02 (weryfikacja email)   | `User.verifyEmail()`, `views.verify_email_view`            |
| UC05 (ocenianie per obszar)| `DiagnosticTest.calculateAreaScores()`, `GradingService`   |
| NFR-02 (autozapis)         | `views.diagnostic_autosave` + `static/js/diagnostic.js`    |
| NFR-03 (Argon2, SSL)       | `settings.PASSWORD_HASHERS`, `SECURE_COOKIES`              |
| NFR-04 (kontrast)          | `static/css/tokens.css` — WCAG AA                          |
| R5.1 (testy jednostkowe)   | 3 pliki testowe, cel ≥70% pokrycia                         |
| R6.3 (brak materiałów)     | `seed_diagnostic` + `seed_materials` z przykładami         |

## Co dalej

Po Sprincie 1:

- **Sprint 2** — dodawanie materiałów, głosowanie, moderacja, płatności,
  sprawdzanie prac pisemnych, panel moderatora.
- **Sprint 3** — rekomendacje (FR-05), symulacja egzaminu z timerem (FR-06),
  ranking (FR-07), panel admina z metrykami, raporty PDF, testy
  obciążeniowe (NFR-08), beta testy (R7.1).

## Zespół

**Julia Łapiuk** — Product Owner & Designer (frontend, UX, dokumentacja).
**Seweryn Olejnik** — Tech Lead (backend, architektura, testy).

Model pracy: fullstack team — każda osoba ma główną odpowiedzialność,
ale ruch między warstwami jest dozwolony i zachęcany.
