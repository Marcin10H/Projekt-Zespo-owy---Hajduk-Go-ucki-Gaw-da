# System Zarzadzania Rezerwacjami Sal - Proejkt z przedmiotu Projekt Zespołowy, pokazywany co 2 tygodnie na zajęciach.

Wewnetrzna aplikacja webowa do zarzadzania i rezerwacji sal konferencyjnych w firmie.

## Aktualny stan projektu
Obecna wersja obejmuje:
* logowanie z podzialem na role admin/pracownik,
* panel administratora do zarzadzania salami,
* mozliwosc dodawania pracownikow przez administratora,
* mozliwosc zmiany hasla przez pracownika,
* baze danych SQLite z automatycznym kontem startowym admin/admin.

## Instrukcja uruchomienia lokalnego

### 1. Klonowanie repozytorium
```bash
git clone https://github.com/Marcin10H/Projekt-Zespo-owy---Hajduk-Go-ucki-Gaw-da.git
cd Projekt-Zespo-owy---Hajduk-Go-ucki-Gaw-da
```

### 2. Utworzenie i aktywacja srodowiska wirtualnego
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instalacja bibliotek
```bash
python -m pip install Flask flask-sqlalchemy
```

### 4. Uruchomienie serwera
```bash
python app.py
```

Aplikacja bedzie dostepna pod adresem:
http://127.0.0.1:5000
