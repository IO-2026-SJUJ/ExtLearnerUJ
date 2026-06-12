# Raport z Artefaktów oraz Analiza Retrospektywna — Sprint 3

**Projekt:** ExtLearnerUJ — Platforma przygotowująca studentów UJ do egzaminu eksternistycznego B2+ z języka angielskiego
**Zespół:** SJUJ (Julia Łapiuk, Seweryn Olejnik)

---

## 1. Wykaz zrealizowanych zadań i podział prac (Artefakty)

W Sprincie 3 domknęliśmy backlog funkcjonalny projektu oraz przeprowadziliśmy dwie tury poprawek po testach manualnych: realna wysyłka e-maili, reset hasła, ujednolicenie uprawnień ról, RODO, test kwalifikacyjny dla kandydatów na moderatorów, rozliczenie indywidualne prac i oceny sprawdzających. Podział ról bez zmian: Julia Łapiuk — warstwa prezentacji, JS i UX, Seweryn Olejnik — logika biznesowa, modele i testy. Zadania na styku warstw (symulacja egzaminu) realizowaliśmy wspólnie.

| Identyfikator zadania / Wymaganie | Opis i zakres prac | Główny wykonawca | Wsparcie | Czas (J. Łapiuk) | Czas (S. Olejnik) | Czas całkowity | Lokalizacja artefaktu w repozytorium |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **TSK-23**<br>*(FR-05)* | **Rekomendacje materiałów**<br>`RecommendationService` proponujący materiały z obszarów, w których diagnostyka dała wynik < 50%; sekcja na panelu głównym. | S. Olejnik | J. Łapiuk | 1 h | 2 h | **3 h** | `ExtLearnerUJ/services.py`<br>`ExtLearnerUJ/templates/.../dashboard.html` |
| **TSK-24**<br>*(FR-06, NFR-02)* | **Symulacja egzaminu z timerem**<br>Model `ExamAttempt` z deadlinem egzekwowanym serwerowo, odliczanie i autozapis odpowiedzi po stronie klienta, automatyczne zakończenie po czasie. | wspólnie | — | 2 h | 2 h | **4 h** | `ExtLearnerUJ/models.py`<br>`ExtLearnerUJ/static/js/exam.js` |
| **TSK-25**<br>*(FR-07, UC15)* | **Ranking, statystyki i raport PDF**<br>Punktacja (`UserStats`), strona „Najaktywniejsi użytkownicy", strona „Moje statystyki" z wykresami per obszar oraz generator raportu PDF w czystym Pythonie. | S. Olejnik | J. Łapiuk | 2 h | 2 h | **4 h** | `ExtLearnerUJ/services.py`<br>`ExtLearnerUJ/templates/.../stats/` |
| **TSK-26**<br>*(FR-12, FR-02)* | **Wnioski moderatorskie z testem kwalifikacyjnym**<br>Wniosek (motywacja + certyfikat) z testem z angielskiego ocenianym serwerowo: wynik < 50% odrzuca automatycznie (bez angażowania admina), wynik ≥ 50% trafia do kolejki admina wraz z wynikiem. | S. Olejnik | J. Łapiuk | 1 h | 3 h | **4 h** | `ExtLearnerUJ/moderator_test.py`<br>`ExtLearnerUJ/templates/.../admin_panel/` |
| **TSK-27**<br>*(FR-01)* | **Realne maile i reset hasła**<br>SMTP konfigurowany przez zmienne środowiskowe (fallback konsolowy w dev), przepływ „Nie pamiętam hasła" z tokenem 1 h, ponowne wysłanie kodu weryfikacyjnego. | S. Olejnik | J. Łapiuk | 1 h | 3 h | **4 h** | `config/settings.py`<br>`ExtLearnerUJ/templates/.../auth/` |
| **TSK-28** | **Ujednolicenie ról i przebudowa UI**<br>Moderator i admin mają pełny zestaw funkcji studenta (metody na klasie bazowej `User`), przebudowa panelu Moderacja, „Odczytaj wszystkie" w powiadomieniach, naprawa konfliktów merge po Sprincie 2. | J. Łapiuk | S. Olejnik | 4 h | 1 h | **5 h** | `ExtLearnerUJ/models.py`<br>`ExtLearnerUJ/templates/.../moderator/dashboard.html` |
| **TSK-29**<br>*(FR-11)* | **Rozszerzenia panelu administratora**<br>Filtr ról + odbieranie moderatora z listy, blokady z datą końca i auto-odblokowaniem, usuwanie materiałów (admin/autor, filtr „Moje"), usunięcie materiału po uznaniu zgłoszenia + link do autora. | S. Olejnik | J. Łapiuk | 1 h | 3 h | **4 h** | `ExtLearnerUJ/views.py`<br>`ExtLearnerUJ/templates/.../admin_panel/` |
| **TSK-30**<br>*(FR-03, RODO O-01)* | **Usuwanie konta wraz z danymi**<br>Transakcyjne usunięcie wszystkich danych użytkownika z potwierdzeniem hasłem; prace oceniane przez usuwanego sprawdzającego wracają do kolejki. | S. Olejnik | J. Łapiuk | 1 h | 1 h | **2 h** | `ExtLearnerUJ/models.py`<br>`ExtLearnerUJ/templates/.../auth/delete_account.html` |
| **TSK-31**<br>*(FR-15)* | **Rozliczenie indywidualne prac**<br>Bramki płatności wyłączone (oznaczone „niedostępne"), w zamian rozliczenie bezpośrednie ze sprawdzającym: rezerwacja blokuje pracę, zleceniodawca dostaje powiadomienie z kontaktem, kolumna „Zarobek" w kolejce. | S. Olejnik | J. Łapiuk | 2 h | 3 h | **5 h** | `ExtLearnerUJ/templates/.../works/payment.html`<br>`ExtLearnerUJ/templates/.../moderator/works_queue.html` |
| **TSK-32**<br>*(FR-14)* | **Oceny sprawdzających i panel zarobków**<br>Ocena 1–5 ★ po otrzymaniu sprawdzonej pracy (jedna na pracę), średnia widoczna dla admina; panel zarobków pokazuje statystyki liczone jako pełna cena pakietu (bez marży). | S. Olejnik | J. Łapiuk | 1 h | 3 h | **4 h** | `ExtLearnerUJ/models.py` (`ModeratorRating`)<br>`ExtLearnerUJ/templates/.../moderator/earnings.html` |
| **TSK-33**<br>*(UC32)* | **Powiadomienia „Pokaż szczegóły"**<br>Rozwijane szczegóły z pełnym komentarzem decyzji (weryfikacje, oceny, zgłoszenia, wnioski, blokady); rozszerzenie typów plików prac (PDF/DOC/DOCX/TXT/JPG/PNG). | J. Łapiuk | S. Olejnik | 2 h | 1 h | **3 h** | `ExtLearnerUJ/templates/.../notifications/list.html`<br>`ExtLearnerUJ/forms.py` |
| **TSK-34**<br>*(NFR-08, R6.3)* | **Dane startowe**<br>Seedy: `seed_exam`, `seed_admin`; usunięcie konta testowego z danych przykładowych. | S. Olejnik | — | 0 h | 1 h | **1 h** | `ExtLearnerUJ/management/commands/` |
| **TSK-35** | **Testowanie**<br>Rozbudowa zestawu do 247 testów (nowe moduły + obie tury poprawek), w tym testy regresyjne. | S. Olejnik | — | 0 h | 3 h | **3 h** | `ExtLearnerUJ/tests/test_sprint3*.py` |
| **TSK-36** | **Dokumentacja projektu na Github**<br>Aaktualizacja README i generealne utrzymanie na GitHubie. | wspólnie | — | 1 h | 1 h | **2 h** | `src/SPRINT3-CHANGES.md`<br>(dosc/zadanie6) |
| **PODSUMOWANIE** | **Łączny wkład czasowy zespołu (SJUJ)** | | | **18 h** | **28 h** | **47 h** | |

---

## 2. Wnioski z retrospektywy (Podsumowanie fazy)

### 2.1. Co poszło dobrze
* **Regularne commity — do trzech razy sztuka zadziałało XD** — sztywny, dzienny harmonogram commitów z przypisanymi zadaniami zmusił nas do systematyczności; zmiany szły na Githuba małymi porcjami przez cały sprint.
* **E-mail dowieziony** — SMTP wszedł na początku sprintu zgodnie z planem i rozwiązał bolączkę testowania manualnego z poprzednich iteracji.
* **Cały backlog + dwie tury poprawek** — wszystkie wymagania funkcjonalne zaimplementowane, poprawki z testów manualnych podniosły spójność aplikacji, całość pokryta 247 testami.

### 2.2. Co można poprawić
* **Konfiguracja usług zewnętrznych na ostatnią chwilę** — pierwotny plan (Outlook) okazał się niewykonalny, bo Microsoft wyłączył logowanie hasłem dla SMTP; przesiadka na Gmaila z hasłem aplikacji kosztowała czas.
* **Zmiany koncepcji w trakcie sprintu** — rezygnacja z bramek płatności na rzecz rozliczenia indywidualnego i zerowa marża wymagały przeróbek gotowego kodu i testów.

### 2.3. Wnioski na zakończenie projektu
* **Decyzje produktowe przed kodowaniem** — większe zmiany koncepcji (model rozliczeń, marża) ustalamy zanim zaczniemy implementację.
* **Założenia integracyjne sprawdzać na starcie** — ograniczenia usług zewnętrznych (poczta, płatności) weryfikujemy na początku iteracji, nie przy wdrażaniu.
* **Dokumentacja końcowa i prezentacja** — pozostałe zadania są nietechniczne: dokumentacja końcowa i prezentacja projektu.
* **Higiena repozytorium** — `.env` z danymi dostępowymi poza repo, rotacja haseł po obronie, usunięcie plików tymczasowych.
