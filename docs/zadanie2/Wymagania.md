# Wymagania

---

## Ograniczenia

#### I. Ograniczenia Prawne i Formalne
* **O-01 (Zgodność z RODO):** System przetwarza dane osobowe (e-mail, imię, nazwisko) oraz dane wrażliwe dotyczące postępów w edukacji. System musi zapewniać:
    * Szyfrowanie danych w spoczynku i podczas transmisji (SSL/TLS).
    * Mechanizmy realizacji "prawa do bycia zapomnianym" (całkowite usuwanie konta).
    * Rejestrowanie zgód marketingowych i akceptacji regulaminu.
    * Ograniczenie przechowywania logów aktywności do niezbędnego minimum.
* **O-02 (Podatki i Finanse):** W przypadku wprowadzenia modelu subskrypcyjnego lub płatności jednorazowych:
    * **VAT:** System musi obsługiwać odpowiednie stawki podatku (np. 23% dla usług elektronicznych w Polsce).
    * **Dokumentacja:** Konieczność automatycznego generowania faktur lub rachunków zgodnych z polskim prawem skarbowym.
    * **Obsługa płatności:** Zależność od zewnętrznych dostawców (np. Przelewy24), co wiąże się z marżami transakcyjnymi oraz koniecznością obsługi zwrotów (chargeback).

#### II. Ograniczenia Merytoryczne (Zgodność z UJ)
* **O-03 (Wymagania Programowe UJ):** Materiały dydaktyczne, arkusze i baza pytań muszą być ściśle dostosowane do wytycznych Uniwersytetu Jagiellońskiego dla egzaminów eksternistycznych. Każda zmiana w sylabusie lub formie egzaminu na uczelni wymusza aktualizację bazy danych systemu.
* **O-04 (Prawa Autorskie):** Zakaz kopiowania i udostępniania chronionych materiałów dydaktycznych (skany podręczników, zastrzeżone zestawy zadań) bez zgody autorów lub jednostek UJ. System musi opierać się na opracowaniach własnych lub materiałach udostępnionych na licencjach otwartych.

#### III. Ograniczenia Operacyjne i Ludzkie
* **O-05 (Zapotrzebowanie na Moderację):** Aby zapewnić wysoką jakość merytoryczną oraz zapobiegać szerzeniu dezinformacji (np. błędnych odpowiedzi w komentarzach lub zadaniach dodawanych przez społeczność), wymagana jest obecność moderatorów (ekspertów przedmiotowych).
    * Szacunkowe zapotrzebowanie: min. 1 moderator na każdą główną dziedzinę egzaminacyjną.
    * Ograniczenie: brak weryfikacji merytorycznej dyskwalifikuje system jako rzetelne źródło nauki.
* **O-06 (Zarządzanie Treścią):** Konieczność stworzenia dedykowanego panelu administracyjnego (Back-office), aby osoby bez wiedzy technicznej (wykładowcy/moderatorzy) mogły zarządzać bazą pytań.

#### IV. Ograniczenia Techniczne
* **O-07 (Dostępność i Skalowalność):** System musi zachować pełną sprawność w okresach "szczytów egzaminacyjnych" (sesje eksternistyczne). Nagły wzrost liczby użytkowników o 500% w ciągu kilku dni nie może doprowadzić do zawieszenia usług.
* **O-08 (Czytelność i Intuicyjność):** Podstawowa użyteczność: czytelne czcionki, wysoki kontrast i intuicyjna nawigacja, która nie wymaga od użytkownika instrukcji obsługi.

---

## Wymagania systemowe

#### I. Dane ilościowe i prognozowane obciążenie
Z uwagi na wąską grupę docelową (jeden poziom egzaminu, jedna uczelnia), system charakteryzuje się niskim, ale bardzo skoncentrowanym w czasie obciążeniem.

| Parametr | Wartość docelowa / Charakterystyka |
| :--- | :--- |
| **Liczba użytkowników** | ok. 100 – 150 osób na semestr (zgodnie z limitami przyjęć na egzaminy). |
| **Ruch szczytowy (Concurrent Users)** | Obsługa do 30-50 jednoczesnych sesji (szczególnie w wieczory poprzedzające egzamin). |
| **Wolumen danych (Baza pytań)** | Specjalistyczna baza ok. 500 – 1000 pytań dedykowanych pod konkretny program UJ. |
| **Częstotliwość operacji** | Skokowa – niska aktywność w trakcie semestru, bardzo wysoka w okresach sesji eksternistycznej. |
| **Zasoby dyskowe** | Niskie zapotrzebowanie (do 2-5 GB), głównie na bazę danych i proste materiały graficzne. |

#### II. Środowisko sprzętowe i programowe

**1. Warstwa serwerowa (Backend):**
* **Hosting:** Darmowe lub niskobudżetowe plany typu „Hobby” (np. Vercel, Render), które są wystarczające przy skali 100 użytkowników.
* **Baza danych:** Zarządzalna baza PostgreSQL (np. na platformie Supabase) z aktywnym szyfrowaniem połączeń.
* **Lokalizacja:** Ze względu na wymogi RODO, dane muszą być przechowywane na serwerach w regionie UE (np. Frankfurt).

**2. Warstwa kliencka (Frontend):**
* **Dostępność:** Aplikacja webowa działająca na komputerach personalnych z przeglądarką.
* **Przeglądarki:** Pełna kompatybilność z przeglądarkami opartymi o Chromium.
* **Wydajność:** Strona ma być responsywna w odczuciu użytkownika, z możliwymi dłuższymi czasami na wygenerowanie statystyk.

#### III. Specyficzne parametry techniczne
* **Bezpieczeństwo danych:** Regularne kopie zapasowe bazy pytań wykonywane raz na dobę.
* **Obsługa sesji:** Mechanizm „pamięci stanu” – jeśli użytkownik odświeży stronę w trakcie testu, system musi przywrócić aktualne pytanie.
---

## Wymagania funkcjonalne

Wymagania funkcjonalne zostały opracowane w formie testowalnych historyjek użytkownika (User Stories) i przypisano im priorytety zgodnie z metodą MoSCoW (Must, Should, Could, Won't).

#### I. Rejestracja i Zarządzanie Kontem
| ID | Historyjka Użytkownika | Priorytet | Kryterium Akceptacji (Test) |
| :--- | :--- | :--- | :--- |
| <nobr>**FR-01**</nobr> | Jako student, chcę zarejestrować się i potwierdzić konto e-mailem, aby moje postępy były zapisywane. | **Must have** | System wysyła link aktywacyjny; konto pozostaje nieaktywne do czasu kliknięcia w link. |
| **FR-02** | Jako kandydat na moderatora, chcę przesłać certyfikat/dyplom podczas rejestracji, aby udowodnić kompetencje. | **Must have** | Formularz rejestracyjny dla moderatora zawiera pole uploadu plików. |
| **FR-03** | Jako użytkownik, chcę mieć dostęp do ustawień prywatności, aby móc usunąć swoje konto i dane. | **Must have** | Przycisk „Usuń konto” w profilu trwale usuwa dane użytkownika z bazy danych. |

#### II. Proces Nauki i Egzaminów
| ID | Historyjka Użytkownika | Priorytet | Kryterium Akceptacji (Test) |
| :--- | :--- | :--- | :--- |
| <nobr>**FR-04**</nobr> | Jako student, chcę przejść test diagnostyczny, aby system ocenił mój poziom (gramatyka, czytanie itp.). | **Must have** | Po ukończeniu testu system wyświetla raport procentowy dla każdej kategorii umiejętności. |
| **FR-05** | Jako student, chcę otrzymywać rekomendacje materiałów na podstawie moich najsłabszych wyników z testu. | **Should have** | Algorytm wyświetla na ekranie głównym linki do lekcji z kategorii, w których wynik był < 50%. |
| **FR-06** | Jako student, chcę rozwiązywać symulacje egzaminu eksternistycznego z limitem czasowym. | **Must have** | Zegar odlicza czas; po 0:00 system automatycznie blokuje możliwość odpowiedzi i wysyła wynik. |
| **FR-07** | Jako student, chcę zdobywać punkty i piąć się w rankingu, aby czuć motywację do regularnej nauki. | **Could have** | Rozwiązany test dodaje punkty do profilu; ranking wyświetla 10 osób z najwyższym wynikiem. |

#### III. Współdzielenie Treści i Moderacja
| ID | Historyjka Użytkownika | Priorytet | Kryterium Akceptacji (Test) |
| :--- | :--- | :--- | :--- |
| <nobr>**FR-08**</nobr> | Jako student, chcę dodać własne materiały, aby podzielić się nimi ze społecznością. | **Must have** | Przycisk „Dodaj materiał” otwiera edytor; materiał otrzymuje status „Oczekuje na weryfikację”. |
| **FR-09** | Jako użytkownik, chcę głosować na niezweryfikowane materiały, aby nadać im priorytet w kolejce moderatora. | **Should have** | Każdy głos „w górę” liczy się przy sortowaniu pozycji danego materiału w panelu moderatora. |
| **FR-10** | Jako moderator, chcę oceniać i poprawiać prace pisemne przesłane przez studentów. | **Must have** | Moderator może wstawiać komentarze, zaznaczać błędy i poprawiać odpowiedzi w przesłanym materiale studenta. |

#### IV. Administracja i Bezpieczeństwo
| ID | Historyjka Użytkownika | Priorytet | Kryterium Akceptacji (Test) |
| :--- | :--- | :--- | :--- |
| <nobr>**FR-11**</nobr> | Jako administrator, chcę zablokować użytkownika za spam lub obraźliwe treści. | **Must have** | Przycisk „Zablokuj” w panelu admina odcina dostęp do konta na wybrany okres (np. 7 dni). |
| **FR-12** | Jako administrator, chcę zarządzać uprawnieniami kont. | **Could have** | Możliwość zaakceptowania wniosku o zostanie moderatorem, oraz zabranie uprawnien moderatora. |
| **FR-13** | Jako użytkownik, chcę zgłosić materiał pełen błędów, aby admin mógł go usunąć. | **Must have** | Przycisk „Zgłoś błąd/spam” przy każdym materiale przesyła powiadomienie do moderatora/admina. |

#### V. Monetyzacja i Premium
| ID | Historyjka Użytkownika | Priorytet | Kryterium Akceptacji (Test) |
| :--- | :--- | :--- | :--- |
| <nobr>**FR-14**</nobr> | Jako moderator, chcę wypłacać zarobione środki za sprawdzanie prac płatnych. | **Should have** | System sumuje zarobki za każdą sprawdzoną pracę i umożliwia zlecenie wypłaty w panelu finansowym. |
| **FR-15** | Jako student, chcę zapłacić za sprawdzenie eseju. | **Must have** | Integracja z bramką płatności; zlecenie pojawia się u moderatora dopiero po statusie „Opłacone”. ||

---

## Wymagania niefunkcjonalne

| ID | Kategoria | Opis wymagania | Kryterium Akceptacji (Testowalność) |
| :--- | :--- | :--- | :--- |
| <nobr>**NFR-01**</nobr> | **Wydajność** | Czas ładowania pytań egzaminacyjnych. | Każde pytanie testowe wraz z grafiką pomocniczą musi załadować się w czasie poniżej 1.5 sekundy. |
| <nobr>**NFR-02**</nobr> | **Niezawodność** | Mechanizm autozapisu postępów. | System musi zapisywać stan trwającego testu (wybrane odpowiedzi) po każdym kliknięciu, aby odświeżenie strony nie powodowało utraty danych. |
| <nobr>**NFR-03**</nobr> | **Bezpieczeństwo** | Szyfrowanie danych i komunikacji. | Wszystkie hasła muszą być hashowane (np. Argon2/bcrypt), a komunikacja między klientem a serwerem musi być szyfrowana (SSL/TLS). |
| <nobr>**NFR-04**</nobr> | **Dostępność** | Projektowanie uniwersalne (Inkluzywność). | Interfejs musi posiadać współczynnik kontrastu tekstu do tła zapewniający czytelność nawet na starych budżetowych monitorach LCD. |
| <nobr>**NFR-05**</nobr> | **Użyteczność** | Intuicyjność procesu nauki. | Nowy użytkownik musi być w stanie rozpocząć test diagnostyczny w mniej niż minutę od pierwszego pomyślnego zalogowania. |
| <nobr>**NFR-06**</nobr> | **Stabilność** | Obsługa błędów płatności. | W przypadku awarii bramki płatniczej, system musi wyświetlić czytelny komunikat błędu i zapobiec podwójnemu obciążeniu konta użytkownika. |
| <nobr>**NFR-07**</nobr> | **Prywatność** | Izolacja skryptów reklamowych. | Skrypty sieci reklamowych nie mogą mieć dostępu do bazy wyników egzaminacyjnych ani treści prac przesyłanych do moderatorów. |
| <nobr>**NFR-08**</nobr> | **Skalowalność** | Gotowość na szczyty egzaminacyjne. | System musi zachować pełną responsywność przy nagłym wzroście liczby jednoczesnych użytkowników do 50 osób (symulacja nocy przed egzaminem). |