sequenceDiagram
    actor U as Użytkownik
    participant UI as Interfejs Testu
    participant S as System
    participant TS as Serwis Testów
    participant AS as Serwis Oceniania
    participant DB as Baza Danych

    U->>UI: Uruchamia test diagnostyczny
    UI->>S: Żądanie rozpoczęcia testu
    S->>TS: Pobierz pytania diagnostyczne
    TS->>DB: Pobierz pytania z różnych obszarów
    DB-->>TS: Zwraca zestaw pytań
    TS-->>S: Przygotowany test
    S-->>UI: Wyświetla pytania testu

    loop Dla każdego pytania
        UI->>U: Wyświetla pytanie
        U->>UI: Udziela odpowiedzi
    end

    U->>UI: Wysyła test (przycisk zakończ)
    UI->>S: Przesyła odpowiedzi użytkownika

    Note over S, AS: UC05 - Automatyczne ocenianie

    S->>AS: Przekazuje odpowiedzi do oceny
    AS->>DB: Pobiera klucz odpowiedzi
    DB-->>AS: Zwraca klucz odpowiedzi
    AS->>AS: Analizuje odpowiedzi
    AS->>AS: Porównuje z kluczem odpowiedzi
    AS->>AS: Oblicza wynik dla każdego obszaru
    AS->>DB: Zapisuje wynik diagnostyczny
    DB-->>AS: Potwierdzenie zapisu
    AS-->>S: Zwraca wyniki oceny

    S->>DB: Zapisuje kompletne wyniki testu
    DB-->>S: Potwierdzenie zapisu
    S-->>UI: Prezentuje wyniki diagnozy
    UI-->>U: Wyświetla wyniki w podziale na obszary
