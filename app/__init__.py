
import os
from flask import Flask, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    db.init_app(app)

    from app import models
    from app.routes.main import main
    from app.routes.clientes import clientes
    from app.routes.encomendas import encomendas
    from app.routes.pagamentos import pagamentos
    from app.routes.auth import auth

    app.register_blueprint(main)
    app.register_blueprint(clientes)
    app.register_blueprint(encomendas)
    app.register_blueprint(pagamentos)
    app.register_blueprint(auth)

    @app.before_request
    def exigir_login():
        if request.endpoint is None or request.endpoint == "static":
            return None

        if request.endpoint.startswith("auth."):
            return None

        if "usuario_id" not in session:
            return redirect(url_for("auth.login"))

    return app
