# Campus Lite

Campus Lite ist eine Flask-Webanwendung für ein Schulprojekt.
Die App unterstützt die Verwaltung von Kursen/Fächern, Lektionen und Anwesenheiten mit rollenbasierter Sicht.

## Funktionen

- Lehrpersonen können Fächer erstellen, bearbeiten und löschen.
- Lehrpersonen planen Lektionen pro Fach (Datum, Zeit, Raum/Gebäude).
- Lehrpersonen laden Schüler:innen in Fächer ein.
- Lehrpersonen erfassen Präsenzen pro Lektion (`present`, `absent`, `excused`).
- Schüler:innen sehen ihre eingeladenen Fächer, den Stundenplan und ihre Präsenzübersicht.
- Admins verwalten alle registrierten Benutzer und Rollen.

## Rollenmodell

- `student`: Leserechte auf eigene Kurse, Stundenplan und Anwesenheit.
- `teacher`: Verwaltung eigener Kurse, Lektionen, Einschreibungen und Präsenzen.
- `admin`: Benutzerverwaltung und Rollenverwaltung.

## Tech Stack

- Python 3.9
- Flask
- Flask-Login
- Flask-SQLAlchemy
- Flask-Migrate / Alembic
- MySQL 8
- Gunicorn
- Docker & Docker Compose

## REST API

Eine vollständige JSON-API ist unter `/api` verfügbar.
Die kompakte Endpunkt-Dokumentation (Methode + URL + Auth) steht in:

- `API.md`

## Projektstruktur (vereinfacht)

```text
app/
  auth/       # Login/Registrierung/Logout
  teacher/    # Teacher-Funktionen (Kurse, Lektionen, Präsenzen)
  admin/      # Admin-Funktionen (User/Rollen)
  templates/  # Jinja2-Templates
  models.py   # Datenmodelle
scripts/
  init_demo_data.py  # Erstellt Demo-Benutzer
```

## Voraussetzungen

- Docker Desktop (oder Docker Engine + Docker Compose Plugin)
- Optional für lokalen Non-Docker-Betrieb: Python 3.9 und MySQL

## Schnellstart mit Docker

1. `.env` aus der Vorlage erstellen:
   ```bash
   cp .env.example .env
   ```
   Unter Windows PowerShell:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Werte in `.env` setzen (mindestens Passwörter und DB-User).
3. Container starten:
   ```bash
   docker compose up --build
   ```
4. App öffnen: `http://localhost:5000`

Beim Start führt der `web`-Container automatisch aus:
- `flask db upgrade`
- `python -m scripts.init_demo_data`
- Start von Gunicorn auf Port `5000`

## Demo-Accounts (Seed)

Wenn die Datenbank leer ist, werden folgende Benutzer erstellt:

- Admin: `admin` / `admin123`
- Teacher: `teacher1` / `teacher123`
- Studenten: `student1` bis `student10` / jeweils `student123`

Hinweis: Nur für Entwicklung/Präsentation verwenden, nicht in Produktion.

## Lokale Entwicklung ohne Docker (optional)

1. Virtuelle Umgebung erstellen und aktivieren.
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. Datenbank konfigurieren (über `.env` oder `DATABASE_URL`).
4. Migrationen anwenden:
   ```bash
   flask db upgrade
   ```
5. Optional Demo-Daten laden:
   ```bash
   python -m scripts.init_demo_data
   ```
6. Entwicklungsserver starten:
   ```bash
   python run.py
   ```

## Deployment auf VM (Docker)

Empfohlener Ablauf:

1. Projekt auf die VM kopieren (z. B. per Git Clone).
2. Docker + Compose auf der VM installieren.
3. `.env` produktionsnah setzen (sichere Passwörter, Secret Key).
4. Starten:
   ```bash
   docker compose up -d --build
   ```
5. Optional Reverse Proxy (Nginx/Caddy) vor Port `5000` setzen.

## Datenbankmodell (Kurzüberblick)

- `users`: Benutzerkonten + Rolle
- `courses`: Fächer, jeweils einer Lehrperson zugeordnet
- `enrollments`: Zuordnung Schüler:in ↔ Fach
- `lessons`: Lektionen pro Fach
- `attendance`: Präsenz je Schüler:in pro Lektion

## Wichtige Hinweise

- Diese App ist ein Schulprojekt und primär für Lernzwecke gebaut.
- Für produktiven Betrieb sollten zusätzliche Sicherheitsmassnahmen ergänzt werden (z. B. HTTPS, Backup-Strategie, stärkere Validierungen, Monitoring).
