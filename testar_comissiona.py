# -*- coding: utf-8 -*-
"""
Testes automatizados do Comissiona.
Usa SQLite em memoria: nao altera o banco PostgreSQL configurado no .env.
Execute com: python testar_comissiona.py
"""

import os
import sys
import unittest
from decimal import Decimal
from sqlalchemy import func

# Define o banco temporario ANTES de importar o app.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "chave-temporaria-apenas-para-testes"

try:
    from app import create_app, db
    from app.models import User, Cliente, Encomenda, Pagamento
except ModuleNotFoundError as erro:
    print("\nDependencia ausente:", erro)
    print("Execute: python -m pip install Flask Flask-SQLAlchemy python-dotenv")
    sys.exit(2)


class TestesComissiona(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            SECRET_KEY="chave-temporaria-apenas-para-testes",
        )
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        # Fecha a conexao do SQLite em memoria ao terminar os testes.
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.session.remove()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def criar_usuario(self, email="artista@teste.com", nome="Artista"):
        usuario = User(nome=nome, email=email)
        usuario.definir_senha("SenhaTeste1!")
        db.session.add(usuario)
        db.session.commit()
        return usuario

    def logar_como(self, usuario):
        with self.client.session_transaction() as sess:
            sess["usuario_id"] = usuario.id
            sess["usuario_nome"] = usuario.nome

    def criar_cliente(self, usuario, nome="Cliente Teste", email="cliente@teste.com"):
        cliente = Cliente(
            nome=nome,
            email=email,
            usuario_id=usuario.id,
        )
        db.session.add(cliente)
        db.session.commit()
        return cliente

    def criar_encomenda(self, usuario, cliente, titulo="Ilustracao teste", valor="100.00"):
        encomenda = Encomenda(
            titulo=titulo,
            descricao="Descricao de teste",
            tipo="Ilustracao",
            valor=Decimal(valor),
            status="Pendente",
            cliente_id=cliente.id,
            usuario_id=usuario.id,
        )
        db.session.add(encomenda)
        db.session.commit()
        return encomenda

    def criar_pagamento(self, usuario, encomenda, valor, status="Pago"):
        pagamento = Pagamento(
            valor=Decimal(valor),
            status=status,
            usuario_id=usuario.id,
            encomenda_id=encomenda.id,
            cliente_nome=encomenda.cliente.nome,
            encomenda_titulo=encomenda.titulo,
        )
        db.session.add(pagamento)
        db.session.commit()
        return pagamento

    def test_01_paginas_internas_exigem_login(self):
        resposta = self.client.get("/clientes")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login", resposta.location)

    def test_02_cadastro_login_e_logout(self):
        resposta = self.client.post("/cadastro", data={
            "nome": "Artista Um",
            "email": "um@teste.com",
            "senha": "SenhaForte1!",
            "confirmar_senha": "SenhaForte1!",
        }, follow_redirects=True)
        self.assertEqual(resposta.status_code, 200)

        usuario = User.query.filter_by(email="um@teste.com").first()
        self.assertIsNotNone(usuario)
        self.assertTrue(usuario.verificar_senha("SenhaForte1!"))

        resposta_login = self.client.post("/login", data={
            "email": "um@teste.com",
            "senha": "SenhaForte1!",
        })
        self.assertEqual(resposta_login.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertIn("usuario_id", sess)

        resposta_logout = self.client.get("/logout")
        self.assertEqual(resposta_logout.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertNotIn("usuario_id", sess)

    def test_03_cliente_cadastrar_editar_e_excluir(self):
        usuario = self.criar_usuario()
        self.logar_como(usuario)

        resposta = self.client.post("/clientes/novo", data={
            "nome": "Maria Cliente",
            "email": "maria@teste.com",
            "telefone": "49999999999",
            "observacoes": "Cliente de teste",
        })
        self.assertEqual(resposta.status_code, 302)

        cliente = Cliente.query.filter_by(email="maria@teste.com").first()
        self.assertIsNotNone(cliente)

        resposta_edicao = self.client.post(
            f"/clientes/{cliente.id}/editar",
            data={
                "nome": "Maria Atualizada",
                "email": "maria@teste.com",
                "telefone": "48888888888",
                "observacoes": "Atualizado",
            },
        )
        self.assertEqual(resposta_edicao.status_code, 302)
        db.session.refresh(cliente)
        self.assertEqual(cliente.nome, "Maria Atualizada")

        cliente_id = cliente.id
        resposta_exclusao = self.client.post(f"/clientes/{cliente_id}/excluir")
        self.assertEqual(resposta_exclusao.status_code, 302)
        self.assertIsNone(db.session.get(Cliente, cliente_id))

    def test_04_encomenda_cadastrar_editar_filtrar_e_excluir(self):
        usuario = self.criar_usuario()
        cliente = self.criar_cliente(usuario)
        self.logar_como(usuario)

        resposta = self.client.post("/encomendas/nova", data={
            "titulo": "Retrato inicial",
            "cliente_id": str(cliente.id),
            "descricao": "Retrato de personagem",
            "tipo": "Meio corpo",
            "prazo": "",
            "valor": "150.00",
            "status": "Pendente",
        })
        self.assertEqual(resposta.status_code, 302)

        encomenda = Encomenda.query.filter_by(titulo="Retrato inicial").first()
        self.assertIsNotNone(encomenda)
        self.assertEqual(encomenda.valor, Decimal("150.00"))

        resposta_filtro = self.client.get("/encomendas?busca=Retrato")
        self.assertEqual(resposta_filtro.status_code, 200)
        self.assertIn(b"Retrato inicial", resposta_filtro.data)

        resposta_edicao = self.client.post(
            f"/encomendas/{encomenda.id}",
            data={
                "titulo": "Retrato atualizado",
                "cliente_id": str(cliente.id),
                "descricao": "Descricao alterada",
                "tipo": "Completo",
                "prazo": "",
                "valor": "180.00",
                "status": "Em andamento",
            },
        )
        self.assertEqual(resposta_edicao.status_code, 302)
        db.session.refresh(encomenda)
        self.assertEqual(encomenda.titulo, "Retrato atualizado")
        self.assertEqual(encomenda.valor, Decimal("180.00"))

        encomenda_id = encomenda.id
        resposta_exclusao = self.client.post(
            f"/encomendas/{encomenda_id}/excluir"
        )
        self.assertEqual(resposta_exclusao.status_code, 302)
        self.assertIsNone(db.session.get(Encomenda, encomenda_id))

    def test_05_pagamentos_parciais_somam_corretamente_na_encomenda(self):
        usuario = self.criar_usuario()
        cliente = self.criar_cliente(usuario)
        encomenda = self.criar_encomenda(usuario, cliente, valor="100.00")
        self.criar_pagamento(usuario, encomenda, "30.00", "Pago")
        self.criar_pagamento(usuario, encomenda, "20.00", "Parcial")
        self.criar_pagamento(usuario, encomenda, "10.00", "Pendente")
        self.logar_como(usuario)

        resposta = self.client.get(f"/encomendas/{encomenda.id}")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"50.00", resposta.data)

        resposta_lista = self.client.get("/encomendas")
        self.assertEqual(resposta_lista.status_code, 200)
        self.assertIn(b"50.00", resposta_lista.data)

    def test_06_pagina_de_pagamentos_calcula_totais(self):
        usuario = self.criar_usuario()
        cliente = self.criar_cliente(usuario)
        encomenda = self.criar_encomenda(usuario, cliente, valor="100.00")
        self.criar_pagamento(usuario, encomenda, "30.00", "Pago")
        self.criar_pagamento(usuario, encomenda, "20.00", "Parcial")
        self.criar_pagamento(usuario, encomenda, "10.00", "Pendente")
        self.logar_como(usuario)

        resposta = self.client.get("/pagamentos")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Cliente Teste", resposta.data)
        self.assertIn(b"Ilustracao teste", resposta.data)

        totais = (
            db.session.query(func.sum(Pagamento.valor))
            .filter_by(usuario_id=usuario.id)
            .scalar()
        )
        self.assertEqual(totais, Decimal("60.00"))

    def test_07_nao_permite_usar_cliente_de_outro_artista(self):
        usuario_a = self.criar_usuario("a@teste.com", "Artista A")
        usuario_b = self.criar_usuario("b@teste.com", "Artista B")
        cliente_b = self.criar_cliente(
            usuario_b, "Cliente B", "cliente-b@teste.com"
        )
        self.logar_como(usuario_a)

        resposta = self.client.post("/encomendas/nova", data={
            "titulo": "Pedido indevido",
            "cliente_id": str(cliente_b.id),
            "valor": "100.00",
            "status": "Pendente",
        }, follow_redirects=True)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            Encomenda.query.filter_by(titulo="Pedido indevido").count(), 0
        )

    def test_08_artista_nao_acessa_encomenda_de_outro_artista(self):
        usuario_a = self.criar_usuario("a@teste.com", "Artista A")
        usuario_b = self.criar_usuario("b@teste.com", "Artista B")
        cliente_b = self.criar_cliente(
            usuario_b, "Cliente B", "cliente-b@teste.com"
        )
        encomenda_b = self.criar_encomenda(usuario_b, cliente_b)
        self.logar_como(usuario_a)

        resposta = self.client.get(f"/encomendas/{encomenda_b.id}")
        self.assertEqual(resposta.status_code, 404)

    def test_09_pagamento_nao_pode_ser_criado_para_encomenda_de_outro_artista(self):
        usuario_a = self.criar_usuario("a@teste.com", "Artista A")
        usuario_b = self.criar_usuario("b@teste.com", "Artista B")
        cliente_b = self.criar_cliente(
            usuario_b, "Cliente B", "cliente-b@teste.com"
        )
        encomenda_b = self.criar_encomenda(usuario_b, cliente_b)
        self.logar_como(usuario_a)

        resposta = self.client.post("/pagamentos/novo", data={
            "encomenda_id": str(encomenda_b.id),
            "valor": "25.00",
            "status": "Pago",
        }, follow_redirects=True)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Pagamento.query.count(), 0)

    def test_10_pagamento_parcial_e_preservado_ao_excluir_encomenda(self):
        usuario = self.criar_usuario()
        cliente = self.criar_cliente(usuario)
        encomenda = self.criar_encomenda(usuario, cliente)
        pagamento = self.criar_pagamento(usuario, encomenda, "25.00", "Pago")
        pagamento_id = pagamento.id
        self.logar_como(usuario)

        resposta = self.client.post(
            f"/encomendas/{encomenda.id}/excluir"
        )
        self.assertEqual(resposta.status_code, 302)

        pagamento_preservado = db.session.get(Pagamento, pagamento_id)
        self.assertIsNotNone(pagamento_preservado)
        self.assertEqual(pagamento_preservado.valor, Decimal("25.00"))

    def test_11_cadastrar_e_excluir_pagamento_pela_interface(self):
        usuario = self.criar_usuario()
        cliente = self.criar_cliente(usuario)
        encomenda = self.criar_encomenda(usuario, cliente)
        self.logar_como(usuario)

        resposta = self.client.post("/pagamentos/novo", data={
            "encomenda_id": str(encomenda.id),
            "valor": "35.50",
            "data_pagamento": "",
            "forma_pagamento": "Pix",
            "status": "Pago",
            "observacoes": "Pagamento de teste",
        })
        self.assertEqual(resposta.status_code, 302)

        pagamento = Pagamento.query.filter_by(
            encomenda_id=encomenda.id
        ).first()
        self.assertIsNotNone(pagamento)
        self.assertEqual(pagamento.valor, Decimal("35.50"))
        self.assertEqual(pagamento.cliente_nome, cliente.nome)
        self.assertEqual(pagamento.encomenda_titulo, encomenda.titulo)

        resposta_exclusao = self.client.post(
            f"/pagamentos/{pagamento.id}/excluir"
        )
        self.assertEqual(resposta_exclusao.status_code, 302)
        self.assertIsNone(db.session.get(Pagamento, pagamento.id))


if __name__ == "__main__":
    print("\n======================================")
    print("       TESTES AUTOMATIZADOS")
    print("             COMISSIONA")
    print("======================================\n")
    resultado = unittest.main(verbosity=2, exit=False)
    total = resultado.result.testsRun
    falhas = len(resultado.result.failures)
    erros = len(resultado.result.errors)
    ignorados = len(resultado.result.skipped)
    aprovados = total - falhas - erros - ignorados

    print("\n======================================")
    print("             RESULTADO")
    print("======================================")
    print(f"Testes executados: {total}")
    print(f"Aprovados:         {aprovados}")
    print(f"Falhas:            {falhas}")
    print(f"Erros:             {erros}")
    print(f"Ignorados:         {ignorados}")
    if falhas or erros:
        print("\nO Comissiona precisa de ajustes nos itens que falharam.")
    else:
        print("\nTodos os testes automatizados passaram!")
    print("======================================")
