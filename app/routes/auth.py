
import re

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import User

auth = Blueprint("auth", __name__)


@auth.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not nome or not email or not senha or not confirmar_senha:
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("auth.cadastro"))

        if senha != confirmar_senha:
            flash("As senhas não coincidem.", "error")
            return redirect(url_for("auth.cadastro"))

        # Verifica todos os requisitos da senha
        requisitos_faltantes = []

        if len(senha) < 8:
            requisitos_faltantes.append("No mínimo 8 caracteres")

        if not re.search(r"[A-Z]", senha):
            requisitos_faltantes.append("Uma letra maiúscula")

        if not re.search(r"[a-z]", senha):
            requisitos_faltantes.append("Uma letra minúscula")

        if not re.search(r"[0-9]", senha):
            requisitos_faltantes.append("Um número")

        if not re.search(r"[^a-zA-Z0-9]", senha):
            requisitos_faltantes.append("Um caractere especial (@, #, !)")

        if requisitos_faltantes:
            flash("||".join(requisitos_faltantes), "senha")
            return redirect(url_for("auth.cadastro"))

        if User.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "error")
            return redirect(url_for("auth.cadastro"))

        usuario = User(nome=nome, email=email)
        usuario.definir_senha(senha)

        db.session.add(usuario)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Este e-mail já está cadastrado.", "error")
            return redirect(url_for("auth.cadastro"))

        flash("Cadastro realizado com sucesso! Faça seu login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("cadastro.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        usuario = User.query.filter_by(email=email).first()

        if usuario and usuario.verificar_senha(senha):
            session.clear()
            session["usuario_id"] = usuario.id
            session["usuario_nome"] = usuario.nome

            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("encomendas.listar_encomendas"))

        flash("E-mail ou senha incorretos.", "error")

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "success")
    return redirect(url_for("auth.login"))
