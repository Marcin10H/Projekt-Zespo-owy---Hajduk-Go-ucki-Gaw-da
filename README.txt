# System Zarządzania Rezerwacjami Sal w Przedsiębiorstwie

Wewnętrzna aplikacja webowa przeznaczona do zarządzania i rezerwacji sal konferencyjnych w firmie. Projekt ma na celu ułatwienie pracownikom przeglądu dostępnych przestrzeni biurowych oraz weryfikację ich wyposażenia. 

## 📌 Aktualny stan projektu
Obecna wersja to działający prototyp, który obejmuje:
* Skonfigurowane środowisko i podstawową architekturę aplikacji.
* Utworzoną lokalną bazę danych pozwalającą na przechowywanie informacji o salach, takich jak nazwa, pojemność, wyposażenie).
* Skrypt zasilający bazę danymi testowymi.
* Podstawowy interfejs użytkownika, który na bieżąco pobiera i wyświetla listę dostępnych sal bezpośrednio z bazy danych.

---

## 🚀 Instrukcja Uruchomienia Lokalnego

Aby uruchomić projekt na swoim komputerze i przetestować jego działanie:

### 1. Klonowanie repozytorium
Pobierz kod na swój dysk i przejdź do folderu z projektem:
```bash
git clone https://github.com/Marcin10H/Projekt-Zespo-owy---Hajduk-Go-ucki-Gaw-da.git
cd Projekt-Zespo-owy---Hajduk-Go-ucki-Gaw-da

### 2. Utworzenie i aktywacja wirtualnego środowiska (venv)
python -m venv venv
.\venv\Scripts\activate

### 3. Instalacja niezbędnych pakietów
Można użyć jednej z poniższych komend, aby zainstalować wymagane biblioteki:
python -m pip install Flask flask-sqlalchemy
# lub
pip install Flask flask-sqlalchemy

### 4. Inicjalizacja Bazy Danych
Zanim uruchomisz aplikację po raz pierwszy, wygeneruj plik bazy danych, która wypełni się testowymi salami:
python init_db.py

## 5. Uruchomienie Serwera
Aby wystartować aplikację, wpisz komendę:
python app.py

Aplikacja będzie gotowa do testów w przeglądarce pod adresem:
http://127.0.0.1:5000




