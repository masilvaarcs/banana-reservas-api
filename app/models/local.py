from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Local(Base):
    __tablename__ = "locais"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)

    salas: Mapped[list["Sala"]] = relationship(
        "Sala", back_populates="local", cascade="all, delete-orphan"
    )
    reservas: Mapped[list["Reserva"]] = relationship(
        "Reserva", back_populates="local", cascade="all, delete-orphan"
    )
