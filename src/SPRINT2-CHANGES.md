# Sprint 2 · Tydzień 1 — co się zmieniło

Rozbudowa projektu wobec Sprintu 1. Poniżej nowe funkcjonalności i jak
je uruchomić.

## Nowe funkcjonalności

### Dla studenta
- **FR-08** Dodawanie własnych materiałów (tytuł, kategoria, opis, opcjonalny plik PDF/DOCX/TXT/JPG/PNG, max 10 MB).
- **FR-09** Głosowanie na materiały oczekujące weryfikacji — priorytet rośnie, moderator widzi je pierwsze.
- **FR-13** Zgłaszanie materiałów z błędami lub spamu (dropka w szczegółach materiału).
- **UC32** Strona powiadomień z licznikiem nieprzeczytanych w navbarze (ikonka 🔔).

### Dla moderatora
- **UC36** Panel moderatora z kolejką materiałów posortowaną po priorytecie.
- **UC31 + UC33** Widok weryfikacji pojedynczego materiału: pełny tekst + panel decyzji (Zatwierdź / Odrzuć / Wyślij do poprawy + pole komentarza).
- **UC32** Po decyzji moderatora automatycznie tworzona jest notyfikacja dla autora.

### Architektura
- Nowa rola `Moderator` z implementacją metod `viewMaterialsToVerify()`, `verifyMaterial()`.
- Wzbogacony `context_processor` o flagi `is_moderator`, `is_admin`, licznik `unread_notifications` — używany w navbarze.
- Nowy model `Comment` (było w `classDiagram.md`, teraz zaimplementowane).
- `Vote` z `unique_together` — jeden user = jeden głos na materiał.
- Pełna implementacja `User.submitReport()` — wcześniej stub zwracał None.

## Setup — co trzeba zrobić po pobraniu

### Jeśli masz aktywne venv ze Sprintu 1:

```bash
source venv/bin/activate
pip install -r requirements.txt    # bez zmian, ale dla pewności
python manage.py migrate           # zastosuje nową migrację 0002_sprint2
```

Baza danych się nie kasuje — nowa migracja tylko dodaje pola i modele.
Istniejący test diagnostyczny i materiały zostają.

### Jak zobaczyć panel moderatora

Sprint 2 zakłada, że rola `Moderator` jest przyznawana ręcznie przez admina —
pełny flow aplikacji moderatorskiej i oceny przez admina jest w Sprincie 3.
Na razie do testów tworzymy moderatora bezpośrednio w shellu:

```bash
python manage.py shell
```

```python
from ExtLearnerUJ.models import Moderator, User
from django.contrib.auth.hashers import make_password

# Utwórz moderatora testowego
mod = Moderator.objects.create(
    email='moderator@uj.edu.pl',
    password=make_password('TestoweHaslo123'),
    name='Jan Moderator',
    status=User.STATUS_ACTIVE,
    emailVerified=True,
)
```

Teraz wylogowujesz się ze zwykłego konta i logujesz jako
`moderator@uj.edu.pl` / `TestoweHaslo123`. W navbarze zobaczysz link **Moderacja**.

### Testowy scenariusz end-to-end

1. Zaloguj się jako student.
2. Przejdź do **Materiały** → kliknij **+ Dodaj materiał**.
3. Wypełnij formularz, kliknij "Wyślij do weryfikacji".
4. Na liście widzisz swój materiał z chipem **⏳ Oczekuje**.
5. Wyloguj się, zaloguj jako moderator.
6. Kliknij **Moderacja** w navbarze → **Otwórz kolejkę**.
7. Wybierz materiał, zaznacz "Zaakceptuj", zapisz decyzję.
8. Wyloguj, zaloguj ponownie jako student.
9. Zobacz ikonkę 🔔 z licznikiem — kliknij, zobacz powiadomienie.
10. Wróć na listę materiałów — Twój materiał ma teraz chip **✓ Zweryfikowany**.

Głosowanie:
1. Jako student otwórz dowolny materiał **niezweryfikowany**.
2. Kliknij przycisk **👍 Głosuj**.
3. Priorytet w nagłówku rośnie o 1, przycisk się wyszarza.
4. Druga próba nic nie robi — jeden głos per user.

Zgłoszenia:
1. Jako student otwórz dowolny materiał.
2. Kliknij **⚠ Zgłoś błąd / spam**.
3. Wpisz powód (min. 10 znaków), wyślij.
4. W Sprincie 2 (tydzień 2) dojdzie panel admina do rozpatrywania tych zgłoszeń.
   Na razie zgłoszenie ląduje w tabeli `Report` — możesz podejrzeć przez
   `python manage.py shell` → `Report.objects.all()`.

## Testy

```bash
python manage.py test ExtLearnerUJ.tests -v 2
```

Dodany plik `test_sprint2.py` z ~25 testami pokrywającymi wszystkie
nowe funkcjonalności. Łącznie powinno być około **90 testów na zielono**
(66 z Sprintu 1 + nowe z tego tygodnia).

Coverage:

```bash
coverage run --source=ExtLearnerUJ manage.py test ExtLearnerUJ.tests
coverage report -m
```

## Co dalej — tydzień 2 Sprintu 2

- FR-15: wysyłanie prac pisemnych do sprawdzenia (Work, Package, PaymentTransaction z mockowaną płatnością)
- FR-10: edytor moderatora do zaznaczania błędów (kolorowe markery, komentarze per fragment)
- FR-11: panel admina do blokowania userów i rozpatrywania zgłoszeń
