# Analiza zasad SOLID i wzorców projektowych

## 1. Zasady SOLID

### 1.1 Single Responsibility Principle (SRP)
Każda klasa w diagramie posiada jedną, jasno określoną odpowiedzialność:
- `User` odpowiada za zarządzanie kontem użytkownika (rejestracja, logowanie).
- `Material` zarządza materiałami edukacyjnymi.
- `WorkReview` odpowiada za ocenę prac.
- `StatisticsService`, `RecommendationService`, `GradingService` realizują konkretne funkcje systemowe.

**Uzasadnienie:**  
Rozdzielenie odpowiedzialności zwiększa czytelność, testowalność oraz ułatwia rozwój systemu.

---

### 1.2 Open/Closed Principle (OCP)
System jest otwarty na rozszerzenia, ale zamknięty na modyfikacje:
- Hierarchia `Test` → `DiagnosticTest`, `MaterialTest`, `ModeratorTest` umożliwia dodawanie nowych typów testów bez zmiany istniejącego kodu.
- Możliwość rozszerzania ról użytkowników (`User` → `Student`, `Moderator`, `Admin`).

**Uzasadnienie:**  
Nowe funkcjonalności można dodawać poprzez dziedziczenie zamiast modyfikowania istniejących klas.

---

### 1.3 Liskov Substitution Principle (LSP)
Klasy pochodne mogą zastępować klasy bazowe:
- `Student`, `Moderator`, `Admin` mogą być używane wszędzie tam, gdzie oczekiwany jest `User`.
- Każdy typ `Test` może być używany jako `Test`.

**Uzasadnienie:**  
Zachowanie spójności interfejsów zapewnia poprawne działanie systemu przy użyciu polimorfizmu.

---

### 1.4 Interface Segregation Principle (ISP)
Zamiast jednego dużego interfejsu zastosowano wiele wyspecjalizowanych:
- Funkcjonalności są rozdzielone między klasy takie jak `Student`, `Moderator`, `Admin`.
- Serwisy (`RecommendationService`, `StatisticsService`) mają wąskie, konkretne interfejsy.

**Uzasadnienie:**  
Klasy korzystają tylko z metod, które są im potrzebne.

---

### 1.5 Dependency Inversion Principle (DIP)
System opiera się na abstrakcjach:
- Logika biznesowa jest delegowana do serwisów (`GradingService`, `StatisticsService`).
- Klasy wysokiego poziomu (np. `Student`) korzystają z usług zamiast implementować logikę samodzielnie.

**Uzasadnienie:**  
Zmniejsza to sprzężenie między komponentami i ułatwia testowanie.

---

## 2. Wzorce projektowe

## 1. Strategy

### Na czym polega
Wzorzec Strategy polega na wydzieleniu różnych algorytmów do osobnych klas (lub metod), które można stosować zamiennie w zależności od kontekstu. Klient nie musi znać szczegółów implementacji – wybiera jedynie odpowiednią strategię.

### Zastosowanie w projekcie
- `GradingService`:
  - `autoGradeDiagnostic(...)`
  - `autoGradeMaterialTest(...)`

Różne typy testów wymagają różnych sposobów oceniania.

### Uzasadnienie
- umożliwia łatwe dodanie nowych typów oceniania bez modyfikacji istniejącego kodu,
- upraszcza logikę klas takich jak `Test`,
- zwiększa elastyczność systemu.

---

## 2. Factory Method

### Na czym polega
Factory Method polega na delegowaniu procesu tworzenia obiektów do specjalnych metod, zamiast bezpośredniego używania konstruktorów. Ukrywa to szczegóły tworzenia i pozwala kontrolować proces inicjalizacji.

### Zastosowanie w projekcie
- `Session.create()`
- `Material.create(...)`
- `Work.submit(...)`

### Uzasadnienie
- centralizuje tworzenie obiektów,
- pozwala dodać walidację lub dodatkową logikę przy tworzeniu,
- ułatwia zmianę sposobu tworzenia obiektów bez wpływu na resztę systemu.

---

## 3. Service Layer

### Na czym polega
Service Layer to wzorzec architektoniczny, który polega na wydzieleniu logiki biznesowej do osobnej warstwy usług. Modele domenowe pozostają prostsze i skupione na danych.

### Zastosowanie w projekcie
- `RecommendationService`
- `StatisticsService`
- `RankingService`
- `GradingService`

### Uzasadnienie
- oddziela logikę biznesową od danych,
- ułatwia testowanie i rozwój systemu,
- zapobiega nadmiernemu rozrostowi klas domenowych (np. `User`, `Student`).

---

## 4. Composite

### Na czym polega
Composite pozwala traktować obiekty pojedyncze i złożone w jednolity sposób poprzez strukturę drzewiastą (całość-składniki).

### Zastosowanie w projekcie
- `Material` zawiera:
  - `FileAttachment`
  - `Test`
- `Test` zawiera `Question`

### Uzasadnienie
- upraszcza operacje na złożonych strukturach danych,
- umożliwia rekurencyjne przetwarzanie (np. materiał → test → pytania),
- dobrze odwzorowuje naturalną strukturę systemu edukacyjnego.

---

## Podsumowanie

Wybrane wzorce wspierają:
- elastyczność i rozszerzalność (Strategy),
- kontrolę tworzenia obiektów (Factory Method),
- separację logiki biznesowej (Service Layer),
- przejrzystą strukturę danych (Composite).

Dzięki nim system jest łatwiejszy w utrzymaniu, skalowalny i zgodny z dobrymi praktykami projektowymi.
