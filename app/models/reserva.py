from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Reserva(Base):
    __tablename__ = "reservas"
    __table_args__ = (
        CheckConstraint("fim > inicio", name="ck_reservas_periodo_valido"),
        CheckConstraint(
            "(cafe = 0) OR (quantidade_pessoas IS NOT NULL AND quantidade_pessoas > 0)",
            name="ck_reservas_cafe_qtd",
        ),
        Index("ix_reservas_local_sala_inicio_fim", "local_id", "sala_id", "inicio", "fim"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    local_id: Mapped[int] = mapped_column(ForeignKey("locais.id", ondelete="CASCADE"), index=True)
    sala_id: Mapped[int] = mapped_column(ForeignKey("salas.id", ondelete="CASCADE"), index=True)
    inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fim: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    responsavel: Mapped[str] = mapped_column(String(120), nullable=False)
    cafe: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quantidade_pessoas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_por_email: Mapped[str | None] = mapped_column(String(254), nullable=True)

    local: Mapped["Local"] = relationship("Local", back_populates="reservas")
    sala: Mapped["Sala"] = relationship("Sala", back_populates="reservas")
