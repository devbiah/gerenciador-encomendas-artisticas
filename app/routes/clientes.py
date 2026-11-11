
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Cliente, Pagamento

clientes = Blueprint("clientes", __name__)


@clientes.route("/clientes")
def listar_clientes():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    lista = (
        Cliente.query
        .filter_by(usuario_id=usuario_id)
        .order_by(Cliente.nome)
        .all()
    )

    return render_template("clientes.html", clientes=lista)


@clientes.route("/clientes/novo", methods=["GET", "POST"])
def novo_cliente():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        telefone = request.form.get("telefone", "").strip() or None
        observacoes = request.form.get("observacoes", "").strip()

        if not nome or not email:
            flash("Preencha o nome e o e-mail do cliente.", "error")
            return redirect(url_for("clientes.novo_cliente"))

        cliente = Cliente(
            nome=nome,
            email=email,
            telefone=telefone,
            observacoes=observacoes,
            usuario_id=usuario_id
        )

        db.session.add(cliente)

        try:
            db.session.commit()
            flash("Cliente cadastrado com sucesso!", "success")
            return redirect(url_for("clientes.listar_clientes"))

        except IntegrityError:
            db.session.rollback()
            flash("Você já possui um cliente cadastrado com esse e-mail.", "error")

    return render_template("novo_cliente.html")


@clientes.route("/clientes/<int:id>/editar", methods=["GET", "POST"])
def editar_cliente(id):
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    cliente = Cliente.query.filter_by(
        id=id,
        usuario_id=usuario_id
    ).first_or_404()

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        telefone = request.form.get("telefone", "").strip() or None
        observacoes = request.form.get("observacoes", "").strip()

        if not nome or not email:
            flash("Preencha o nome e o e-mail do cliente.", "error")
            return redirect(
                url_for("clientes.editar_cliente", id=id)
            )

        # Guarda o nome antigo antes de atualizar o cadastro
        nome_anterior = cliente.nome

        cliente.nome = nome
        cliente.email = email
        cliente.telefone = telefone
        cliente.observacoes = observacoes

        # Atualiza o nome nos pagamentos que tinham o nome antigo
        pagamentos_vinculados = Pagamento.query.filter_by(
            cliente_nome=nome_anterior,
            usuario_id=usuario_id
        ).all()

        for pagamento in pagamentos_vinculados:
            pagamento.cliente_nome = nome

        try:
            db.session.commit()
            flash("Cliente atualizado com sucesso!", "success")
            return redirect(url_for("clientes.listar_clientes"))

        except IntegrityError:
            db.session.rollback()
            flash("Já existe um cliente com esse e-mail na sua conta.", "error")

    return render_template("novo_cliente.html", cliente=cliente)


@clientes.route("/clientes/<int:id>/excluir", methods=["POST"])
def excluir_cliente(id):
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    cliente = Cliente.query.filter_by(
        id=id,
        usuario_id=usuario_id
    ).first_or_404()

    db.session.delete(cliente)
    db.session.commit()

    flash(
        "Cliente excluído. As encomendas vinculadas foram preservadas.",
        "success"
    )

    return redirect(url_for("clientes.listar_clientes"))
