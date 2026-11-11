
from datetime import datetime
from app import db


class Pagamento(db.Model):
    __tablename__ = "pagamentos"

    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data_pagamento = db.Column(db.Date)
    forma_pagamento = db.Column(db.String(50))
    status = db.Column(db.String(30), default="Pendente")
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Dados preservados mesmo após excluir a encomenda
    cliente_nome = db.Column(db.String(150), nullable=True)
    encomenda_titulo = db.Column(db.String(150), nullable=True)

    # O pagamento continua pertencendo ao artista
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    # A encomenda pode ser excluída sem apagar o pagamento
    encomenda_id = db.Column(
        db.Integer,
        db.ForeignKey("encomendas.id", ondelete="SET NULL"),
        nullable=True
    )

    encomenda = db.relationship(
        "Encomenda",
        back_populates="pagamentos"
    )
