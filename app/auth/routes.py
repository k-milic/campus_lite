from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user
from app.extensions import db, login_manager
from app.models import User
from app.auth import auth_bp


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.check_password(request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Login fehlgeschlagen")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("Benutzername existiert bereits")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("E-Mail existiert bereits")
            return redirect(url_for("auth.register"))

        user = User(username=username, email=email, role="student")
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash("Registrierung erfolgreich, bitte einloggen")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
