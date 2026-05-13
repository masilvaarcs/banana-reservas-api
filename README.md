# 🐍 banana-reservas-api

Serviço de gerenciamento de reservas de salas da Banana Ltda.

## 📋 Responsabilidade na Arquitetura

Este serviço é responsável pelo CRUD de reservas, salas e locais, além da validação de conflitos de horário. Todas as rotas de negócio são protegidas por JWT emitido no banana-auth-api.

```text
[Frontend] -> requisições de reserva + JWT -> [banana-reservas-api]
                                               -> valida JWT localmente
                                               -> processa requisição
```

## 📦 Estrutura de Repositórios

Este repositório é independente e representa apenas o Projeto 2 (banana-reservas-api).

- Não existe solução única carregando os 3 projetos.
- A execução é isolada por ambiente Python local.
- A integração com o Projeto 1 acontece por JWT compartilhado via variável de ambiente.

## 🛠️ Stack Tecnológica

| Tecnologia | Versão | Justificativa |
| --- | --- | --- |
| Python | 3.11+ | Versão estável e aderente ao desafio |
| FastAPI | 0.111.0 | API REST com validação automática e Swagger nativo |
| SQLAlchemy | 2.0.44 | ORM obrigatório no desafio |
| Alembic | 1.16.5 | Versionamento de schema relacional |
| PostgreSQL | Local | Banco relacional obrigatório |
| python-jose | 3.3.0 | Validação local de JWT |
| Uvicorn | 0.30.1 | Servidor ASGI para execução da API |

## ✅ Pré-requisitos

- Python 3.11+
- PostgreSQL local
- VS Code com extensão Python

## ⚙️ Variáveis de Ambiente

Crie o arquivo .env na raiz do projeto (não commitar), usando .env.example:

```env
DATABASE_URL=postgresql://postgres:suasenha@localhost:5432/banana_reservas
JWT_SECRET=CHAVE_SECRETA_COMPARTILHADA_MINIMO_32_CHARS
JWT_ALGORITHM=HS256
JWT_ISSUER=banana-auth-service
JWT_AUDIENCE=banana-app
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Importante: JWT_SECRET deve ser exatamente o mesmo valor configurado em Jwt:Secret do Projeto 1.

## 🚀 Como Rodar Localmente

```bash
# 1) entrar na pasta do projeto
cd banana-reservas-api

# 2) criar e ativar ambiente virtual
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1

# 3) instalar dependências
pip install -r requirements.txt

# 4) aplicar migrations
alembic upgrade head

# 5) subir API
uvicorn app.main:app --reload --port 8000
```

Endpoints locais:

- API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- Health: <http://localhost:8000/api/health>

## 🔐 JWT e Integração com Projeto 1

O fluxo de autenticação é:

1. Frontend autentica no banana-auth-api.
2. Recebe JWT no login.
3. Envia `Authorization: Bearer TOKEN_JWT` nas rotas deste serviço.
4. Este serviço valida token localmente com JWT_SECRET, JWT_ISSUER e JWT_AUDIENCE.

Não há chamada HTTP do serviço Python para o serviço C# durante a validação.

## 📡 Endpoints

Todos os endpoints abaixo exigem `Authorization: Bearer TOKEN_JWT`, exceto /api/health.

### Locais

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | /api/locais | Lista locais |
| POST | /api/locais | Cria local |
| PUT | /api/locais/{id} | Atualiza local |
| DELETE | /api/locais/{id} | Remove local |

### Salas

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | /api/salas | Lista salas |
| GET | /api/salas?local_id={id} | Filtra salas por local |
| POST | /api/salas | Cria sala |
| PUT | /api/salas/{id} | Atualiza sala |
| DELETE | /api/salas/{id} | Remove sala |

### Reservas

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | /api/reservas | Lista reservas |
| POST | /api/reservas | Cria reserva com validação de conflito |
| PUT | /api/reservas/{id} | Atualiza reserva com validação de conflito |
| DELETE | /api/reservas/{id} | Remove reserva |
| DELETE | /api/reservas/batch | Remove reservas em lote (bônus) |

#### DELETE /api/reservas/batch

Requisição:
```json
{
  "reserva_ids": [1, 2, 3]
}
```

Resposta (200 OK):
```json
{
  "deleted_count": 3
}
```

## ⚠️ Regra de Conflito de Horário

A reserva é bloqueada quando já existe, para a mesma sala e local, um intervalo que se sobrepõe:

```text
novo.inicio < existente.fim AND novo.fim > existente.inicio
```

Em caso de conflito, retorno HTTP 409:

```json
{
  "error": "Conflito de horário",
  "detail": "A sala já está reservada neste período."
}
```

## 📁 Estrutura do Projeto

```text
banana-reservas-api/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── models/
│   │   ├── local.py
│   │   ├── sala.py
│   │   └── reserva.py
│   ├── schemas/
│   │   ├── local.py
│   │   ├── sala.py
│   │   └── reserva.py
│   ├── routers/
│   │   ├── locais.py
│   │   ├── salas.py
│   │   └── reservas.py
│   └── services/
│       ├── auth.py
│       └── reserva_service.py
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```
