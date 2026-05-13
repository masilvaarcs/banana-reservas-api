from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.local import Local
from app.models.reserva import Reserva
from app.models.sala import Sala


def get_local_or_404(db: Session, local_id: int) -> Local:
    local = db.get(Local, local_id)
    if local is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local não encontrado.")
    return local


def get_sala_or_404(db: Session, sala_id: int) -> Sala:
    sala = db.get(Sala, sala_id)
    if sala is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sala não encontrada.")
    return sala


def validate_sala_local_pair(db: Session, local_id: int, sala_id: int) -> Sala:
    get_local_or_404(db, local_id)
    sala = get_sala_or_404(db, sala_id)

    if sala.local_id != local_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A sala informada não pertence ao local informado.",
        )

    return sala


def has_schedule_conflict(
    db: Session,
    *,
    local_id: int,
    sala_id: int,
    inicio: datetime,
    fim: datetime,
    ignore_reserva_id: int | None = None,
) -> bool:
    query = select(Reserva.id).where(
        Reserva.local_id == local_id,
        Reserva.sala_id == sala_id,
        Reserva.inicio < fim,
        Reserva.fim > inicio,
    )

    if ignore_reserva_id is not None:
        query = query.where(Reserva.id != ignore_reserva_id)

    return db.execute(query.limit(1)).scalar_one_or_none() is not None
