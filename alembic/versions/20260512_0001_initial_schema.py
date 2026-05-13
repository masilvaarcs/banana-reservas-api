"""initial schema

Revision ID: 20260512_0001
Revises:
Create Date: 2026-05-12 21:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260512_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "locais",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_index(op.f("ix_locais_id"), "locais", ["id"], unique=False)

    op.create_table(
        "salas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("local_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("capacidade", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["local_id"], ["locais.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("local_id", "nome", name="uq_salas_local_nome"),
    )
    op.create_index(op.f("ix_salas_id"), "salas", ["id"], unique=False)
    op.create_index(op.f("ix_salas_local_id"), "salas", ["local_id"], unique=False)

    op.create_table(
        "reservas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("local_id", sa.Integer(), nullable=False),
        sa.Column("sala_id", sa.Integer(), nullable=False),
        sa.Column("inicio", sa.DateTime(), nullable=False),
        sa.Column("fim", sa.DateTime(), nullable=False),
        sa.Column("responsavel", sa.String(length=120), nullable=False),
        sa.Column("cafe", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quantidade_pessoas", sa.Integer(), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("criado_por_email", sa.String(length=254), nullable=True),
        sa.CheckConstraint("fim > inicio", name="ck_reservas_periodo_valido"),
        sa.CheckConstraint(
            "(cafe = false) OR (quantidade_pessoas IS NOT NULL AND quantidade_pessoas > 0)",
            name="ck_reservas_cafe_qtd",
        ),
        sa.ForeignKeyConstraint(["local_id"], ["locais.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sala_id"], ["salas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reservas_id"), "reservas", ["id"], unique=False)
    op.create_index(op.f("ix_reservas_local_id"), "reservas", ["local_id"], unique=False)
    op.create_index(op.f("ix_reservas_sala_id"), "reservas", ["sala_id"], unique=False)
    op.create_index(
        "ix_reservas_local_sala_inicio_fim",
        "reservas",
        ["local_id", "sala_id", "inicio", "fim"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reservas_local_sala_inicio_fim", table_name="reservas")
    op.drop_index(op.f("ix_reservas_sala_id"), table_name="reservas")
    op.drop_index(op.f("ix_reservas_local_id"), table_name="reservas")
    op.drop_index(op.f("ix_reservas_id"), table_name="reservas")
    op.drop_table("reservas")

    op.drop_index(op.f("ix_salas_local_id"), table_name="salas")
    op.drop_index(op.f("ix_salas_id"), table_name="salas")
    op.drop_table("salas")

    op.drop_index(op.f("ix_locais_id"), table_name="locais")
    op.drop_table("locais")
