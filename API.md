# REST API (Campus Lite)

## Basis
- Base URL lokal: `http://localhost:5000`
- Alle Requests/Responses sind JSON.
- Auth erfolgt per Bearer Token im Header:
  - `Authorization: Bearer <access_token>`

## Authentisierung (API-only, ohne Browser)
1. `POST http://localhost:5000/api/login` mit `username` + `password` aufrufen.
2. `token` aus der Antwort in allen geschützten Endpunkten senden.
3. Token wird serverseitig in der DB pro User gespeichert (`users.api_token`).
4. Logout via `POST http://localhost:5000/api/logout` invalidiert den Token.

Beispiel (HTTPie):
```bash
http POST :5000/api/login username=teacher1 password=teacher123
http GET :5000/api/courses "Authorization:Bearer <token>"
```

## Endpunkte

### System
- `GET http://localhost:5000/api/health`

### Auth
- `POST http://localhost:5000/api/auth/register`
- `POST http://localhost:5000/api/login`
- `POST http://localhost:5000/api/logout`
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
- `teacher`: eigene Kurse, Lektionen, Einschreibungen, Präsenzen.
- `admin`: Vollzugriff + Benutzerverwaltung.
