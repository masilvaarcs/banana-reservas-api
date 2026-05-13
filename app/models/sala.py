from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sala(Base):
    __tablename__ = "salas"
    __table_args__ = (UniqueConstraint("local_id", "nome", name="uq_salas_local_nome"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    local_id: Mapped[int] = mapped_column(ForeignKey("locais.id", ondelete="CASCADE"), index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    capacidade: Mapped[int | None] = mapped_column(Integer, nullable=True)

    local: Mapped["Local"] = relationship("Local", back_populates="salas")
    reservas: Mapped[list["Reserva"]] = relationship(
        "Reserva", back_populates="sala", cascade="all, delete-orphan"
    )
