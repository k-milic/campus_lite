import random
from datetime import date, time, timedelta

from app import create_app
from app.extensions import db
from app.models import Attendance, Course, Enrollment, Lesson, User

# Create an app context so DB queries can run from this script.
app = create_app()

with app.app_context():
    table_counts = {
        "users": User.query.count(),
        "courses": Course.query.count(),
        "lessons": Lesson.query.count(),
        "enrollments": Enrollment.query.count(),
        "attendance": Attendance.query.count(),
    }

    # Seed only when the full demo dataset is still empty.
    if any(count > 0 for count in table_counts.values()):
        print("Database is not empty. No demo data created.")
        print(
            "Current counts - "
            f"users: {table_counts['users']}, "
            f"courses: {table_counts['courses']}, "
            f"lessons: {table_counts['lessons']}, "
            f"enrollments: {table_counts['enrollments']}, "
            f"attendance: {table_counts['attendance']}"
        )
    else:
        random.seed(42)

        try:
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
            students = []
            for i in range(1, 11):
                student = User(
                    username=f"student{i}",
                    email=f"student{i}@campus-lite.ch",
                    role="student"
                )
                student.set_password("student123")
                users.append(student)
                students.append(student)

            db.session.add_all(users)
            db.session.flush()

            # Demo courses assigned to teacher1.
            course_specs = [
                {
                    "name": "Mathematik",
                    "description": "Grundlagen Algebra und Analysis",
                    "room": "A101",
                    "building": "Hauptgebaeude",
                    "start_time": time(8, 15),
                    "end_time": time(9, 45),
                    "start_date": date(2026, 3, 16),
                },
                {
                    "name": "Informatik",
                    "description": "Python, Datenstrukturen und Algorithmen",
                    "room": "B204",
                    "building": "IT-Campus",
                    "start_time": time(10, 15),
                    "end_time": time(11, 45),
                    "start_date": date(2026, 3, 17),
                },
                {
                    "name": "Netzwerktechnik",
                    "description": "TCP/IP, Routing und Subnetting",
                    "room": "C303",
                    "building": "Lab Center",
                    "start_time": time(13, 15),
                    "end_time": time(14, 45),
                    "start_date": date(2026, 3, 18),
                },
            ]

            courses = []
            lessons = []

            for spec in course_specs:
                course = Course(
                    name=spec["name"],
                    description=spec["description"],
                    teacher_id=teacher.id,
                )
                db.session.add(course)
                db.session.flush()
                courses.append(course)

                # Four weekly lessons per course.
                for week in range(4):
                    lesson = Lesson(
                        course_id=course.id,
                        date=spec["start_date"] + timedelta(weeks=week),
                        start_time=spec["start_time"],
                        end_time=spec["end_time"],
                        room=spec["room"],
                        building=spec["building"],
                    )
                    db.session.add(lesson)
                    lessons.append(lesson)

            db.session.flush()

            # Enroll all students in all courses.
            enrollments = []
            for student in students:
                for course in courses:
                    enrollments.append(
                        Enrollment(student_id=student.id, course_id=course.id)
                    )
            db.session.add_all(enrollments)
            db.session.flush()

            # Attendance distribution: 70% present, 20% late, 10% absent.
            attendance_rows = []
            for lesson in lessons:
                for student in students:
                    value = random.random()
                    if value < 0.70:
                        status = "present"
                    elif value < 0.90:
                        status = "late"
                    else:
                        status = "absent"

                    attendance_rows.append(
                        Attendance(
                            student_id=student.id,
                            lesson_id=lesson.id,
                            status=status,
                        )
                    )

            db.session.add_all(attendance_rows)
            db.session.commit()

            print("Demo data created successfully.")
            print(f"Users: {len(users)} (1 admin, 1 teacher, {len(students)} students)")
            print(f"Courses: {len(courses)}")
            print(f"Lessons: {len(lessons)}")
            print(f"Enrollments: {len(enrollments)}")
            print(f"Attendance records: {len(attendance_rows)}")
        except Exception as exc:
            db.session.rollback()
            print(f"Demo data creation failed: {exc}")
            raise
