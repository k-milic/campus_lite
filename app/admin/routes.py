from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from app.admin import admin_bp
from app.extensions import db
from app.models import User


def admin_required():
    return current_user.is_authenticated and current_user.role == "admin"


@admin_bp.route("/users")
@login_required
def user_list():
    if not admin_required():
        flash("Kein Zugriff")
        return redirect(url_for("dashboard"))

    users = User.query.all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/update/<int:user_id>", methods=["POST"])
@login_required
def update_user_role(user_id):
    if not admin_required():
        flash("Kein Zugriff")
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(user_id)
    new_role = request.form["role"]

    if new_role in ["student", "teacher", "admin"]:
        user.role = new_role
        db.session.commit()
        flash("Rolle aktualisiert")

    return redirect(url_for("admin.user_list"))


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if not admin_required():
        flash("Kein Zugriff")
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(user_id)

    # Admin darf sich nicht selbst löschen
    if user.id == current_user.id:
        flash("Du kannst dich nicht selbst loeschen")
        return redirect(url_for("admin.user_list"))

    db.session.delete(user)
    db.session.commit()
    flash("Benutzer gelöscht")

    return redirect(url_for("admin.user_list"))
