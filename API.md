# REST API (Campus Lite)

## Basis
- Base URL lokal: `http://localhost:5000`
- Alle Requests/Responses sind JSON.
- Auth erfolgt per Bearer Token im Header:
  - `Authorization: Bearer <access_token>`

## Authentisierung (API-only, ohne Browser)
1. `POST http://localhost:5000/api/auth/login` mit `username` + `password` aufrufen.
2. `access_token` aus der Antwort in allen geschuetzten Endpunkten senden.
3. Token-Laufzeit: `API_TOKEN_MAX_AGE` Sekunden (Default `43200` = 12h).

Beispiel (HTTPie):
```bash
http POST :5000/api/auth/login username=teacher1 password=teacher123
http GET :5000/api/courses "Authorization:Bearer <access_token>"
```

## Endpunkte

### System
- `GET http://localhost:5000/api/health`

### Auth
- `POST http://localhost:5000/api/auth/register`
- `POST http://localhost:5000/api/auth/login`
- `GET http://localhost:5000/api/auth/me`
- `POST http://localhost:5000/api/auth/logout`

### Kurse
- `GET http://localhost:5000/api/courses`
- `POST http://localhost:5000/api/courses`
- `GET http://localhost:5000/api/courses/{course_id}`
- `PATCH http://localhost:5000/api/courses/{course_id}`
- `DELETE http://localhost:5000/api/courses/{course_id}`

### Einschreibungen (Studenten in Kurs)
- `GET http://localhost:5000/api/courses/{course_id}/students`
- `PUT http://localhost:5000/api/courses/{course_id}/students`
- `POST http://localhost:5000/api/courses/{course_id}/students/{student_id}`
- `DELETE http://localhost:5000/api/courses/{course_id}/students/{student_id}`

### Lektionen
- `GET http://localhost:5000/api/courses/{course_id}/lessons`
- `POST http://localhost:5000/api/courses/{course_id}/lessons`
- `GET http://localhost:5000/api/lessons/{lesson_id}`
- `PATCH http://localhost:5000/api/lessons/{lesson_id}`
- `DELETE http://localhost:5000/api/lessons/{lesson_id}`

### Praesenzen
- `GET http://localhost:5000/api/lessons/{lesson_id}/attendance`
- `PUT http://localhost:5000/api/lessons/{lesson_id}/attendance`
- `PUT http://localhost:5000/api/lessons/{lesson_id}/attendance/{student_id}`

### Student Self-Service
- `GET http://localhost:5000/api/students/me/courses`
- `GET http://localhost:5000/api/students/me/schedule`
- `GET http://localhost:5000/api/students/me/attendance`

### Admin Benutzerverwaltung
- `GET http://localhost:5000/api/users`
- `GET http://localhost:5000/api/users/{user_id}`
- `PATCH http://localhost:5000/api/users/{user_id}`
- `DELETE http://localhost:5000/api/users/{user_id}`

## Rollen-/Zugriffsmodell (Kurz)
- `student`: nur eigene Daten (`/students/me/*`, eigene Kurs/Lektion-Reads).
- `teacher`: eigene Kurse, Lektionen, Einschreibungen, Praesenzen.
- `admin`: Vollzugriff + Benutzerverwaltung.
