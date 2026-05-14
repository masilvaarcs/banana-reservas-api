"""
Configuração global de fixtures para os testes do banana-reservas-api.

IMPORTANTE: as variáveis de ambiente DEVEM ser definidas ANTES de qualquer
import de módulo da aplicação. O motivo: app/database.py chama get_settings()
em nível de módulo (ao ser importado), criando o engine imediatamente.
Como conftest.py é processado pelo pytest antes dos arquivos de teste, definir
os.environ aqui garante que os módulos da app vejam o banco de teste (SQLite)
em vez do PostgreSQL de produção.
"""

import os

# ── Variáveis de ambiente de teste (sobrescrevem .env durante os testes) ──────
# DATABASE_URL usa SQLite local para isolamento total: sem necessidade de
# PostgreSQL rodando, sem risco de contaminar dados reais.
os.environ["DATABASE_URL"] = "sqlite:///./banana_test.db"
os.environ["JWT_SECRET"] = "banana_test_secret_para_testes_unitarios_ok_32c"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ISSUER"] = "banana-auth-service"
os.environ["JWT_AUDIENCE"] = "banana-app"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

# ── Imports da aplicação (somente após definir as envs acima) ─────────────────
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import Base
from app.dependencies import get_db
from app.main import app

# ── Constantes usadas nos helpers de teste ────────────────────────────────────
_TEST_JWT_SECRET = os.environ["JWT_SECRET"]
_TEST_JWT_ISSUER = os.environ["JWT_ISSUER"]
_TEST_JWT_AUDIENCE = os.environ["JWT_AUDIENCE"]

# ── Engine SQLite — isolado, sem dependência de PostgreSQL ────────────────────
_engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    """Substitui a dependência get_db pelo banco SQLite de teste."""
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


def make_token(
    email: str = "test@banana.com",
    sub: str = "test-user-id-001",
) -> str:
    """
    Gera um JWT de teste válido, assinado com o mesmo secret configurado
    para a aplicação. Usado para autenticar requisições nos testes.
    """
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": sub,
            "email": email,
            "name": "Test User",
            "iss": _TEST_JWT_ISSUER,
            "aud": _TEST_JWT_AUDIENCE,
            "iat": now,
            "exp": now + timedelta(hours=1),
        },
        _TEST_JWT_SECRET,
        algorithm="HS256",
    )


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Cria todas as tabelas no SQLite no início da sessão de testes e as remove
    (junto com o arquivo .db) ao final. Roda automaticamente, sem precisar
    ser declarado nos testes.
    """
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)
    _engine.dispose()  # Libera conexões antes de remover o arquivo (necessário no Windows)
    db_path = "./banana_test.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass  # Arquivo ainda em uso — será limpo na próxima execução


@pytest.fixture(scope="module")
def client(setup_test_db):
    """
    TestClient do FastAPI com:
      - Dependência get_db substituída pelo banco SQLite de teste.
      - Funções de auto-migração do lifespan patchadas (desnecessárias com SQLite).

    Escopo 'module': um único cliente compartilhado por arquivo de teste.
    """
    app.dependency_overrides[get_db] = _override_get_db
    with (
        patch("app.main.ensure_database_exists"),
        patch("app.main.run_alembic_migrations"),
    ):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def auth_headers() -> dict[str, str]:
    """Header Authorization com JWT de teste válido."""
    return {"Authorization": f"Bearer {make_token()}"}
