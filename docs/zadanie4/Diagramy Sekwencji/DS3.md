sequenceDiagram
    actor U as Użytkownik
    participant UI as Interfejs Logowania
    participant S as System
    participant Auth as Serwis Autoryzacji
    participant DB as Baza Danych

    U->>UI: Wybiera opcję logowania
    UI->>U: Wyświetla formularz logowania
    U->>UI: Podaje login/email oraz hasło
    UI->>S: Przesyła dane logowania
    S->>Auth: Przekazuje dane do weryfikacji
    Auth->>DB: Pobiera dane użytkownika po loginie/email
    DB-->>Auth: Zwraca dane użytkownika (hash hasła, status)

    Auth->>Auth: Porównuje hash hasła

    alt Dane niepoprawne
        Auth-->>S: Błąd uwierzytelnienia
        S-->>UI: Komunikat o błędnych danych
        UI-->>U: Wyświetla błąd logowania
        U->>UI: Ponownie podaje dane
        UI->>S: Przesyła dane logowania
        S->>Auth: Ponowna weryfikacja
        Auth->>DB: Pobiera dane użytkownika
        DB-->>Auth: Zwraca dane
        Auth->>Auth: Porównuje hash hasła
    end

    alt Konto nieaktywne
        Auth-->>S: Konto nieaktywne
        S-->>UI: Komunikat o nieaktywnym koncie
        UI-->>U: Wyświetla informację o konieczności aktywacji
    else Dane poprawne i konto aktywne
        Auth-->>S: Uwierzytelnienie pomyślne
        S->>S: Tworzy sesję użytkownika
        S->>DB: Zapisuje dane sesji
        DB-->>S: Potwierdzenie zapisu sesji
        S-->>UI: Przekierowanie do panelu głównego
        UI-->>U: Wyświetla panel główny
    end
