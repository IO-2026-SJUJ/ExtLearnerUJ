sequenceDiagram
    actor U as Użytkownik
    participant E as Klient Email
    participant UI as Interfejs Systemu
    participant S as System
    participant DB as Baza Danych

    U->>E: Otwiera wiadomość email
    E->>U: Wyświetla email z linkiem aktywacyjnym
    U->>E: Klika link aktywacyjny
    E->>UI: Przekierowanie do systemu z tokenem
    UI->>S: Przesyła token aktywacyjny
    S->>DB: Pobiera dane tokenu
    DB-->>S: Zwraca dane tokenu

    S->>S: Weryfikuje ważność tokenu

    alt Token ważny
        S->>DB: Ustawia status konta na "aktywne"
        DB-->>S: Potwierdzenie aktualizacji
        S->>DB: Usuwa/dezaktywuje token
        S-->>UI: Przekierowanie na stronę sukcesu
        UI-->>U: Wyświetla potwierdzenie aktywacji konta
    else Token wygasły
        S-->>UI: Komunikat o wygaśnięciu tokenu
        UI-->>U: Wyświetla błąd - token wygasł
    else Token nieistniejący
        S-->>UI: Komunikat o nieprawidłowym tokenie
        UI-->>U: Wyświetla błąd - nieprawidłowy link
    end
