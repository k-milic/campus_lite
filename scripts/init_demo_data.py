from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()

    if User.query.count() == 0:
        admin = User(username="admin", email="admin@campus-lite.ch", role="admin")
        admin.set_password("admin123")

        teacher = User(username="teacher1", email="teacher@campus-lite.ch", role="teacher")
        teacher.set_password("teacher123")

        student = User(username="student1", email="student@campus-lite.ch", role="student")
        student.set_password("student123")

        db.session.add_all([admin, teacher, student])
        db.session.commit()

        print("Demo-User erstellt")
