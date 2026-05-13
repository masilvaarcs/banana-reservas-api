from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.sala import Sala
from app.schemas.sala import SalaCreate, SalaResponse, SalaUpdate
from app.services.auth import AuthUser, get_current_user
from app.services.reserva_service import get_local_or_404

router = APIRouter(prefix="/api/salas", tags=["salas"])


@router.get("", response_model=list[SalaResponse])
def list_salas(
    local_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> list[Sala]:
    _ = current_user

    query = select(Sala).order_by(Sala.nome)
    if local_id is not None:
        query = query.where(Sala.local_id == local_id)

    return db.execute(query).scalars().all()


@router.post("", response_model=SalaResponse, status_code=status.HTTP_201_CREATED)
def create_sala(
    payload: SalaCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> Sala:
    _ = current_user

    get_local_or_404(db, payload.local_id)

    sala = Sala(
        local_id=payload.local_id,
        nome=payload.nome.strip(),
        capacidade=payload.capacidade,
    )

    db.add(sala)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma sala com esse nome nesse local.",
        ) from exc

    db.refresh(sala)
    return sala


@router.put("/{sala_id}", response_model=SalaResponse)
def update_sala(
    sala_id: int,
    payload: SalaUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> Sala:
    _ = current_user

    sala = db.get(Sala, sala_id)
    if sala is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sala não encontrada.")

    if payload.local_id is not None:
        get_local_or_404(db, payload.local_id)
        sala.local_id = payload.local_id

    if payload.nome is not None:
        sala.nome = payload.nome.strip()

    if payload.capacidade is not None:
        sala.capacidade = payload.capacidade

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma sala com esse nome nesse local.",
        ) from exc

    db.refresh(sala)
    return sala


@router.delete("/{sala_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sala(
    sala_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> Response:
    _ = current_user

    sala = db.get(Sala, sala_id)
    if sala is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sala não encontrada.")

    db.delete(sala)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
