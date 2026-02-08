from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from app.teacher import teacher_bp
from app.extensions import db
from app.models import (
    Course,
    Lesson,
    User,
    Enrollment,
    Attendance
)

# ===============================
# KURSE
# ===============================
@teacher_bp.route("/teacher/courses")
@login_required
def course_list():
    if current_user.role != "teacher":
        return redirect(url_for("dashboard"))

    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    return render_template("teacher/courses.html", courses=courses)


@teacher_bp.route("/teacher/courses/create", methods=["GET", "POST"])
@login_required
def create_course():
    if current_user.role != "teacher":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        course = Course(
            name=request.form.get("name"),
            description=request.form.get("description"),
            teacher_id=current_user.id
        )
        db.session.add(course)
        db.session.commit()
        flash("Fach erstellt", "success")
        return redirect(url_for("teacher.course_list"))

    return render_template("teacher/course_create.html")


@teacher_bp.route("/teacher/courses/<int:course_id>/delete", methods=["POST"])
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    if course.teacher_id != current_user.id:
        return redirect(url_for("teacher.course_list"))

    db.session.delete(course)
    db.session.commit()
    flash("Fach gelöscht", "success")
    return redirect(url_for("teacher.course_list"))


# ===============================
# STUDENTEN ZU FACH
# ===============================
@teacher_bp.route("/teacher/courses/<int:course_id>/students", methods=["GET", "POST"])
@login_required
def course_students(course_id):
    course = Course.query.get_or_404(course_id)

    if course.teacher_id != current_user.id:
        return redirect(url_for("teacher.course_list"))

    students = User.query.filter_by(role="student").all()
    enrolled_ids = {
        e.student_id for e in Enrollment.query.filter_by(course_id=course.id)
    }

    if request.method == "POST":
        Enrollment.query.filter_by(course_id=course.id).delete()

        for student_id in request.form.getlist("students"):
            db.session.add(
                Enrollment(
                    student_id=int(student_id),
                    course_id=course.id
                )
            )

        db.session.commit()
        flash("Studenten aktualisiert", "success")
        return redirect(url_for("teacher.course_students", course_id=course.id))

    return render_template(
        "teacher/course_students.html",
        course=course,
        students=students,
        enrolled_ids=enrolled_ids
    )


# ===============================
# LEKTIONEN
# ===============================
@teacher_bp.route("/teacher/courses/<int:course_id>/lessons")
@login_required
def lesson_list(course_id):
    course = Course.query.get_or_404(course_id)

    if course.teacher_id != current_user.id:
        return redirect(url_for("teacher.course_list"))

    lessons = (
        Lesson.query
        .filter_by(course_id=course.id)
        .order_by(Lesson.date, Lesson.start_time)
        .all()
    )

    return render_template(
        "teacher/lessons.html",
        course=course,
        lessons=lessons
    )


@teacher_bp.route("/teacher/courses/<int:course_id>/lessons/create", methods=["GET", "POST"])
@login_required
def create_lesson(course_id):
    course = Course.query.get_or_404(course_id)

    if course.teacher_id != current_user.id:
        return redirect(url_for("teacher.course_list"))

    if request.method == "POST":
        lesson = Lesson(
            course_id=course.id,
            date=request.form.get("date"),
            start_time=request.form.get("start_time"),
            end_time=request.form.get("end_time"),
            room=request.form.get("room"),
            building=request.form.get("building")
        )
        db.session.add(lesson)
        db.session.commit()
        flash("Lektion erstellt", "success")
        return redirect(url_for("teacher.lesson_list", course_id=course.id))

    return render_template("teacher/lesson_create.html", course=course)


@teacher_bp.route("/teacher/lessons/<int:lesson_id>/edit", methods=["GET", "POST"])
@login_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course

    if course.teacher_id != current_user.id:
        return redirect(url_for("teacher.course_list"))

    if request.method == "POST":
        lesson.date = request.form.get("date")
        lesson.start_time = request.form.get("start_time")
        lesson.end_time = request.form.get("end_time")
        lesson.room = request.form.get("room")
        lesson.building = request.form.get("building")

        db.session.commit()
        flash("Lektion aktualisiert", "success")
        return redirect(url_for("teacher.lesson_list", course_id=course.id))

    return render_template("teacher/lesson_edit.html", lesson=lesson)


@teacher_bp.route("/teacher/lessons/<int:lesson_id>/delete", methods=["POST"])
@login_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course

    if course.teacher_id != current_user.id:
        return redirect(url_for("teacher.course_list"))

    db.session.delete(lesson)
    db.session.commit()
    flash("Lektion gelöscht", "success")
    return redirect(url_for("teacher.lesson_list", course_id=course.id))


# ===============================
# PRÄSENZEN PRO LEKTION
# ===============================
@teacher_bp.route("/teacher/lessons/<int:lesson_id>/presences", methods=["GET", "POST"])
@login_required
def lesson_presences(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course

    if course.teacher_id != current_user.id:
        return redirect(url_for("teacher.course_list"))

    enrollments = Enrollment.query.filter_by(course_id=course.id).all()
    students = [e.student for e in enrollments]

    if request.method == "POST":
        Attendance.query.filter_by(lesson_id=lesson.id).delete()

        for student in students:
            status = request.form.get(f"status_{student.id}")
            if status:
                db.session.add(
                    Attendance(
                        student_id=student.id,
                        lesson_id=lesson.id,
                        status=status
                    )
                )

        db.session.commit()
        flash("Präsenzen gespeichert", "success")
        return redirect(
            url_for("teacher.lesson_list", course_id=course.id)
        )

    existing = {
        a.student_id: a.status
        for a in Attendance.query.filter_by(lesson_id=lesson.id)
    }

    return render_template(
        "teacher/lesson_presences.html",
        lesson=lesson,
        students=students,
        existing=existing
    )
