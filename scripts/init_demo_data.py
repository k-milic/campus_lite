from app import create_app
from app.extensions import db
from app.models import User

# Create an app context so DB queries can run from this script.
app = create_app()

with app.app_context():

    # Seed demo users only if the user table is currently empty.
    if User.query.count() == 0:

        users = []

        # Default admin account.
        admin = User(
            username="admin",
            email="admin@campus-lite.ch",
            role="admin"
        )
        admin.set_password("admin123")
        users.append(admin)

        # Default teacher account.
        teacher = User(
            username="teacher1",
            email="teacher@campus-lite.ch",
            role="teacher"
        )
        teacher.set_password("teacher123")
        users.append(teacher)

        # Ten default student accounts.
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
