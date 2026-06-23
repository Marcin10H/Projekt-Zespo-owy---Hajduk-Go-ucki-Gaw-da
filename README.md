# 🏢 System Zarządzania Rezerwacjami Sal

## O projekcie (About the Project)

Wewnętrzna aplikacja webowa do rezerwacji sal konferencyjnych w firmie. Projekt z przedmiotu **Projekt Zespołowy**, robiony etapami na zajęciach.

System pozwala pracownikom przeglądać sale, filtrować je według wymagań i rezerwować terminy. Administrator zarządza salami, użytkownikami i ma podgląd wszystkich rezerwacji w systemie.

### 👥 Role użytkowników

* **Administrator:** dodaje, edytuje i usuwa sale, zakłada i zarządza kontami pracowników, widzi wszystkie rezerwacje w systemie, może je odwoływać (także cudze).
* **Pracownik:** wyszukuje sale, składa rezerwacje, zarządza własnymi rezerwacjami, zmienia hasło.

### 🔧 Panel administratora (szczegóły)

**Sale:**
* dodawanie nowej sali (nazwa, liczba miejsc, informacja o rzutniku),
* edycja istniejącej sali,
* usuwanie sali tylko wtedy, gdy **nie ma do niej żadnych rezerwacji** (system blokuje usunięcie i zwraca komunikat błędu).

**Użytkownicy (pracownicy):**
* dodawanie konta z hasłem startowym (minimum 8 znaków),
* edycja nazwy, loginu i opcjonalnie hasła,
* usuwanie pracownika wraz z jego rezerwacjami,
* administrator **nie może** edytować ani usunąć własnego konta admina przez panel użytkowników,
* przy usuwaniu nie da się skasować samego siebie.

**Rezerwacje:**
* podgląd wszystkich rezerwacji w systemie,
* odwoływanie dowolnej rezerwacji (nie tylko własnej),
* sekcje na dole panelu są zwijane (użytkownicy, wszystkie rezerwacje, moje rezerwacje).

### 🛠️ Technologie i architektura

* **Backend:** Python, Flask, SQLAlchemy (ORM)
* **Baza danych:** SQLite (`database.db` tworzona automatycznie przy pierwszym uruchomieniu)
* **Frontend:** HTML, Bootstrap 5, JavaScript (fetch API)
* **Bezpieczeństwo:** hashowanie haseł (`werkzeug.security`), tokeny CSRF (`Flask-WTF`), sesje z podziałem ról

### 🔒 Bezpieczeństwo

* hasła w bazie są hashowane, nie trzymamy ich jako zwykły tekst,
* przy logowaniu sprawdzane są role (`admin` / `pracownik`), a chronione strony wymagają zalogowania,
* operacje administratora (sale, użytkownicy) są dodatkowo blokowane dla pracownika,
* formularze i żądania API (POST/PUT/DELETE) mają ochronę CSRF,
* nowy pracownik z hasłem startowym **musi je zmienić** zanim zrobi cokolwiek innego w systemie,
* pracownik może odwołać tylko swoją rezerwację, admin może odwołać każdą,
* hasło startowe i nowe hasło muszą mieć co najmniej 8 znaków.

### ⚠️ Walidacja i obsługa błędów

Aplikacja sprawdza dane po stronie serwera i pokazuje komunikaty po polsku (alerty na stronie lub w oknach modalnych):

* puste pola, zły format daty, koniec przed początkiem rezerwacji,
* zajęta sala w wybranym terminie (także przy rezerwacji cyklicznej),
* duplikat loginu lub nazwy sali,
* pojemność sali musi być liczbą większą od zera,
* próba usunięcia sali z rezerwacjami,
* brak uprawnień (np. pracownik próbuje wejść w funkcje admina),
* błędy zapisu do bazy z `rollback` transakcji, żeby nie zostawić niespójnych danych.

API zwraca sensowne kody HTTP (400, 403, 404, 409, 500) z opisem błędu w JSON.

### ⚙️ Najważniejsze funkcje

* Logowanie z podziałem na role (`admin` / `pracownik`)
* Wymuszenie zmiany hasła startowego u nowego pracownika
* Wyszukiwanie sal po liczbie miejsc, rzutniku i opcjonalnym terminie (sprawdzanie dostępności)
* Rezerwacja pojedyncza lub cykliczna (co tydzień przez miesiąc)
* Walidacja konfliktów terminów, system nie pozwala na nakładające się rezerwacje
* Panel administratora ze zwijanymi sekcjami (użytkownicy, wszystkie rezerwacje, moje rezerwacje)
* REST API pod ścieżkami `/api/...` obsługiwane z poziomu panelu

### 📌 Stan projektu

To nadal **prototyp** studencki. Do zrobienia m.in. podział kodu na osobne moduły i migracje bazy (np. Flask-Migrate).

## English Summary

An internal web application for booking conference rooms in a company setting. Built as a **team university project**, developed iteratively during classes.

Employees can browse and filter rooms, check availability, and make reservations. Administrators manage rooms and user accounts and can view or cancel any booking.

### Admin panel details

**Rooms:** add, edit, and delete. A room can only be deleted when it has no reservations.

**Users:** add employees with a temporary password, edit their data, delete accounts (along with their bookings). The main admin account cannot be edited or removed through the user management panel.

**Bookings:** view all reservations in the system and cancel any of them. Bottom sections (users, all bookings, my bookings) are collapsible.

### Security

* password hashing (no plain-text storage),
* session-based login with role checks,
* CSRF protection on forms and API requests,
* forced password change for new employees,
* employees can cancel only their own bookings; admins can cancel any booking,
* minimum password length of 8 characters.

### Validation and errors

Server-side validation with Polish error messages: empty fields, invalid dates, booking conflicts, duplicate logins or room names, permission checks, and database rollback on save errors. API returns proper HTTP status codes with JSON error descriptions.

### Key features

* Role-based access (`admin` / employee)
* Forced password change on first login for new employees
* Room search by capacity, projector, and optional time slot
* Single or recurring weekly reservations (every week for a month)
* Conflict detection for overlapping bookings
* Collapsible admin sections for users and reservations
* Password hashing, CSRF protection, session-based auth

**Tech stack:** Python, Flask, SQLAlchemy, SQLite, Bootstrap 5, JavaScript.

## 📸 Zrzuty ekranu / Screenshots


*Ekran logowania / Login page*

![Ekran logowania](screenshots/logowanie.png)

*Pierwsze logowanie pracownika, wymuszona zmiana hasła / First login, password change required*

![Zmiana hasła startowego](screenshots/zmiana-hasla.png)

*Panel główny pracownika / Employee main panel*

![Panel pracownika](screenshots/panel-pracownik.png)

*Panel główny administratora / Admin main panel*

![Panel administratora](screenshots/panel-admin.png)

*Rezerwacja sali / Room reservation*

![Rezerwacja sali](screenshots/rezerwacja.png)

*Panel administratora, rozwinięte sekcje na dole (użytkownicy, rezerwacje) / Admin panel, expanded bottom sections*

![Panel administratora, sekcje rozwijane](screenshots/panel-admin-sekcje.png)


## 🚀 Uruchomienie lokalne / Local setup

```bash
git clone https://github.com/Marcin10H/Projekt-Zespo-owy---Hajduk-Go-ucki-Gaw-da.git
cd Projekt-Zespo-owy---Hajduk-Go-ucki-Gaw-da

python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux / macOS

python -m pip install -r requirements.txt
python app.py
```

Aplikacja działa pod adresem: **http://127.0.0.1:5000**

**Konto startowe administratora:** login `admin`, hasło `admin`
