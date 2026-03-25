# Scenariusze przypadków użycia

## UC01 – Rejestracja konta

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik nie ma jeszcze konta i posiada poprawny adres e-mail.
- **Warunki końcowe:** Konto zostaje utworzone, a po potwierdzeniu e-mail aktywowane.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję rejestracji.
  2. Wprowadza dane wymagane do utworzenia konta.
  3. System sprawdza poprawność danych.
     -> *Jeśli dane są niepoprawne:* System wyświetla komunikat o błędzie i wraca do kroku 2.
  4. System tworzy konto i wysyła wiadomość aktywacyjną.
  5. Użytkownik potwierdza adres e-mail w UC02.
  6. System aktywuje konto.
- **Powiązania:** `UC01 <<include>> UC02`

## UC02 – Weryfikacja email

- **Aktor:** Podstawowy użytkownik / System
- **Warunki początkowe:** Konto zostało utworzone, a link aktywacyjny został wysłany.
- **Warunki końcowe:** Adres e-mail zostaje potwierdzony, konto staje się aktywne.
- **Scenariusz (główny przepływ):**
  1. Użytkownik otwiera wiadomość e-mail z linkiem aktywacyjnym.
  2. Kliknięcie linku przekierowuje do systemu.
  3. System weryfikuje ważność tokenu.
     -> *Jeśli token jest nieważny lub wygasły:* System wyświetla komunikat o błędzie i kończy scenariusz niepowodzeniem.
  4. System aktywuje konto użytkownika.
  5. Użytkownik otrzymuje potwierdzenie aktywacji.
- **Powiązania:** `<<include>>` w UC01

## UC03 – Logowanie

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik ma aktywne konto.
- **Warunki końcowe:** Użytkownik uzyskuje dostęp do systemu.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję logowania.
  2. Podaje login/e-mail oraz hasło.
  3. System weryfikuje dane logowania.
     -> *Jeśli dane są niepoprawne:* System wyświetla komunikat o błędzie i wraca do kroku 2.
  4. System tworzy sesję użytkownika.
  5. Użytkownik trafia do panelu głównego.

## UC04 – Wykonanie testu diagnostycznego

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik jest zalogowany.
- **Warunki końcowe:** Wyniki testu zostają zapisane.
- **Scenariusz (główny przepływ):**
  1. Użytkownik uruchamia test diagnostyczny.
  2. System wyświetla pytania z różnych obszarów.
  3. Użytkownik udziela odpowiedzi.
  4. Użytkownik wysyła test.
  5. System uruchamia automatyczne ocenianie w UC05.
  6. System zapisuje wyniki testu.
- **Powiązania:** `UC04 <<include>> UC05`

## UC05 – Automatyczne ocenianie w poszczególnych obszarach

- **Aktor:** System
- **Warunki początkowe:** Odpowiedzi z testu diagnostycznego zostały przesłane.
- **Warunki końcowe:** Wyniki i ocena obszarów zostają obliczone.
- **Scenariusz (główny przepływ):**
  1. System analizuje odpowiedzi użytkownika.
  2. Porównuje je z kluczem odpowiedzi.
  3. Oblicza wynik dla każdego obszaru.
  4. Zapisuje wynik diagnostyczny.
  5. Udostępnia dane do rekomendacji materiałów.
- **Powiązania:** `<<include>>` w UC04

## UC06 – Sprawdzenie rekomendacji materiałów

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Dostępne są wyniki testu diagnostycznego.
- **Warunki końcowe:** Użytkownik widzi listę rekomendowanych materiałów.
- **Scenariusz (główny przepływ):**
  1. Użytkownik otwiera sekcję rekomendacji.
  2. System analizuje wyniki diagnostyczne.
  3. System dobiera materiały zgodne z brakami w wiedzy.
  4. System prezentuje rekomendacje w kolejności priorytetu.
  5. Użytkownik może przejść do wybranego materiału.

## UC07 – Przeglądanie materiałów

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik jest zalogowany.
- **Warunki końcowe:** Użytkownik wyświetla wybrany materiał.
- **Scenariusz (główny przepływ):**
  1. Użytkownik otwiera katalog materiałów.
  2. System prezentuje listę materiałów z filtrami i wyszukiwarką.
  3. Użytkownik wybiera konkretny materiał.
  4. System wyświetla szczegóły materiału.
  5. Użytkownik może skorzystać z funkcji dodatkowych: ulubione, znacznik weryfikacji, głosowanie.
     -> *Jeśli użytkownik nie jest zalogowany (alternatywna ścieżka do UC03):* -> UC03
- **Powiązania:** `UC07 <<include>> UC08`, `UC07 <<include>> UC09`, `UC07 <<include>> UC10`

## UC08 – Dodawanie materiału do ulubionych

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik przegląda materiał.
- **Warunki końcowe:** Materiał zostaje zapisany na liście ulubionych.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję „Dodaj do ulubionych”.
  2. System zapisuje materiał na jego liście.
  3. System potwierdza wykonanie operacji.
- **Powiązania:** `<<extend>>` w UC07

## UC09 – Sprawdzanie znacznika weryfikacji i priorytetu

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik ogląda szczegóły materiału.
- **Warunki końcowe:** Użytkownik zna status weryfikacji i priorytet materiału.
- **Scenariusz (główny przepływ):**
  1. Użytkownik otwiera szczegóły materiału.
  2. System wyświetla znacznik weryfikacji.
  3. System pokazuje priorytet materiału.
  4. Użytkownik decyduje, czy chce dalej korzystać z materiału.
- **Powiązania:** `<<extend>>` w UC07

## UC10 – Głosowanie na materiał – zwiększanie jego priorytetu

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik przegląda materiał i ma prawo głosu.
- **Warunki końcowe:** Priorytet materiału zostaje zwiększony.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję głosowania.
  2. System sprawdza, czy użytkownik może głosować.
     -> *Jeśli użytkownik nie ma prawa głosu:* System wyświetla komunikat i kończy scenariusz niepowodzeniem.
  3. System zapisuje głos.
  4. System zwiększa priorytet materiału.
  5. Użytkownik widzi potwierdzenie akcji.
- **Powiązania:** `<<extend>>` w UC07

## UC11 – Nauka z materiałów

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik wybrał materiał do nauki.
- **Warunki końcowe:** Postęp nauki zostaje zapisany, a użytkownik może przejść do testu.
- **Scenariusz (główny przepływ):**
  1. Użytkownik otwiera wybrany materiał.
  2. Zapoznaje się z treścią.
  3. System umożliwia przejście do testu sprawdzającego.
  4. Użytkownik rozpoczyna UC12.
- **Powiązania:** `UC11 <<include>> UC12`

## UC12 – Wykonanie testu sprawdzającego zakres materiału

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik zakończył naukę materiału.
- **Warunki końcowe:** Wynik testu zostaje zapisany.
- **Scenariusz (główny przepływ):**
  1. Użytkownik uruchamia test sprawdzający.
  2. System wyświetla pytania związane z materiałem.
  3. Użytkownik udziela odpowiedzi.
  4. Użytkownik przesyła test.
  5. System ocenia wynik.
  6. System uruchamia aktualizację statystyk w UC13.
- **Powiązania:** `UC12 <<include>> UC13`

## UC13 – Aktualizowanie statystyk

- **Aktor:** System
- **Warunki początkowe:** Dostępny jest wynik testu sprawdzającego.
- **Warunki końcowe:** Statystyki użytkownika zostają zaktualizowane.
- **Scenariusz (główny przepływ):**
  1. System pobiera wynik testu.
  2. Aktualizuje poziom opanowania materiału.
  3. Zapisuje statystyki postępu.
  4. Udostępnia dane do widoku statystyk.
- **Powiązania:** `<<include>>` w UC12

## UC14 – Sprawdzanie swoich statystyk

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik jest zalogowany i ma zapisane dane aktywności.
- **Warunki końcowe:** Statystyki są wyświetlone użytkownikowi.
- **Scenariusz (główny przepływ):**
  1. Użytkownik otwiera panel statystyk.
  2. System prezentuje postęp nauki, wyniki testów i aktywność.
  3. Użytkownik analizuje swoje dane.
  4. Użytkownik może pobrać raport w UC15.
     -> *Jeśli użytkownik nie jest zalogowany (alternatywna ścieżka do UC03):* -> UC03
- **Powiązania:** `UC15 <<extend>> UC14`

## UC15 – Pobranie raportu z całego okresu nauki

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik przegląda swoje statystyki.
- **Warunki końcowe:** Raport zostaje wygenerowany i pobrany.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję pobrania raportu.
  2. System generuje raport z całego okresu nauki.
  3. System tworzy plik do pobrania.
  4. Użytkownik zapisuje raport lokalnie.
- **Powiązania:** `<<extend>>` w UC14

## UC16 – Dodanie własnego materiału

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik jest zalogowany i ma uprawnienie do dodania materiału.
- **Warunki końcowe:** Materiał zostaje zapisany do dalszej weryfikacji.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję dodania materiału.
  2. Wypełnia dane materiału.
  3. Dodaje pliki w UC18.
     -> *Jeśli pliki nie zostaną dodane (alternatywna ścieżka):* System zapisuje materiał bez plików i kończy scenariusz.
  4. Opcjonalnie tworzy testy/ćwiczenia w UC17.
  5. System zapisuje materiał.
- **Powiązania:** `UC16 <<include>> UC18`, `UC17 <<extend>> UC16`

## UC17 – Tworzenie testu sprawdzającego i/lub ćwiczeń

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik dodaje własny materiał.
- **Warunki końcowe:** Testy lub ćwiczenia zostają przypisane do materiału.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję tworzenia testu/ćwiczeń.
  2. Definiuje pytania i zadania.
  3. Zapisuje treści.
  4. System dołącza je do materiału.
- **Powiązania:** `<<extend>>` w UC16

## UC18 – Załączanie plików

- **Aktor:** Podstawowy użytkownik / Kandydat na Moderatora
- **Warunki początkowe:** Użytkownik dodaje materiał lub przesyła pracę.
- **Warunki końcowe:** Pliki zostają dołączone do przesyłki.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera pliki z urządzenia.
  2. System sprawdza ich typ i rozmiar.
     -> *Jeśli plik ma nieobsługiwany typ lub przekracza rozmiar:* System wyświetla komunikat o błędzie i nie dołącza pliku.
  3. System przesyła pliki.
  4. System przypisuje je do materiału lub pracy.
- **Powiązania:** `<<include>>` w UC16 i UC29

## UC19 – Przesłanie pracy pisemnej do sprawdzenia

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik ma gotową pracę do sprawdzenia.
- **Warunki końcowe:** Praca zostaje wysłana do systemu i oczekuje na sprawdzenie.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję przesłania pracy.
  2. System proponuje wybór pakietu w UC20.
  3. Użytkownik opłaca usługę w UC21.
     -> *Jeśli płatność nie zostanie zrealizowana:* System wyświetla komunikat o niepowodzeniu i kończy scenariusz.
  4. Użytkownik dodaje pracę i wysyła ją do sprawdzenia.
  5. System rejestruje zgłoszenie.
- **Powiązania:** `UC19 <<include>> UC20`, `UC19 <<include>> UC21`, `UC22 <<extend>> UC19`

## UC20 – Wybór pakietu

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik chce przesłać pracę do sprawdzenia.
- **Warunki końcowe:** Pakiet zostaje wybrany.
- **Scenariusz (główny przepływ):**
  1. Użytkownik otwiera listę dostępnych pakietów.
  2. System prezentuje zakres usług.
  3. Użytkownik wybiera pakiet.
  4. System przekazuje wybór do płatności UC21.
- **Powiązania:** `<<include>>` w UC19

## UC21 – Płatność

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik wybrał pakiet.
- **Warunki końcowe:** Płatność zostaje zrealizowana albo odrzucona.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera metodę płatności.
  2. System przekierowuje do operatora płatności.
  3. Użytkownik zatwierdza transakcję.
  4. System otrzymuje potwierdzenie płatności.
  5. System umożliwia wysłanie pracy.
- **Powiązania:** `<<include>>` w UC19

## UC22 – Sprawdzenie cennika

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik chce poznać koszt sprawdzenia pracy.
- **Warunki końcowe:** Cennik zostaje wyświetlony.
- **Scenariusz (główny przepływ):**
  1. Użytkownik otwiera sekcję cennika.
  2. System wyświetla dostępne pakiety i ceny.
  3. Użytkownik wraca do UC19 i wybiera odpowiednią usługę.
- **Powiązania:** `<<extend>>` w UC19

## UC23 – Przegląd ocenionej pracy pisemnej

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Praca została sprawdzona przez moderatora.
- **Warunki końcowe:** Użytkownik widzi ocenę, komentarze i poprawki.
- **Scenariusz (główny przepływ):**
  1. Użytkownik otwiera ocenioną pracę.
  2. System wyświetla wynik, komentarze i zaznaczone błędy.
  3. Użytkownik analizuje feedback.
  4. Użytkownik może ocenić moderatora w UC24.
     -> *Jeśli użytkownik nie chce oceniać moderatora:* System kończy scenariusz.
- **Powiązania:** `UC24 <<extend>> UC23`

## UC24 – Ocena moderatora

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik przegląda ocenioną pracę.
- **Warunki końcowe:** Ocena moderatora zostaje zapisana.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję oceny moderatora.
  2. Wystawia ocenę i/lub komentarz.
  3. System zapisuje ocenę.
  4. System aktualizuje ranking jakości moderatorów.
- **Powiązania:** `<<extend>>` w UC23

## UC25 – Zgłaszanie materiałów i użytkowników

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik jest zalogowany i widzi materiał lub profil użytkownika.
- **Warunki końcowe:** Zgłoszenie zostaje zapisane i przekazane do rozpatrzenia.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję zgłoszenia.
  2. Określa, czy zgłasza materiał, czy użytkownika.
  3. Podaje powód zgłoszenia.
  4. System rejestruje zgłoszenie.
  5. Zgłoszenie trafia do administratora.

## UC26 – Usuwanie konta

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** Użytkownik jest zalogowany.
- **Warunki końcowe:** Konto zostaje usunięte lub zdezaktywowane zgodnie z polityką systemu.
- **Scenariusz (główny przepływ):**
  1. Użytkownik wybiera opcję usunięcia konta.
  2. System prosi o potwierdzenie operacji.
  3. Użytkownik potwierdza decyzję.
  4. System usuwa lub dezaktywuje konto.
  5. System kończy sesję użytkownika.

## UC27 – Sprawdzanie rankingu studentów

- **Aktor:** Podstawowy użytkownik
- **Warunki początkowe:** System ma dostępne dane rankingowe.
- **Warunki końcowe:** Ranking jest wyświetlony.
- **Scenariusz (główny przepływ):**
  1. Użytkownik otwiera ranking.
  2. System pobiera dane z wyników i aktywności.
  3. System sortuje użytkowników według przyjętego kryterium.
  4. Użytkownik widzi aktualną listę rankingową.

---

## UC28 – Wysłanie zgłoszenia

- **Aktor:** Kandydat na Moderatora
- **Warunki początkowe:** Kandydat ma dostęp do formularza zgłoszeniowego.
- **Warunki końcowe:** Zgłoszenie zostaje wysłane do administratora.
- **Scenariusz (główny przepływ):**
  1. Kandydat otwiera formularz aplikacyjny.
  2. System przechodzi do UC29 i UC30.
  3. Kandydat uzupełnia formularz i wykonuje wymagany test.
  4. Kandydat wysyła zgłoszenie.
  5. System zapisuje wniosek do rozpatrzenia.
     -> *Jeśli test nie zostanie zdany:* System wyświetla komunikat o niepowodzeniu i nie wysyła zgłoszenia (kończy scenariusz).
- **Powiązania:** `UC28 <<include>> UC29`, `UC28 <<include>> UC30`

## UC29 – Wypełnienie formularza i załączenie plików

- **Aktor:** Kandydat na Moderatora
- **Warunki początkowe:** Kandydat rozpoczął proces aplikacji.
- **Warunki końcowe:** Formularz i załączniki zostają zapisane.
- **Scenariusz (główny przepływ):**
  1. Kandydat wpisuje dane osobowe i uzasadnienie aplikacji.
  2. Dodaje wymagane pliki.
  3. System waliduje kompletność danych.
     -> *Jeśli dane są niekompletne:* System wyświetla komunikat o błędzie i wraca do kroku 1.
  4. System zapisuje formularz.
- **Powiązania:** `<<include>>` w UC28

## UC30 – Wykonanie testu sprawdzającego

- **Aktor:** Kandydat na Moderatora
- **Warunki początkowe:** Kandydat wypełnił formularz aplikacyjny.
- **Warunki końcowe:** Wynik testu zostaje zapisany.
- **Scenariusz (główny przepływ):**
  1. Kandydat uruchamia test sprawdzający.
  2. System wyświetla pytania kwalifikacyjne.
  3. Kandydat odpowiada na pytania.
  4. System ocenia test.
  5. Wynik zostaje dołączony do aplikacji.
- **Powiązania:** `<<include>>` w UC28

---

## UC31 – Weryfikacja materiału

- **Aktor:** Moderator
- **Warunki początkowe:** Materiał oczekuje na weryfikację.
- **Warunki końcowe:** Materiał zostaje zweryfikowany, a autor otrzymuje informację o wyniku.
- **Scenariusz (główny przepływ):**
  1. Moderator otwiera zgłoszony materiał.
  2. Analizuje treść, jakość i zgodność z zasadami.
  3. W razie potrzeby korzysta z UC34 i UC35.
     -> *Jeśli podczas analizy wykryte zostaną poważne błędy:* -> UC34
  4. Moderator podejmuje decyzję w UC33.
  5. System wykonuje powiadomienie autora w UC32.
     -> *Jeśli decyzja to odrzucenie lub wysłanie do poprawy:* -> UC35
- **Powiązania:** `UC31 <<include>> UC32`, `UC31 <<include>> UC33`, `UC34 <<extend>> UC31`, `UC35 <<extend>> UC31`

## UC32 – Powiadomienie autora o zakończonej weryfikacji jego materiału

- **Aktor:** System
- **Warunki początkowe:** Moderator zakończył weryfikację materiału.
- **Warunki końcowe:** Autor otrzymuje powiadomienie.
- **Scenariusz (główny przepływ):**
  1. System odczytuje wynik weryfikacji.
  2. Generuje wiadomość do autora.
  3. Wysyła powiadomienie w aplikacji i/lub e-mail.
- **Powiązania:** `<<include>>` w UC31

## UC33 – Zatwierdzenie / Odrzucenie / Wysłanie do poprawy

- **Aktor:** Moderator
- **Warunki początkowe:** Materiał został oceniony przez moderatora.
- **Warunki końcowe:** Status materiału zostaje ustawiony.
- **Scenariusz (główny przepływ):**
  1. Moderator wybiera jedną z trzech decyzji.
  2. System zapisuje status materiału.
  3. W razie potrzeby materiał trafia do poprawy.
  4. Przy akceptacji materiał przechodzi do publikacji.

## UC34 – Wystawienie komentarza do materiału

- **Aktor:** Moderator
- **Warunki początkowe:** Trwa proces weryfikacji materiału.
- **Warunki końcowe:** Komentarz zostaje zapisany i przypisany do materiału.
- **Scenariusz (główny przepływ):**
  1. Moderator wpisuje komentarz.
  2. System zapisuje komentarz.
  3. Autor może go odczytać po zakończeniu weryfikacji.
- **Powiązania:** `<<extend>>` w UC31

## UC35 – Edycja testów i zadań

- **Aktor:** Moderator
- **Warunki początkowe:** Moderator weryfikuje materiał zawierający testy lub zadania.
- **Warunki końcowe:** Zmodyfikowane testy lub zadania zostają zapisane.
- **Scenariusz (główny przepływ):**
  1. Moderator otwiera edytor testów i zadań.
  2. Wprowadza poprawki.
  3. System zapisuje zmiany.
  4. Zaktualizowana wersja trafia do materiału.
- **Powiązania:** `<<extend>>` w UC31

## UC36 – Przeglądanie materiałów do weryfikacji zgodnie z priorytetami

- **Aktor:** Moderator
- **Warunki początkowe:** Istnieją materiały oczekujące na weryfikację.
- **Warunki końcowe:** Moderator widzi listę materiałów uporządkowaną wg priorytetu.
- **Scenariusz (główny przepływ):**
  1. Moderator otwiera kolejkę materiałów.
  2. System sortuje materiały według priorytetu.
  3. Moderator wybiera materiał do sprawdzenia.
  4. System przechodzi do UC31.

## UC37 – Sprawdzanie statystyk

- **Aktor:** Moderator
- **Warunki początkowe:** Moderator jest zalogowany.
- **Warunki końcowe:** Statystyki moderatora są wyświetlone.
- **Scenariusz (główny przepływ):**
  1. Moderator otwiera panel statystyk.
  2. System prezentuje liczbę zweryfikowanych materiałów, czas pracy i decyzje.
  3. Moderator analizuje własną aktywność.

## UC38 – Przeglądanie prac do sprawdzenia

- **Aktor:** Moderator
- **Warunki początkowe:** W systemie są dostępne prace czekające na sprawdzenie.
- **Warunki końcowe:** Moderator widzi listę prac do sprawdzenia.
- **Scenariusz (główny przepływ):**
  1. Moderator otwiera kolejkę prac.
  2. System wyświetla dostępne prace.
  3. Moderator wybiera konkretną pracę do rezerwacji lub sprawdzenia.
     -> *Jeśli pracę już rezerwuje inny moderator:* System wyświetla komunikat i wraca do kroku 2.
- **Powiązania:** `UC39 <<extend>> UC38`

## UC39 – Rezerwacja pracy do sprawdzenia

- **Aktor:** Moderator
- **Warunki początkowe:** Moderator przegląda listę prac.
- **Warunki końcowe:** Praca zostaje zarezerwowana przez moderatora.
- **Scenariusz (główny przepływ):**
  1. Moderator wybiera pracę z listy.
  2. Kliknie opcję rezerwacji.
  3. System przypisuje pracę do tego moderatora.
  4. Inni moderatorzy nie mogą jej już zarezerwować.
- **Powiązania:** `<<extend>>` w UC38

## UC40 – Sprawdzanie pracy

- **Aktor:** Moderator
- **Warunki początkowe:** Praca została zarezerwowana przez moderatora.
- **Warunki końcowe:** Praca zostaje oceniona, a uwagi zapisane.
- **Scenariusz (główny przepływ):**
  1. Moderator otwiera zarezerwowaną pracę.
  2. Analizuje treść i strukturę.
  3. Zaznacza błędy w UC41.
  4. Dodaje komentarze w UC42.
  5. Zatwierdza wynik sprawdzenia.
- **Powiązania:** `UC40 <<include>> UC41`, `UC40 <<include>> UC42`

## UC41 – Zaznaczanie błędów w edytorze

- **Aktor:** Moderator
- **Warunki początkowe:** Moderator sprawdza pracę w edytorze.
- **Warunki końcowe:** Błędy zostają oznaczone w dokumencie.
- **Scenariusz (główny przepływ):**
  1. Moderator zaznacza fragment tekstu.
  2. Określa typ błędu.
  3. System zapisuje oznaczenie.
- **Powiązania:** `<<include>>` w UC40

## UC42 – Dodawanie komentarza

- **Aktor:** Moderator
- **Warunki początkowe:** Moderator pracuje nad oceną pracy.
- **Warunki końcowe:** Komentarz zostaje zapisany.
- **Scenariusz (główny przepływ):**
  1. Moderator wpisuje komentarz do pracy.
  2. System zapisuje treść komentarza.
  3. Komentarz jest widoczny dla użytkownika po publikacji wyniku.
- **Powiązania:** `<<include>>` w UC40

---

## UC43 – Sprawdzanie statystyk

- **Aktor:** Administrator
- **Warunki początkowe:** Administrator jest zalogowany.
- **Warunki końcowe:** Statystyki systemowe zostają wyświetlone.
- **Scenariusz (główny przepływ):**
  1. Administrator otwiera panel statystyk.
  2. System prezentuje dane o użytkownikach, moderatorach, materiałach i zgłoszeniach.
  3. Administrator analizuje raporty i wskaźniki.

## UC44 – Rozpatrywanie wniosków o zostanie moderatorem

- **Aktor:** Administrator
- **Warunki początkowe:** Istnieją zgłoszenia kandydatów.
- **Warunki końcowe:** Wniosek zostaje zaakceptowany lub odrzucony.
- **Scenariusz (główny przepływ):**
  1. Administrator otwiera listę wniosków.
  2. Analizuje dane kandydata i wynik testu.
  3. Podejmuje decyzję o przyjęciu lub odrzuceniu.
     -> *Jeśli administrator postanawia zaakceptować kandydata:* -> UC45
- **Powiązania:** `UC45 <<extend>> UC44`

## UC45 – Powiadomienie o zakwalifikowaniu

- **Aktor:** System
- **Warunki początkowe:** Administrator zaakceptował wniosek kandydata.
- **Warunki końcowe:** Kandydat otrzymuje informację o zakwalifikowaniu.
- **Scenariusz (główny przepływ):**
  1. System odczytuje decyzję administratora.
  2. Generuje powiadomienie.
  3. Wysyła wiadomość do kandydata.
- **Powiązania:** `<<extend>>` w UC44

## UC46 – Przeglądanie zgłoszeń użytkowników

- **Aktor:** Administrator
- **Warunki początkowe:** W systemie istnieją zgłoszenia użytkowników.
- **Warunki końcowe:** Administrator widzi listę zgłoszeń.
- **Scenariusz (główny przepływ):**
  1. Administrator otwiera panel zgłoszeń.
  2. System wyświetla listę zgłoszeń.
  3. Administrator wybiera zgłoszenie do rozpatrzenia.
     -> *Jeśli zgłoszenie wymaga dodatkowych danych:* -> UC47
- **Powiązania:** `UC47 <<extend>> UC46`

## UC47 – Rozpatrywanie zgłoszeń

- **Aktor:** Administrator
- **Warunki początkowe:** Administrator wybrał konkretne zgłoszenie.
- **Warunki końcowe:** Zgłoszenie zostaje rozstrzygnięte.
- **Scenariusz (główny przepływ):**
  1. Administrator analizuje treść zgłoszenia.
  2. Sprawdza kontekst materiału lub użytkownika.
  3. Podejmuje decyzję: odrzucenie, ostrzeżenie, blokada, usunięcie itp.
  4. System zapisuje wynik rozpatrzenia.
- **Powiązania:** `<<extend>>` w UC46

## UC48 – Zarządzanie kontami i uprawnieniami

- **Aktor:** Administrator
- **Warunki początkowe:** Administrator jest zalogowany.
- **Warunki końcowe:** Konto lub uprawnienia użytkownika zostają zaktualizowane.
- **Scenariusz (główny przepływ):**
  1. Administrator wyszukuje konto użytkownika.
  2. Otwiera kartę konta.
  3. Zmienia status konta lub poziom uprawnień.
     -> *Jeśli zmiana statusu na „zablokowane”:* System automatycznie odmawia dostępu do funkcji systemu.
  4. Zapisuje zmiany.
  5. System aktualizuje dostęp użytkownika.
