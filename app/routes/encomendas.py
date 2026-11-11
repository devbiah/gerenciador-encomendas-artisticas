
import os
import uuid

from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import func
from werkzeug.utils import secure_filename

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app
)

from app import db
from app.models import (
    Encomenda,
    Cliente,
    Pagamento,
    ArquivoReferencia
)


encomendas = Blueprint("encomendas", __name__)

EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp"}


def obter_imagens_enviadas():
    return [
        arquivo
        for arquivo in request.files.getlist("imagens")
        if arquivo and arquivo.filename
    ]


def validar_imagens(imagens):
    for imagem in imagens:
        nome = secure_filename(imagem.filename)

        if not nome or "." not in nome:
            return False

        extensao = nome.rsplit(".", 1)[1].lower()

        if extensao not in EXTENSOES_PERMITIDAS:
            return False

    return True


def caminho_pasta_referencias():
    pasta = os.path.join(
        current_app.root_path,
        "static",
        "uploads",
        "referencias"
    )

    os.makedirs(pasta, exist_ok=True)

    return pasta


def salvar_imagens(encomenda, imagens):
    pasta = caminho_pasta_referencias()

    for imagem in imagens:
        nome_original = secure_filename(imagem.filename)
        extensao = nome_original.rsplit(".", 1)[1].lower()

        nome_arquivo = f"{uuid.uuid4().hex}.{extensao}"
        caminho = os.path.join(pasta, nome_arquivo)

        imagem.save(caminho)

        referencia = ArquivoReferencia(
            nome_arquivo=nome_arquivo,
            nome_original=nome_original,
            encomenda=encomenda
        )

        db.session.add(referencia)


def excluir_arquivo_referencia(arquivo):
    caminho = os.path.join(
        caminho_pasta_referencias(),
        arquivo.nome_arquivo
    )

    if os.path.isfile(caminho):
        os.remove(caminho)


def voltar_para_encomenda(id):
    return redirect(
        url_for("encomendas.detalhe_encomenda", id=id)
    )


# ==========================================
# LISTAR ENCOMENDAS
# ==========================================

@encomendas.route("/encomendas")
def listar_encomendas():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    todas = (
        Encomenda.query
        .filter_by(usuario_id=usuario_id)
        .all()
    )

    total = len(todas)

    em_andamento = sum(
        1 for e in todas
        if e.status == "Em andamento"
    )

    aguardando_pagamento = 0

    for encomenda in todas:
        pagamentos_confirmados = Pagamento.query.filter(
            Pagamento.encomenda_id == encomenda.id,
            Pagamento.usuario_id == usuario_id,
            func.lower(func.trim(Pagamento.status)).in_(
                ["pago", "parcial"]
            )
        ).all()

        encomenda.total_pago = sum(
            (
                Decimal(str(p.valor))
                for p in pagamentos_confirmados
            ),
            Decimal("0.00")
        )

        if encomenda.total_pago < Decimal(str(encomenda.valor)):
            aguardando_pagamento += 1

    busca = request.args.get("busca", "").strip()
    status_filtro = request.args.get("status", "")
    prazo_filtro = request.args.get("prazo", "")

    hoje = date.today()

    todas.sort(key=lambda e: e.prazo or date.max)

    if busca:
        termo = busca.casefold()

        todas = [
            e for e in todas
            if termo in (e.titulo or "").casefold()
            or (
                e.cliente
                and termo in e.cliente.nome.casefold()
            )
        ]

    if status_filtro:
        todas = [
            e for e in todas
            if e.status == status_filtro
        ]

    if prazo_filtro == "atrasadas":
        todas = [
            e for e in todas
            if e.prazo
            and e.prazo < hoje
            and e.status != "Concluída"
        ]

    elif prazo_filtro == "proximos7":
        limite = hoje + timedelta(days=7)

        todas = [
            e for e in todas
            if e.prazo
            and hoje <= e.prazo <= limite
            and e.status != "Concluída"
        ]

    elif prazo_filtro == "sem_prazo":
        todas = [
            e for e in todas
            if not e.prazo
        ]

    return render_template(
        "encomendas.html",
        encomendas=todas,
        total=total,
        em_andamento=em_andamento,
        aguardando_pagamento=aguardando_pagamento,
        busca=busca,
        status_filtro=status_filtro,
        prazo_filtro=prazo_filtro,
        hoje=hoje
    )


# ==========================================
# CADASTRAR NOVA ENCOMENDA
# ==========================================

@encomendas.route("/encomendas/nova", methods=["GET", "POST"])
def nova_encomenda():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    clientes = (
        Cliente.query
        .filter_by(usuario_id=usuario_id)
        .order_by(Cliente.nome)
        .all()
    )

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        observacoes = request.form.get("observacoes", "").strip()
        tipo = request.form.get("tipo", "").strip()
        valor_texto = request.form.get("valor", "").strip()
        prazo_texto = request.form.get("prazo", "")
        cliente_texto = request.form.get("cliente_id", "")
        status = request.form.get("status", "Pendente").strip()

        imagens = obter_imagens_enviadas()

        if not titulo or not valor_texto or not cliente_texto:
            flash("Preencha o título, o valor e o cliente.", "error")
            return redirect(url_for("encomendas.nova_encomenda"))

        if not validar_imagens(imagens):
            flash(
                "Envie somente imagens PNG, JPG, JPEG, GIF ou WEBP.",
                "error"
            )
            return redirect(url_for("encomendas.nova_encomenda"))

        try:
            valor = Decimal(valor_texto.replace(",", "."))
            cliente_id = int(cliente_texto)

            if not valor.is_finite() or valor <= 0:
                raise ValueError

            prazo = (
                datetime.strptime(prazo_texto, "%Y-%m-%d").date()
                if prazo_texto else None
            )

        except (InvalidOperation, ValueError):
            flash(
                "Verifique o valor, o cliente e a data informados.",
                "error"
            )
            return redirect(url_for("encomendas.nova_encomenda"))

        cliente = Cliente.query.filter_by(
            id=cliente_id,
            usuario_id=usuario_id
        ).first()

        if not cliente:
            flash("Cliente inválido.", "error")
            return redirect(url_for("encomendas.nova_encomenda"))

        if status not in ["Pendente", "Em andamento", "Concluída"]:
            status = "Pendente"

        encomenda = Encomenda(
            titulo=titulo,
            descricao=descricao,
            observacoes=observacoes,
            tipo=tipo,
            prazo=prazo,
            valor=valor,
            status=status,
            cliente_id=cliente.id,
            usuario_id=usuario_id
        )

        try:
            db.session.add(encomenda)
            db.session.flush()

            salvar_imagens(encomenda, imagens)

            db.session.commit()

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Erro ao cadastrar encomenda."
            )
            flash("Não foi possível cadastrar a encomenda.", "error")
            return redirect(url_for("encomendas.nova_encomenda"))

        flash("Encomenda cadastrada com sucesso!", "success")
        return redirect(url_for("encomendas.listar_encomendas"))

    return render_template(
        "nova_encomenda.html",
        clientes=clientes
    )


# ==========================================
# DETALHES E EDIÇÃO DA ENCOMENDA
# ==========================================

@encomendas.route("/encomendas/<int:id>", methods=["GET", "POST"])
def detalhe_encomenda(id):
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    encomenda = Encomenda.query.filter_by(
        id=id,
        usuario_id=usuario_id
    ).first_or_404()

    clientes = (
        Cliente.query
        .filter_by(usuario_id=usuario_id)
        .order_by(Cliente.nome)
        .all()
    )

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        observacoes = request.form.get("observacoes", "").strip()
        tipo = request.form.get("tipo", "").strip()
        valor_texto = request.form.get("valor", "").strip()
        prazo_texto = request.form.get("prazo", "")
        cliente_texto = request.form.get("cliente_id", "").strip()
        status = request.form.get("status", "").strip()

        imagens = obter_imagens_enviadas()

        if not titulo or not valor_texto:
            flash("Preencha o título e o valor.", "error")
            return voltar_para_encomenda(id)

        if not validar_imagens(imagens):
            flash(
                "Envie somente imagens PNG, JPG, JPEG, GIF ou WEBP.",
                "error"
            )
            return voltar_para_encomenda(id)

        try:
            valor = Decimal(valor_texto.replace(",", "."))

            if not valor.is_finite() or valor <= 0:
                raise ValueError

            prazo = (
                datetime.strptime(prazo_texto, "%Y-%m-%d").date()
                if prazo_texto else None
            )

        except (InvalidOperation, ValueError):
            flash("Verifique o valor e a data informados.", "error")
            return voltar_para_encomenda(id)

        cliente = None

        if cliente_texto:
            try:
                cliente_id = int(cliente_texto)
            except ValueError:
                flash("Cliente inválido.", "error")
                return voltar_para_encomenda(id)

            cliente = Cliente.query.filter_by(
                id=cliente_id,
                usuario_id=usuario_id
            ).first()

            if not cliente:
                flash("Cliente inválido.", "error")
                return voltar_para_encomenda(id)

        if status not in ["Pendente", "Em andamento", "Concluída"]:
            flash("Status inválido.", "error")
            return voltar_para_encomenda(id)

        try:
            encomenda.titulo = titulo
            encomenda.descricao = descricao
            encomenda.observacoes = observacoes
            encomenda.tipo = tipo
            encomenda.valor = valor
            encomenda.prazo = prazo
            encomenda.cliente_id = cliente.id if cliente else None
            encomenda.status = status

            salvar_imagens(encomenda, imagens)

            pagamentos_vinculados = Pagamento.query.filter_by(
                encomenda_id=encomenda.id,
                usuario_id=usuario_id
            ).all()

            for pagamento in pagamentos_vinculados:
                pagamento.encomenda_titulo = titulo
                pagamento.cliente_nome = (
                    cliente.nome if cliente else "Cliente excluído"
                )

            db.session.commit()

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Erro ao atualizar encomenda."
            )
            flash("Não foi possível atualizar a encomenda.", "error")
            return voltar_para_encomenda(id)

        flash("Encomenda atualizada com sucesso!", "success")
        return redirect(url_for("encomendas.listar_encomendas"))

    pagamentos_confirmados = Pagamento.query.filter(
        Pagamento.encomenda_id == encomenda.id,
        Pagamento.usuario_id == usuario_id,
        func.lower(func.trim(Pagamento.status)).in_(
            ["pago", "parcial"]
        )
    ).all()

    total_pago = sum(
        (
            Decimal(str(p.valor))
            for p in pagamentos_confirmados
        ),
        Decimal("0.00")
    )

    saldo_restante = max(
        Decimal("0.00"),
        Decimal(str(encomenda.valor)) - total_pago
    )

    return render_template(
        "detalhe_encomenda.html",
        encomenda=encomenda,
        clientes=clientes,
        total_pago=total_pago,
        saldo_restante=saldo_restante
    )


# ==========================================
# EXCLUIR IMAGEM DE REFERÊNCIA
# ==========================================

@encomendas.route(
    "/encomendas/<int:id>/referencia/<int:arquivo_id>/excluir",
    methods=["POST"]
)
def excluir_referencia(id, arquivo_id):
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    encomenda = Encomenda.query.filter_by(
        id=id,
        usuario_id=usuario_id
    ).first_or_404()

    arquivo = ArquivoReferencia.query.filter_by(
        id=arquivo_id,
        encomenda_id=encomenda.id
    ).first_or_404()

    try:
        excluir_arquivo_referencia(arquivo)

        db.session.delete(arquivo)
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Erro ao excluir imagem de referência."
        )
        flash("Não foi possível excluir a imagem.", "error")
        return voltar_para_encomenda(id)

    flash("Imagem de referência excluída.", "success")

    return voltar_para_encomenda(id)


# ==========================================
# EXCLUIR ENCOMENDA
# ==========================================

@encomendas.route("/encomendas/<int:id>/excluir", methods=["POST"])
def excluir_encomenda(id):
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("auth.login"))

    encomenda = Encomenda.query.filter_by(
        id=id,
        usuario_id=usuario_id
    ).first_or_404()

    try:
        for arquivo in encomenda.arquivos_referencia:
            excluir_arquivo_referencia(arquivo)

        db.session.delete(encomenda)
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Erro ao excluir encomenda."
        )
        flash("Não foi possível excluir a encomenda.", "error")
        return voltar_para_encomenda(id)

    flash(
        "Encomenda excluída com sucesso! Os pagamentos foram preservados.",
        "success"
    )

    return redirect(url_for("encomendas.listar_encomendas"))
