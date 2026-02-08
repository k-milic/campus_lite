from flask import Flask, render_template, redirect, url_for
from flask_login import login_required, current_user

from config import Config
from app.extensions import db, migrate, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # --------------------------------------------------
    # Extensions
    # --------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # --------------------------------------------------
    # Models laden (wichtig für Migrate)
    # --------------------------------------------------
    from app import models

    # --------------------------------------------------
    # Blueprints
    # --------------------------------------------------
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.teacher import teacher_bp
    app.register_blueprint(teacher_bp)

    from app.admin import admin_bp
    app.register_blueprint(admin_bp)

    # --------------------------------------------------
    # User Loader
    # --------------------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # --------------------------------------------------
    # Basis-Routen
    # --------------------------------------------------
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("auth.login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html")

    # ==================================================
    # STUDENT
    # ==================================================

    # -------------------------
    # Stundenplan
    # -------------------------
    @app.route("/student/schedule")
    @login_required
    def student_schedule():
        if current_user.role != "student":
            return redirect(url_for("dashboard"))

        from app.models import Lesson, Enrollment, Course

        lessons = (
            Lesson.query
            .join(Course)
            .join(Enrollment, Enrollment.course_id == Course.id)
            .filter(Enrollment.student_id == current_user.id)
            .order_by(Lesson.date, Lesson.start_time)
            .all()
        )

        return render_template(
            "student/schedule.html",
            lessons=lessons
        )

    # -------------------------
    # Präsenzeinsicht (Übersicht pro Fach)
    # -------------------------
    @app.route("/student/attendance")
    @login_required
    def student_attendance():
        if current_user.role != "student":
            return redirect(url_for("dashboard"))

        from app.models import Enrollment, Lesson, Attendance

        enrollments = Enrollment.query.filter_by(
            student_id=current_user.id
        ).all()

        overview = []

        for enrollment in enrollments:
            course = enrollment.course

            lessons = Lesson.query.filter_by(course_id=course.id).all()
            total_lessons = len(lessons)

            attendances = (
                Attendance.query
                .join(Lesson)
                .filter(
                    Attendance.student_id == current_user.id,
                    Lesson.course_id == course.id
                )
                .all()
            )

            present_count = sum(
                1 for a in attendances if a.status in ("present", "excused")
            )

            percent = (
                round((present_count / total_lessons) * 100, 1)
                if total_lessons > 0 else 0
            )

            overview.append({
                "course": course,
                "teacher": course.teacher.username,
                "total": total_lessons,
                "present": present_count,
                "percent": percent
            })

        return render_template(
            "student/attendance.html",
            overview=overview
        )

    return app
