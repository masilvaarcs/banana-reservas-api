import re

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

# A conexão é lazy; o app só tenta abrir socket quando realmente executa query.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_database_exists() -> None:
    """
    Cria o banco de dados PostgreSQL caso ainda não exista.

    Conecta ao banco de sistema 'postgres' e executa CREATE DATABASE se o banco
    configurado em DATABASE_URL não for encontrado. Necessário porque o Alembic
    (e o SQLAlchemy) não conseguem criar o banco em si — apenas as tabelas.
    """
    db_name = settings.database_url.split("/")[-1]
    # Substitui o nome do banco pelo banco de sistema 'postgres'
    system_url = re.sub(r"/[^/]+$", "/postgres", settings.database_url)

    system_engine = create_engine(system_url, isolation_level="AUTOCOMMIT")
    with system_engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": db_name},
        )
        if not result.fetchone():
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    system_engine.dispose()


def run_alembic_migrations() -> None:
    """
    Aplica todas as migrations Alembic pendentes (equivalente a 'alembic upgrade head').

    Importado aqui de forma lazy para evitar dependência circular na inicialização
    do módulo e para não carregar o Alembic em contextos que não precisam dele.
    """
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
