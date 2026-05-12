# 🐍 banana-reservas-api

Serviço de gerenciamento de reservas de salas da **Banana Ltda.**

## 📋 Responsabilidade na Arquitetura

Este serviço é responsável pelo **CRUD de reservas, salas e locais**, além da **validação de conflitos de horário**. Todas as rotas são protegidas por JWT, que é emitido pelo `banana-auth-api` (C#) e validado localmente neste serviço usando o secret compartilhado.

```
[Frontend] → requisições de reserva + JWT → [banana-reservas-api]
                                                  ↓
                                    valida JWT com secret compartilhado
                                                  ↓
                                    processa a requisição
```

## 🛠️ Stack Tecnológica

| Tecnologia | Versão | Justificativa |
|---|---|---|
| Python | 3.11+ | Versão estável com melhorias de performance e tipagem |
| FastAPI | 0.111+ | Framework moderno, async-first, com Swagger automático e validação via Pydantic |
| SQLAlchemy | 2.x | ORM maduro e flexível, obrigatório conforme especificação |
| Alembic | 1.13+ | Gerenciamento de migrations para SQLAlchemy |
| PostgreSQL | Local | Banco relacional já disponível no ambiente de desenvolvimento |
| python-jose | 3.3+ | Biblioteca robusta para decodificação e validação de JWT |
| Pydantic v2 | incluso | Validação de dados e schemas tipados (incluso no FastAPI) |
| Uvicorn | 0.29+ | Servidor ASGI de alta performance para rodar o FastAPI |

## ✅ Pré-requisitos

- Python 3.11+
- PostgreSQL (local)
- VS Code + extensão Python (Pylance)

## ⚙️ Variáveis de Ambiente

Crie o arquivo `.env` na raiz do projeto (não commitado). Use `.env.example` como base:

```env
DATABASE_URL=postgresql://postgres:suasenha@localhost:5432/banana_reservas
JWT_SECRET=CHAVE_SECRETA_COMPARTILHADA_MINIMO_32_CHARS
JWT_ALGORITHM=HS256
JWT_ISSUER=banana-auth-service
JWT_AUDIENCE=banana-app
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

> ⚠️ **Importante:** O valor de `JWT_SECRET` deve ser **idêntico** ao `Jwt:Secret` configurado no `banana-auth-api`.

## 🚀 Como Rodar Localmente

```bash
# 1. Clonar o repositório
git clone https://github.com/seu-usuario/banana-reservas-api.git
cd banana-reservas-api

# 2. Criar e ativar o ambiente virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Criar o banco de dados no PostgreSQL
# (criar manualmente o banco 'banana_reservas' antes)

# 5. Aplicar migrations
alembic upgrade head

# 6. Rodar o servidor
uvicorn app.main:app --reload --port 8000

# A API estará disponível em:
# http://localhost:8000
# Swagger: http://localhost:8000/docs
```

## 📡 Endpoints

Todos os endpoints exigem header: `Authorization: Bearer <JWT>`

### Locais
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/locais` | Lista todos os locais |
| POST | `/api/locais` | Cria um local |
| PUT | `/api/locais/{id}` | Edita um local |
| DELETE | `/api/locais/{id}` | Remove um local |

### Salas
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/salas` | Lista todas as salas |
| GET | `/api/salas?local_id=xxx` | Filtra salas por local |
| POST | `/api/salas` | Cria uma sala |
| PUT | `/api/salas/{id}` | Edita uma sala |
| DELETE | `/api/salas/{id}` | Remove uma sala |

### Reservas
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/reservas` | Lista todas as reservas |
| POST | `/api/reservas` | Cria uma reserva (valida conflito) |
| PUT | `/api/reservas/{id}` | Edita uma reserva (valida conflito) |
| DELETE | `/api/reservas/{id}` | Remove uma reserva |
| DELETE | `/api/reservas/batch` | *(bônus)* Remove múltiplas reservas |

### Health
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/health` | Health check do serviço |

## ⚠️ Regra de Conflito de Horário

Uma reserva é bloqueada se, para a **mesma sala e local**, já existir outra reserva onde:

```
nova.inicio < existente.fim  AND  nova.fim > existente.inicio
```

Retorno em caso de conflito: **HTTP 409**
```json
{
  "error": "Conflito de horário",
  "detail": "A sala já está reservada neste período."
}
```

## 🔑 Validação do JWT

O token emitido pelo `banana-auth-api` é validado localmente usando o `JWT_SECRET` compartilhado. Nenhuma chamada HTTP ao serviço C# é necessária durante a validação.

## 📁 Estrutura do Projeto

```
banana-reservas-api/
├── app/
│   ├── main.py
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
├── alembic.ini
├── .env               ← não commitado
├── .env.example
├── requirements.txt
└── README.md
```
