import secrets
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


# Application user model (students, teachers, admins).
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.String(20),
        nullable=False,
        default="student"  # Allowed values: student | teacher | admin.
    )

    api_token = db.Column(
        db.String(64),
        unique=True,
        index=True,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Store a hashed password instead of raw text.
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    # Validate a plain-text password against the stored hash.
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # Generate and persist a new API token for this user.
    def generate_token(self):
        while True:
            token = secrets.token_hex(32)
            if User.query.filter_by(api_token=token).first() is None:
                self.api_token = token
                db.session.commit()
                return token

    # Revoke current API token.
    def revoke_token(self):
        self.api_token = None
        db.session.commit()

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# Course/subject created and owned by a teacher.
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


# Enrollment mapping between one student and one course.
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

    # Prevent duplicate enrollment of the same student in the same course.
    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "course_id",
            name="uq_student_course"
        ),
    )

    def __repr__(self):
        return f"<Enrollment student={self.student_id} course={self.course_id}>"


# Scheduled lesson inside a course.
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

    # Optional room/location details.
    room = db.Column(db.String(50), nullable=True)
    building = db.Column(db.String(50), nullable=True)

    course = db.relationship("Course", backref="lessons")

    def __repr__(self):
        return (
            f"<Lesson course={self.course_id} "
            f"{self.date} {self.start_time}-{self.end_time}>"
        )


# Attendance status per student per lesson.
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
        db.ForeignKey("lessons.id"),  # Must reference lessons.id.
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="present"  # Allowed values: present | absent | excused.
    )

    student = db.relationship("User", backref="attendances")
    lesson = db.relationship("Lesson", backref="attendances")

    # Enforce at most one attendance entry per student and lesson.
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
