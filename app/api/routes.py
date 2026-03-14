from datetime import datetime
from functools import wraps

from flask import g, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.api import api_bp
from app.extensions import db
from app.models import Attendance, Course, Enrollment, Lesson, User

ALLOWED_ROLES = {"student", "teacher", "admin"}
ALLOWED_ATTENDANCE_STATUSES = {"present", "absent", "excused"}


def api_error(message, status=400, details=None):
    payload = {"error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status


def parse_json_body(required=True):
    data = request.get_json(silent=True)
    if data is None:
        if required:
            return None, api_error("JSON request body is required.", 400)
        return {}, None

    if not isinstance(data, dict):
        return None, api_error("JSON request body must be an object.", 400)

    return data, None


def parse_date(value, field_name):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date(), None
    except (TypeError, ValueError):
        return None, api_error(
            f"Field '{field_name}' must use format YYYY-MM-DD.",
            400
        )


def parse_time(value, field_name):
    try:
        return datetime.strptime(value, "%H:%M").time(), None
    except (TypeError, ValueError):
        return None, api_error(
            f"Field '{field_name}' must use format HH:MM.",
            400
        )


def generate_api_token(user):
    return user.generate_token()


def verify_api_token(token):
    user = User.query.filter_by(api_token=token).first()
    if user is None:
        return None, "Invalid token."

    return user, None


def get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1].strip()
    return token or None


def token_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        token = get_bearer_token()
        if token is None:
            return api_error(
                "Missing or invalid Authorization header. "
                "Use 'Bearer <token>'.",
                401
            )

        user, error = verify_api_token(token)
        if error is not None:
            return api_error(error, 401)

        g.api_user = user
        return view_func(*args, **kwargs)

    return wrapper


def roles_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if g.api_user.role not in roles:
                return api_error("Forbidden.", 403)
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


def serialize_course(course):
    return {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "teacher": {
            "id": course.teacher.id,
            "username": course.teacher.username,
            "email": course.teacher.email
        },
        "created_at": course.created_at.isoformat() if course.created_at else None
    }


def serialize_lesson(lesson):
    return {
        "id": lesson.id,
        "course_id": lesson.course_id,
        "date": lesson.date.isoformat(),
        "start_time": lesson.start_time.strftime("%H:%M"),
        "end_time": lesson.end_time.strftime("%H:%M"),
        "room": lesson.room,
        "building": lesson.building
    }


def serialize_attendance(attendance):
    return {
        "id": attendance.id,
        "student_id": attendance.student_id,
        "lesson_id": attendance.lesson_id,
        "status": attendance.status
    }


def can_manage_course(user, course):
    return user.role == "admin" or (
        user.role == "teacher" and course.teacher_id == user.id
    )


def can_view_course(user, course):
    if user.role == "admin":
        return True
    if user.role == "teacher":
        return course.teacher_id == user.id
    if user.role == "student":
        return (
            Enrollment.query.filter_by(
                student_id=user.id,
                course_id=course.id
            ).first()
            is not None
        )
    return False


def lesson_ids_for_course(course_id):
    rows = db.session.query(Lesson.id).filter_by(course_id=course_id).all()
    return [row[0] for row in rows]


def remove_course_dependencies(course_id):
    ids = lesson_ids_for_course(course_id)
    if ids:
        Attendance.query.filter(
            Attendance.lesson_id.in_(ids)
        ).delete(synchronize_session=False)

    Lesson.query.filter_by(course_id=course_id).delete(synchronize_session=False)
    Enrollment.query.filter_by(course_id=course_id).delete(
        synchronize_session=False
    )


def get_model_or_error(model_cls, model_id, label):
    instance = model_cls.query.get(model_id)
    if instance is None:
        return None, api_error(f"{label} not found.", 404)
    return instance, None


@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# -------------------------------
# API Authentication
# -------------------------------
@api_bp.route("/auth/register", methods=["POST"])
def register_api_user():
    data, error = parse_json_body(required=True)
    if error:
        return error

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))

    if not username or not email or not password:
        return api_error("Fields 'username', 'email' and 'password' are required.", 400)

    if len(password) < 6:
        return api_error("Password must be at least 6 characters long.", 400)

    if User.query.filter_by(username=username).first():
        return api_error("Username already exists.", 409)

    if User.query.filter_by(email=email).first():
        return api_error("Email already exists.", 409)

    user = User(
        username=username,
        email=email,
        role="student"
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"user": serialize_user(user)}), 201


@api_bp.route("/login", methods=["POST"])
@api_bp.route("/auth/login", methods=["POST"])
def login_api_user():
    data, error = parse_json_body(required=True)
    if error:
        return error

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return api_error("Fields 'username' and 'password' are required.", 400)

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return api_error("Invalid credentials.", 401)

    token = generate_api_token(user)

    return jsonify({
        "token": token,
        "access_token": token,
        "token_type": "Bearer",
        "user": serialize_user(user)
    }), 200


@api_bp.route("/auth/me", methods=["GET"])
@token_required
def get_authenticated_user():
    return jsonify({"user": serialize_user(g.api_user)}), 200


@api_bp.route("/logout", methods=["POST"])
@api_bp.route("/auth/logout", methods=["POST"])
@token_required
def logout_api_user():
    g.api_user.revoke_token()
    return jsonify({"message": "Logged out."}), 200


# -------------------------------
# Courses
# -------------------------------
@api_bp.route("/courses", methods=["GET"])
@token_required
def list_courses():
    user = g.api_user

    if user.role == "admin":
        query = Course.query
    elif user.role == "teacher":
        query = Course.query.filter_by(teacher_id=user.id)
    else:
        query = (
            Course.query
            .join(Enrollment, Enrollment.course_id == Course.id)
            .filter(Enrollment.student_id == user.id)
        )

    courses = query.order_by(Course.name).all()
    return jsonify({"items": [serialize_course(c) for c in courses]}), 200


@api_bp.route("/courses", methods=["POST"])
@token_required
@roles_required("teacher", "admin")
def create_course():
    data, error = parse_json_body(required=True)
    if error:
        return error

    name = str(data.get("name", "")).strip()
    description = data.get("description")

    if not name:
        return api_error("Field 'name' is required.", 400)

    creator = g.api_user
    teacher_id = creator.id

    if creator.role == "admin":
        teacher_id = data.get("teacher_id")
        if teacher_id is None:
            return api_error("Field 'teacher_id' is required for admins.", 400)

        teacher = User.query.get(teacher_id)
        if teacher is None or teacher.role != "teacher":
            return api_error("teacher_id must reference an existing teacher.", 400)

    course = Course(
        name=name,
        description=description,
        teacher_id=teacher_id
    )

    db.session.add(course)
    db.session.commit()

    return jsonify({"course": serialize_course(course)}), 201


@api_bp.route("/courses/<int:course_id>", methods=["GET"])
@token_required
def get_course(course_id):
    course, error = get_model_or_error(Course, course_id, "Course")
    if error:
        return error

    if not can_view_course(g.api_user, course):
        return api_error("Forbidden.", 403)

    payload = serialize_course(course)
    payload["lesson_count"] = Lesson.query.filter_by(course_id=course.id).count()
    payload["student_count"] = Enrollment.query.filter_by(course_id=course.id).count()

    return jsonify({"course": payload}), 200


@api_bp.route("/courses/<int:course_id>", methods=["PATCH"])
@token_required
@roles_required("teacher", "admin")
def update_course(course_id):
    course, error = get_model_or_error(Course, course_id, "Course")
    if error:
        return error

    actor = g.api_user

    if not can_manage_course(actor, course):
        return api_error("Forbidden.", 403)

    data, parse_error = parse_json_body(required=True)
    if parse_error:
        return parse_error

    if not data:
        return api_error("At least one field must be provided.", 400)

    if "name" in data:
        name = str(data.get("name", "")).strip()
        if not name:
            return api_error("Field 'name' cannot be empty.", 400)
        course.name = name

    if "description" in data:
        course.description = data.get("description")

    if "teacher_id" in data:
        if actor.role != "admin":
            return api_error("Only admins can reassign courses to another teacher.", 403)

        new_teacher = User.query.get(data.get("teacher_id"))
        if new_teacher is None or new_teacher.role != "teacher":
            return api_error("teacher_id must reference an existing teacher.", 400)
        course.teacher_id = new_teacher.id

    db.session.commit()
    return jsonify({"course": serialize_course(course)}), 200


@api_bp.route("/courses/<int:course_id>", methods=["DELETE"])
@token_required
@roles_required("teacher", "admin")
def delete_course(course_id):
    course, error = get_model_or_error(Course, course_id, "Course")
    if error:
        return error

    if not can_manage_course(g.api_user, course):
        return api_error("Forbidden.", 403)

    remove_course_dependencies(course.id)
    db.session.delete(course)
    db.session.commit()

    return jsonify({"message": "Course deleted."}), 200


# -------------------------------
# Enrollment
# -------------------------------
@api_bp.route("/courses/<int:course_id>/students", methods=["GET"])
@token_required
@roles_required("teacher", "admin")
def list_course_students(course_id):
    course, error = get_model_or_error(Course, course_id, "Course")
    if error:
        return error

    if not can_manage_course(g.api_user, course):
        return api_error("Forbidden.", 403)

    students = (
        User.query
        .join(Enrollment, Enrollment.student_id == User.id)
        .filter(
            Enrollment.course_id == course.id,
            User.role == "student"
        )
        .order_by(User.username)
        .all()
    )
    return jsonify({"items": [serialize_user(s) for s in students]}), 200


@api_bp.route("/courses/<int:course_id>/students", methods=["PUT"])
@token_required
@roles_required("teacher", "admin")
def replace_course_students(course_id):
    course, error = get_model_or_error(Course, course_id, "Course")
    if error:
        return error

    if not can_manage_course(g.api_user, course):
        return api_error("Forbidden.", 403)

    data, error = parse_json_body(required=True)
    if error:
        return error

    student_ids = data.get("student_ids")
    if not isinstance(student_ids, list):
        return api_error("Field 'student_ids' must be a list.", 400)

    cleaned_ids = []
    for raw_id in student_ids:
        try:
            cleaned_ids.append(int(raw_id))
        except (TypeError, ValueError):
            return api_error("student_ids must contain only integer values.", 400)

    unique_ids = list(dict.fromkeys(cleaned_ids))

    if unique_ids:
        students = User.query.filter(
            User.id.in_(unique_ids),
            User.role == "student"
        ).all()
        found_ids = {student.id for student in students}
        missing_ids = [sid for sid in unique_ids if sid not in found_ids]
        if missing_ids:
            return api_error(
                "Some student_ids do not exist or are not students.",
                400,
                {"student_ids": missing_ids}
            )

    Enrollment.query.filter_by(course_id=course.id).delete(synchronize_session=False)

    for student_id in unique_ids:
        db.session.add(Enrollment(student_id=student_id, course_id=course.id))

    db.session.commit()

    return jsonify({
        "message": "Course students replaced.",
        "student_ids": unique_ids
    }), 200


@api_bp.route("/courses/<int:course_id>/students/<int:student_id>", methods=["POST"])
@token_required
@roles_required("teacher", "admin")
def add_student_to_course(course_id, student_id):
    course, error = get_model_or_error(Course, course_id, "Course")
    if error:
        return error

    if not can_manage_course(g.api_user, course):
        return api_error("Forbidden.", 403)

    student, error = get_model_or_error(User, student_id, "Student")
    if error:
        return error

    if student is None or student.role != "student":
        return api_error("Student not found.", 404)

    existing = Enrollment.query.filter_by(
        course_id=course.id,
        student_id=student.id
    ).first()
    if existing:
        return api_error("Student already enrolled in this course.", 409)

    db.session.add(Enrollment(course_id=course.id, student_id=student.id))
    db.session.commit()

    return jsonify({"message": "Student enrolled."}), 201


@api_bp.route("/courses/<int:course_id>/students/<int:student_id>", methods=["DELETE"])
@token_required
@roles_required("teacher", "admin")
def remove_student_from_course(course_id, student_id):
    course, error = get_model_or_error(Course, course_id, "Course")
    if error:
        return error

    if not can_manage_course(g.api_user, course):
        return api_error("Forbidden.", 403)

    enrollment = Enrollment.query.filter_by(
        course_id=course.id,
        student_id=student_id
    ).first()
    if enrollment is None:
        return api_error("Enrollment not found.", 404)

    ids = lesson_ids_for_course(course.id)
    if ids:
        Attendance.query.filter(
            Attendance.lesson_id.in_(ids),
            Attendance.student_id == student_id
        ).delete(synchronize_session=False)

    db.session.delete(enrollment)
    db.session.commit()

    return jsonify({"message": "Student removed from course."}), 200


# -------------------------------
# Lessons
# -------------------------------
@api_bp.route("/courses/<int:course_id>/lessons", methods=["GET"])
@token_required
def list_lessons(course_id):
    course, error = get_model_or_error(Course, course_id, "Course")
    if error:
        return error

    if not can_view_course(g.api_user, course):
        return api_error("Forbidden.", 403)

    lessons = (
        Lesson.query
        .filter_by(course_id=course.id)
        .order_by(Lesson.date, Lesson.start_time)
        .all()
    )

    return jsonify({"items": [serialize_lesson(lesson) for lesson in lessons]}), 200


@api_bp.route("/courses/<int:course_id>/lessons", methods=["POST"])
@token_required
@roles_required("teacher", "admin")
def create_lesson(course_id):
    course, error = get_model_or_error(Course, course_id, "Course")
    if error:
        return error

    if not can_manage_course(g.api_user, course):
        return api_error("Forbidden.", 403)

    data, error = parse_json_body(required=True)
    if error:
        return error

    date_raw = data.get("date")
    start_raw = data.get("start_time")
    end_raw = data.get("end_time")

    if not date_raw or not start_raw or not end_raw:
        return api_error(
            "Fields 'date', 'start_time' and 'end_time' are required.",
            400
        )

    lesson_date, error = parse_date(date_raw, "date")
    if error:
        return error

    start_time, error = parse_time(start_raw, "start_time")
    if error:
        return error

    end_time, error = parse_time(end_raw, "end_time")
    if error:
        return error

    if end_time <= start_time:
        return api_error("'end_time' must be after 'start_time'.", 400)

    lesson = Lesson(
        course_id=course.id,
        date=lesson_date,
        start_time=start_time,
        end_time=end_time,
        room=data.get("room"),
        building=data.get("building")
    )

    db.session.add(lesson)
    db.session.commit()

    return jsonify({"lesson": serialize_lesson(lesson)}), 201


@api_bp.route("/lessons/<int:lesson_id>", methods=["GET"])
@token_required
def get_lesson(lesson_id):
    lesson, error = get_model_or_error(Lesson, lesson_id, "Lesson")
    if error:
        return error

    if not can_view_course(g.api_user, lesson.course):
        return api_error("Forbidden.", 403)

    payload = serialize_lesson(lesson)
    payload["course"] = serialize_course(lesson.course)
    return jsonify({"lesson": payload}), 200


@api_bp.route("/lessons/<int:lesson_id>", methods=["PATCH"])
@token_required
@roles_required("teacher", "admin")
def update_lesson(lesson_id):
    lesson, error = get_model_or_error(Lesson, lesson_id, "Lesson")
    if error:
        return error

    if not can_manage_course(g.api_user, lesson.course):
        return api_error("Forbidden.", 403)

    data, error = parse_json_body(required=True)
    if error:
        return error

    if not data:
        return api_error("At least one field must be provided.", 400)

    next_date = lesson.date
    next_start = lesson.start_time
    next_end = lesson.end_time

    if "date" in data:
        next_date, error = parse_date(data.get("date"), "date")
        if error:
            return error

    if "start_time" in data:
        next_start, error = parse_time(data.get("start_time"), "start_time")
        if error:
            return error

    if "end_time" in data:
        next_end, error = parse_time(data.get("end_time"), "end_time")
        if error:
            return error

    if next_end <= next_start:
        return api_error("'end_time' must be after 'start_time'.", 400)

    lesson.date = next_date
    lesson.start_time = next_start
    lesson.end_time = next_end

    if "room" in data:
        lesson.room = data.get("room")
    if "building" in data:
        lesson.building = data.get("building")

    db.session.commit()
    return jsonify({"lesson": serialize_lesson(lesson)}), 200


@api_bp.route("/lessons/<int:lesson_id>", methods=["DELETE"])
@token_required
@roles_required("teacher", "admin")
def delete_lesson(lesson_id):
    lesson, error = get_model_or_error(Lesson, lesson_id, "Lesson")
    if error:
        return error

    if not can_manage_course(g.api_user, lesson.course):
        return api_error("Forbidden.", 403)

    Attendance.query.filter_by(lesson_id=lesson.id).delete(synchronize_session=False)
    db.session.delete(lesson)
    db.session.commit()

    return jsonify({"message": "Lesson deleted."}), 200


# -------------------------------
# Attendance
# -------------------------------
@api_bp.route("/lessons/<int:lesson_id>/attendance", methods=["GET"])
@token_required
def list_lesson_attendance(lesson_id):
    lesson, error = get_model_or_error(Lesson, lesson_id, "Lesson")
    if error:
        return error

    user = g.api_user

    if can_manage_course(user, lesson.course):
        enrollments = Enrollment.query.filter_by(course_id=lesson.course_id).all()
        attendance_rows = Attendance.query.filter_by(lesson_id=lesson.id).all()
        status_by_student = {
            row.student_id: row.status
            for row in attendance_rows
        }

        items = []
        for enrollment in enrollments:
            items.append({
                "student": serialize_user(enrollment.student),
                "status": status_by_student.get(enrollment.student_id)
            })

        return jsonify({
            "lesson": serialize_lesson(lesson),
            "items": items
        }), 200

    if user.role != "student":
        return api_error("Forbidden.", 403)

    is_enrolled = Enrollment.query.filter_by(
        course_id=lesson.course_id,
        student_id=user.id
    ).first()
    if is_enrolled is None:
        return api_error("Forbidden.", 403)

    own_attendance = Attendance.query.filter_by(
        lesson_id=lesson.id,
        student_id=user.id
    ).first()

    return jsonify({
        "lesson": serialize_lesson(lesson),
        "attendance": own_attendance.status if own_attendance else None
    }), 200


@api_bp.route("/lessons/<int:lesson_id>/attendance", methods=["PUT"])
@token_required
@roles_required("teacher", "admin")
def replace_lesson_attendance(lesson_id):
    lesson, error = get_model_or_error(Lesson, lesson_id, "Lesson")
    if error:
        return error

    if not can_manage_course(g.api_user, lesson.course):
        return api_error("Forbidden.", 403)

    data, error = parse_json_body(required=True)
    if error:
        return error

    items = data.get("items")
    if not isinstance(items, list):
        return api_error("Field 'items' must be a list.", 400)

    enrollment_rows = Enrollment.query.filter_by(course_id=lesson.course_id).all()
    enrolled_student_ids = {row.student_id for row in enrollment_rows}

    normalized = []
    seen_student_ids = set()
    for item in items:
        if not isinstance(item, dict):
            return api_error("Each attendance item must be an object.", 400)

        try:
            student_id = int(item.get("student_id"))
        except (TypeError, ValueError):
            return api_error("Each item needs an integer 'student_id'.", 400)

        status = str(item.get("status", "")).strip()

        if student_id in seen_student_ids:
            return api_error("Duplicate student_id in attendance items.", 400)
        seen_student_ids.add(student_id)

        if student_id not in enrolled_student_ids:
            return api_error(
                f"Student {student_id} is not enrolled in this course.",
                400
            )

        if status not in ALLOWED_ATTENDANCE_STATUSES:
            return api_error(
                "status must be one of: present, absent, excused.",
                400
            )

        normalized.append({"student_id": student_id, "status": status})

    Attendance.query.filter_by(lesson_id=lesson.id).delete(synchronize_session=False)

    for item in normalized:
        db.session.add(
            Attendance(
                student_id=item["student_id"],
                lesson_id=lesson.id,
                status=item["status"]
            )
        )

    db.session.commit()
    return jsonify({"message": "Attendance replaced."}), 200


@api_bp.route("/lessons/<int:lesson_id>/attendance/<int:student_id>", methods=["PUT"])
@token_required
@roles_required("teacher", "admin")
def upsert_attendance_item(lesson_id, student_id):
    lesson, error = get_model_or_error(Lesson, lesson_id, "Lesson")
    if error:
        return error

    if not can_manage_course(g.api_user, lesson.course):
        return api_error("Forbidden.", 403)

    data, error = parse_json_body(required=True)
    if error:
        return error

    status = str(data.get("status", "")).strip()
    if status not in ALLOWED_ATTENDANCE_STATUSES:
        return api_error("status must be one of: present, absent, excused.", 400)

    is_enrolled = Enrollment.query.filter_by(
        course_id=lesson.course_id,
        student_id=student_id
    ).first()
    if is_enrolled is None:
        return api_error("Student is not enrolled in this course.", 400)

    attendance = Attendance.query.filter_by(
        lesson_id=lesson.id,
        student_id=student_id
    ).first()

    if attendance is None:
        attendance = Attendance(
            lesson_id=lesson.id,
            student_id=student_id,
            status=status
        )
        db.session.add(attendance)
    else:
        attendance.status = status

    db.session.commit()

    return jsonify({"attendance": serialize_attendance(attendance)}), 200


# -------------------------------
# Student self-service
# -------------------------------
@api_bp.route("/students/me/courses", methods=["GET"])
@token_required
@roles_required("student")
def student_courses():
    user = g.api_user
    courses = (
        Course.query
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.student_id == user.id)
        .order_by(Course.name)
        .all()
    )
    return jsonify({"items": [serialize_course(course) for course in courses]}), 200


@api_bp.route("/students/me/schedule", methods=["GET"])
@token_required
@roles_required("student")
def student_schedule():
    user = g.api_user
    lessons = (
        Lesson.query
        .join(Course, Course.id == Lesson.course_id)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.student_id == user.id)
        .order_by(Lesson.date, Lesson.start_time)
        .all()
    )
    return jsonify({"items": [serialize_lesson(lesson) for lesson in lessons]}), 200


@api_bp.route("/students/me/attendance", methods=["GET"])
@token_required
@roles_required("student")
def student_attendance():
    user = g.api_user
    enrollments = Enrollment.query.filter_by(student_id=user.id).all()

    overview = []

    for enrollment in enrollments:
        course = enrollment.course

        lessons = Lesson.query.filter_by(course_id=course.id).all()
        total_lessons = len(lessons)

        attendances = (
            Attendance.query
            .join(Lesson)
            .filter(
                Attendance.student_id == user.id,
                Lesson.course_id == course.id
            )
            .all()
        )

        present_count = sum(
            1 for row in attendances if row.status in ("present", "excused")
        )

        percent = (
            round((present_count / total_lessons) * 100, 1)
            if total_lessons > 0 else 0
        )

        overview.append({
            "course": serialize_course(course),
            "total_lessons": total_lessons,
            "present_or_excused": present_count,
            "attendance_percent": percent
        })

    return jsonify({"items": overview}), 200


# -------------------------------
# User administration
# -------------------------------
@api_bp.route("/users", methods=["GET"])
@token_required
@roles_required("admin")
def list_users():
    users = User.query.order_by(User.id).all()
    return jsonify({"items": [serialize_user(user) for user in users]}), 200


@api_bp.route("/users/<int:user_id>", methods=["GET"])
@token_required
@roles_required("admin")
def get_user(user_id):
    user, error = get_model_or_error(User, user_id, "User")
    if error:
        return error

    return jsonify({"user": serialize_user(user)}), 200


@api_bp.route("/users/<int:user_id>", methods=["PATCH"])
@token_required
@roles_required("admin")
def update_user(user_id):
    user, error = get_model_or_error(User, user_id, "User")
    if error:
        return error

    data, parse_error = parse_json_body(required=True)
    if parse_error:
        return parse_error

    if not data:
        return api_error("At least one field must be provided.", 400)

    if "username" in data:
        username = str(data.get("username", "")).strip()
        if not username:
            return api_error("Field 'username' cannot be empty.", 400)
        user.username = username

    if "email" in data:
        email = str(data.get("email", "")).strip()
        if not email:
            return api_error("Field 'email' cannot be empty.", 400)
        user.email = email

    if "role" in data:
        role = str(data.get("role", "")).strip()
        if role not in ALLOWED_ROLES:
            return api_error("role must be one of: student, teacher, admin.", 400)
        user.role = role

    if "password" in data:
        password = str(data.get("password", ""))
        if len(password) < 6:
            return api_error("Password must be at least 6 characters long.", 400)
        user.set_password(password)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return api_error("Username or email already exists.", 409)

    return jsonify({"user": serialize_user(user)}), 200


@api_bp.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
@roles_required("admin")
def delete_user(user_id):
    actor = g.api_user
    user, error = get_model_or_error(User, user_id, "User")
    if error:
        return error

    if actor.id == user.id:
        return api_error("Admin cannot delete own account.", 400)

    Attendance.query.filter_by(student_id=user.id).delete(synchronize_session=False)
    Enrollment.query.filter_by(student_id=user.id).delete(synchronize_session=False)

    teacher_courses = Course.query.filter_by(teacher_id=user.id).all()
    for course in teacher_courses:
        remove_course_dependencies(course.id)
        db.session.delete(course)

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted."}), 200
