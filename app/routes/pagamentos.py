
from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app import db
from app.models import Pagamento, Encomenda

pagamentos = Blueprint("pagamentos", __name__)


@pagamentos.route("/pagamentos")
def listar_pagamentos():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    consulta = Pagamento.query.filter_by(usuario_id=usuario_id)

    lista = consulta.order_by(
        Pagamento.criado_em.desc()
    ).all()

    # Atualiza os nomes e títulos usando os dados atuais das encomendas
    houve_atualizacao = False

    for pagamento in lista:
        if pagamento.encomenda_id:
            encomenda = Encomenda.query.filter_by(
                id=pagamento.encomenda_id,
                usuario_id=usuario_id
            ).first()

            if encomenda:
                nome_atual = (
                    encomenda.cliente.nome
                    if encomenda.cliente
                    else "Cliente excluído"
                )

                if pagamento.cliente_nome != nome_atual:
                    pagamento.cliente_nome = nome_atual
                    houve_atualizacao = True

                if pagamento.encomenda_titulo != encomenda.titulo:
                    pagamento.encomenda_titulo = encomenda.titulo
                    houve_atualizacao = True

    if houve_atualizacao:
        db.session.commit()

    total_recebido = consulta.filter(
        func.lower(func.trim(Pagamento.status)).in_(["pago", "parcial"])
    ).with_entities(
        func.sum(Pagamento.valor)
    ).scalar() or Decimal("0.00")

    total_pendente = consulta.filter(
        func.lower(func.trim(Pagamento.status)) == "pendente"
    ).with_entities(
        func.sum(Pagamento.valor)
    ).scalar() or Decimal("0.00")

    total_geral = consulta.with_entities(
        func.sum(Pagamento.valor)
    ).scalar() or Decimal("0.00")

    return render_template(
        "pagamentos.html",
        pagamentos=lista,
        total_recebido=total_recebido,
        total_pendente=total_pendente,
        total_geral=total_geral
    )


@pagamentos.route("/pagamentos/novo", methods=["GET", "POST"])
def novo_pagamento():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    encomendas = Encomenda.query.filter_by(
        usuario_id=usuario_id
    ).order_by(
        Encomenda.titulo
    ).all()

    if request.method == "POST":
        valor_texto = request.form.get("valor", "").strip().replace(",", ".")
        data_texto = request.form.get("data_pagamento", "")
        encomenda_texto = request.form.get("encomenda_id", "")

        forma_pagamento = request.form.get("forma_pagamento", "").strip()
        status = request.form.get("status", "Pendente").strip()
        observacoes = request.form.get("observacoes", "").strip()

        try:
            valor = Decimal(valor_texto)
            encomenda_id = int(encomenda_texto)

            if not valor.is_finite() or valor <= 0:
                raise ValueError

            data_pagamento = (
                datetime.strptime(data_texto, "%Y-%m-%d").date()
                if data_texto else None
            )

        except (InvalidOperation, ValueError):
            flash("Verifique o valor, a data e a encomenda informados.", "error")
            return redirect(url_for("pagamentos.novo_pagamento"))

        encomenda = Encomenda.query.filter_by(
            id=encomenda_id,
            usuario_id=usuario_id
        ).first()

        if not encomenda:
            flash("Encomenda inválida.", "error")
            return redirect(url_for("pagamentos.novo_pagamento"))

        pagamento = Pagamento(
            valor=valor,
            data_pagamento=data_pagamento,
            forma_pagamento=forma_pagamento,
            status=status,
            observacoes=observacoes,
            usuario_id=usuario_id,
            encomenda_id=encomenda.id,
            cliente_nome=(
                encomenda.cliente.nome
                if encomenda.cliente else "Cliente excluído"
            ),
            encomenda_titulo=encomenda.titulo
        )

        db.session.add(pagamento)
        db.session.commit()

        flash("Pagamento cadastrado com sucesso!", "success")
        return redirect(url_for("pagamentos.listar_pagamentos"))

    return render_template(
        "novo_pagamento.html",
        encomendas=encomendas
    )


@pagamentos.route("/pagamentos/<int:id>/excluir", methods=["POST"])
def excluir_pagamento(id):
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    pagamento = Pagamento.query.filter_by(
        id=id,
        usuario_id=usuario_id
    ).first_or_404()

    db.session.delete(pagamento)
    db.session.commit()

    flash("Pagamento excluído com sucesso!", "success")

    return redirect(url_for("pagamentos.listar_pagamentos"))
