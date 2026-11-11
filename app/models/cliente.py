
from app import db


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    observacoes = db.Column(db.Text)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    usuario = db.relationship(
        "User",
        back_populates="clientes"
    )

    encomendas = db.relationship(
    "Encomenda",
    back_populates="cliente",
    passive_deletes=True
)

    __table_args__ = (
        db.UniqueConstraint(
            "usuario_id",
            "email",
            name="uq_cliente_usuario_email"
        ),
    )
