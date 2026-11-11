# Comissiona — Sistema Web para Gerenciamento de Encomendas Artísticas

Projeto acadêmico desenvolvido na disciplina de Projeto de Software, com o objetivo de criar um sistema web para auxiliar artistas independentes na organização e no gerenciamento de encomendas artísticas.

## Objetivo

Facilitar o controle de clientes, encomendas, prazos, referências e pagamentos, centralizando as informações em um único ambiente.

## Funcionalidades

- Cadastro, consulta, edição e exclusão de clientes.
- Cadastro e gerenciamento de encomendas artísticas.
- Acompanhamento de prazos e status de produção.
- Upload e organização de imagens de referência.
- Controle de pagamentos e valores recebidos.
- Acompanhamento de valores pendentes por encomenda.
- Autenticação de usuários.

## Tecnologias utilizadas

- Python
- Flask 3.x
- Flask-SQLAlchemy
- SQLAlchemy
- HTML5
- CSS3
- PostgreSQL

## Arquitetura

O sistema utiliza arquitetura monolítica em camadas, separando as responsabilidades entre modelos, rotas, templates e arquivos estáticos, facilitando a manutenção e a evolução da aplicação.

## Estrutura do projeto

```text
gerenciador-encomendas-artisticas/
│
├── app/
│   ├── models/
│   ├── routes/
│   ├── templates/
│   ├── static/
│   │   ├── css/
│   │   └── uploads/
│   └── __init__.py
│
├── config.py
├── run.py
└── requirements.txt
```

## Como executar o projeto

1. Clone este repositório.
2. Acesse a pasta do projeto.
3. Crie e ative um ambiente virtual.
4. Instale as dependências:

```bash
pip install -r requirements.txt
```

5. Configure a conexão com o banco de dados.
6. Execute a aplicação:

```bash
python run.py
```

7. Acesse pelo navegador:

```text
http://127.0.0.1:5000
```

## Status do projeto

Em desenvolvimento.

## Licença

Projeto acadêmico sem licença de reutilização. Todos os direitos reservados à autora.
