from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


# =========================================================
# USER
# =========================================================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.String(20),
        nullable=False,
        default="student"  # student | teacher | admin
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # -------------------------
    # Passwort-Helper
    # -------------------------
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# =========================================================
# COURSE (FACH)
# =========================================================
class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    teacher = db.relationship(
        "User",
        backref="courses",
        foreign_keys=[teacher_id]
    )

    def __repr__(self):
        return f"<Course {self.name}>"


# =========================================================
# ENROLLMENT (Student ↔ Kurs)
# =========================================================
class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    student = db.relationship("User", backref="enrollments")
    course = db.relationship("Course", backref="enrollments")

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "course_id",
            name="uq_student_course"
        ),
    )

    def __repr__(self):
        return f"<Enrollment student={self.student_id} course={self.course_id}>"


# =========================================================
# LESSON (LEKTION)
# =========================================================
class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    # optional (vor Ort / online)
    room = db.Column(db.String(50), nullable=True)
    building = db.Column(db.String(50), nullable=True)

    course = db.relationship("Course", backref="lessons")

    def __repr__(self):
        return (
            f"<Lesson course={self.course_id} "
            f"{self.date} {self.start_time}-{self.end_time}>"
        )


# =========================================================
# ATTENDANCE (ANWESENHEIT)
# =========================================================
class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lessons.id"),  # 🔴 WICHTIG: lessons.id
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="present"
        # present | absent | excused
    )

    student = db.relationship("User", backref="attendances")
    lesson = db.relationship("Lesson", backref="attendances")

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "lesson_id",
            name="uq_student_lesson"
        ),
    )

    def __repr__(self):
        return (
            f"<Attendance student={self.student_id} "
            f"lesson={self.lesson_id} status={self.status}>"
        )
