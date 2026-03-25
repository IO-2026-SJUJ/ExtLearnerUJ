sequenceDiagram
    actor U as Użytkownik
    participant UI as Interfejs Materiału
    participant S as System
    participant DB as Baza Danych

    U->>UI: Klika "Dodaj do ulubionych"
    UI->>S: Żądanie dodania materiału do ulubionych
    S->>S: Weryfikuje sesję użytkownika
    S->>DB: Sprawdza czy materiał nie jest już w ulubionych
    DB-->>S: Wynik sprawdzenia

    alt Materiał już w ulubionych
        S-->>UI: Komunikat - materiał już dodany
        UI-->>U: Wyświetla informację
    else Materiał nie jest w ulubionych
        S->>DB: Zapisuje materiał na liście ulubionych użytkownika
        DB-->>S: Potwierdzenie zapisu
        S-->>UI: Potwierdzenie wykonania operacji
        UI-->>U: Wyświetla potwierdzenie (zmiana ikony)
    end
