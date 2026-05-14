"""
Setup standalone do banco de dados para o banana-reservas-api.

Uso:
    python scripts/setup_db.py

Cria o banco PostgreSQL configurado em DATABASE_URL (caso não exista) e aplica
todas as migrations Alembic pendentes. Útil para CI/CD ou setup inicial após
clonar o repositório, sem precisar subir o servidor uvicorn.

Nota: ao iniciar normalmente com `uvicorn app.main:app`, o lifespan da aplicação
executa o mesmo procedimento automaticamente.
"""

import os
import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path para os imports de `app.*`
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# O Alembic procura alembic.ini no CWD; precisamos estar na raiz do projeto
os.chdir(ROOT)


def main() -> None:
    from app.database import ensure_database_exists, run_alembic_migrations

    print("[setup_db] Verificando/criando banco de dados...")
    try:
        ensure_database_exists()
        print("[setup_db] Banco OK.")
    except Exception as exc:
        print(f"[setup_db] ERRO ao criar banco: {exc}")
        print("[setup_db] Verifique DATABASE_URL no arquivo .env e se o PostgreSQL está acessível.")
        sys.exit(1)

    print("[setup_db] Aplicando migrations Alembic...")
    try:
        run_alembic_migrations()
        print("[setup_db] Migrations aplicadas com sucesso.")
    except Exception as exc:
        print(f"[setup_db] ERRO ao aplicar migrations: {exc}")
        sys.exit(1)

    print("[setup_db] Concluído. Execute `uvicorn app.main:app --reload --port 8000` para iniciar.")


if __name__ == "__main__":
    main()
