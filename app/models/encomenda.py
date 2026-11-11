from datetime import datetime
from app import db


class Encomenda(db.Model):
    __tablename__ = "encomendas"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    tipo = db.Column(db.String(50))
    prazo = db.Column(db.Date)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(30), default="Pendente")

    # Mantida para compatibilidade com registros antigos.
    referencias = db.Column(db.Text)

    criada_em = db.Column(db.DateTime, default=datetime.utcnow)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True
    )

    cliente = db.relationship(
        "Cliente",
        back_populates="encomendas"
    )

    pagamentos = db.relationship(
        "Pagamento",
        back_populates="encomenda",
        passive_deletes=True
    )

    arquivos_referencia = db.relationship(
        "ArquivoReferencia",
        back_populates="encomenda",
        cascade="all, delete-orphan",
        passive_deletes=True
    )