from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():

    # Falls DB leer ist, Demo-Daten anlegen
    if User.query.count() == 0:

        users = []

        # Admin
        admin = User(
            username="admin",
            email="admin@campus-lite.ch",
            role="admin"
        )
        admin.set_password("admin123")
        users.append(admin)

        # Teacher
        teacher = User(
            username="teacher1",
            email="teacher@campus-lite.ch",
            role="teacher"
        )
        teacher.set_password("teacher123")
        users.append(teacher)

        # 10 Studenten
        for i in range(1, 11):
            student = User(
                username=f"student{i}",
                email=f"student{i}@campus-lite.ch",
                role="student"
            )
            student.set_password("student123")
            users.append(student)

        db.session.add_all(users)
        db.session.commit()

        print("Demo-User erfolgreich erstellt.")
    else:
        print("User existieren bereits. Keine neuen erstellt.")