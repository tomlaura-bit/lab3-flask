import os
import secrets
import smtplib
import ssl
import time
from email.message import EmailMessage
from functools import wraps

import psycopg
from psycopg.rows import dict_row
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "")
if not app.secret_key:
    raise RuntimeError("Define SECRET_KEY")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def db():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def init_db():
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS admins (
                id BIGSERIAL PRIMARY KEY, username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE, password_hash TEXT NOT NULL)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
                id BIGSERIAL PRIMARY KEY, nombre VARCHAR(120) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'usuario')))""")
            cur.execute("""INSERT INTO admins (username,email,password_hash) VALUES (%s,%s,%s)
                ON CONFLICT DO NOTHING""",
                (os.environ["ADMIN_USERNAME"], os.environ["ADMIN_EMAIL"],
                 generate_password_hash(os.environ["ADMIN_PASSWORD"])))


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def verify_csrf():
    if request.method == "POST" and not secrets.compare_digest(
        str(session.get("csrf", "")), str(request.form.get("csrf", "!"))
    ):
        abort(400)


def login_required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return inner


def send_code(email, code):
    message = EmailMessage()
    message["From"] = os.environ["SMTP_FROM"]
    message["To"] = email
    message["Subject"] = "Código de acceso al laboratorio"
    message.set_content(f"Tu código de acceso es: {code}. Caduca en 10 minutos.")
    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])
    username = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]
    security = os.environ.get("SMTP_SECURITY", "starttls").lower()
    if not all((host, port, username, password)) or security not in ("starttls", "ssl"):
        raise ValueError("Configura SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD y SMTP_SECURITY")
    context = ssl.create_default_context()
    if security == "ssl":
        with smtplib.SMTP_SSL(host, port, timeout=10, context=context) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.starttls(context=context)
            smtp.login(username, password)
            smtp.send_message(message)


@app.route("/")
def home():
    return redirect(url_for("users" if "admin_id" in session else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with db() as conn:
            admin = conn.execute("SELECT * FROM admins WHERE username=%s", (username,)).fetchone()
        if not admin or not check_password_hash(admin["password_hash"], password):
            flash("Usuario o contraseña incorrectos.", "error")
        else:
            code = f"{secrets.randbelow(1000000):06d}"
            try:
                send_code(admin["email"], code)
            except (OSError, ValueError, smtplib.SMTPException):
                app.logger.exception("No se pudo enviar el código")
                flash("No se pudo enviar el código. Inténtalo de nuevo.", "error")
                return render_template("login.html")
            session.clear()
            session.update(pending_id=admin["id"], code_hash=generate_password_hash(code),
                           code_expiry=time.time() + 600, code_attempts=0)
            return redirect(url_for("verify"))
    return render_template("login.html")


@app.route("/verificar", methods=["GET", "POST"])
def verify():
    if "pending_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        if time.time() > session["code_expiry"] or session["code_attempts"] >= 5:
            session.clear()
            flash("Código caducado o demasiados intentos. Inicia sesión otra vez.", "error")
            return redirect(url_for("login"))
        session["code_attempts"] += 1
        if check_password_hash(session["code_hash"], request.form.get("code", "")):
            admin_id = session["pending_id"]
            session.clear()
            session["admin_id"] = admin_id
            return redirect(url_for("users"))
        flash("Código incorrecto.", "error")
    return render_template("verify.html")


@app.post("/salir")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/usuarios")
@login_required
def users():
    with db() as conn:
        rows = conn.execute("SELECT id,nombre,email,rol FROM usuarios ORDER BY id").fetchall()
    return render_template("users.html", users=rows)


def valid_user(form):
    nombre = form.get("nombre", "").strip()
    email = form.get("email", "").strip().lower()
    rol = form.get("rol", "")
    if not nombre or not email or "@" not in email or rol not in ("admin", "usuario"):
        flash("Completa nombre, correo válido y rol.", "error")
        return None
    return nombre, email, rol


@app.route("/usuarios/nuevo", methods=["GET", "POST"])
@login_required
def create_user():
    if request.method == "POST":
        data = valid_user(request.form)
        if data:
            try:
                with db() as conn:
                    conn.execute("INSERT INTO usuarios(nombre,email,rol) VALUES (%s,%s,%s)", data)
                flash("Usuario creado.", "ok")
                return redirect(url_for("users"))
            except psycopg.errors.UniqueViolation:
                flash("Ese correo ya está registrado.", "error")
    return render_template("user_form.html", user=None, title="Nuevo usuario")


@app.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    with db() as conn:
        user = conn.execute("SELECT id,nombre,email,rol FROM usuarios WHERE id=%s", (user_id,)).fetchone()
    if not user:
        abort(404)
    if request.method == "POST":
        data = valid_user(request.form)
        if data:
            try:
                with db() as conn:
                    conn.execute("UPDATE usuarios SET nombre=%s,email=%s,rol=%s WHERE id=%s", (*data, user_id))
                flash("Usuario actualizado.", "ok")
                return redirect(url_for("users"))
            except psycopg.errors.UniqueViolation:
                flash("Ese correo ya está registrado.", "error")
    return render_template("user_form.html", user=user, title="Editar usuario")


@app.post("/usuarios/<int:user_id>/eliminar")
@login_required
def delete_user(user_id):
    with db() as conn:
        conn.execute("DELETE FROM usuarios WHERE id=%s", (user_id,))
    flash("Usuario eliminado.", "ok")
    return redirect(url_for("users"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
else:
    init_db()
