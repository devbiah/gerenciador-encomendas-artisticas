from datetime import datetime
from app import db


class ArquivoReferencia(db.Model):
    __tablename__ = "arquivos_referencia"

    id = db.Column(db.Integer, primary_key=True)

    nome_arquivo = db.Column(db.String(255), nullable=False)
    nome_original = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    encomenda_id = db.Column(
        db.Integer,
        db.ForeignKey("encomendas.id", ondelete="CASCADE"),
        nullable=False
    )

    encomenda = db.relationship(
        "Encomenda",
        back_populates="arquivos_referencia"
    )