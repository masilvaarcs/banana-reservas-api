from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.reserva import Reserva
from app.schemas.reserva import (
    ReservaBatchDeleteRequest,
    ReservaBatchDeleteResponse,
    ReservaCreate,
    ReservaResponse,
    ReservaUpdate,
)
from app.services.auth import AuthUser, get_current_user
from app.services.reserva_service import has_schedule_conflict, validate_sala_local_pair

router = APIRouter(prefix="/api/reservas", tags=["reservas"])


@router.get("", response_model=list[ReservaResponse])
def list_reservas(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> list[Reserva]:
    _ = current_user
    return db.execute(select(Reserva).order_by(Reserva.inicio.desc())).scalars().all()


@router.post("", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED)
def create_reserva(
    payload: ReservaCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> Reserva | JSONResponse:
    validate_sala_local_pair(db, payload.local_id, payload.sala_id)

    if has_schedule_conflict(
        db,
        local_id=payload.local_id,
        sala_id=payload.sala_id,
        inicio=payload.inicio,
        fim=payload.fim,
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Conflito de horário",
                "detail": "A sala já está reservada neste período.",
            },
        )

    reserva = Reserva(
        local_id=payload.local_id,
        sala_id=payload.sala_id,
        inicio=payload.inicio,
        fim=payload.fim,
        responsavel=payload.responsavel.strip(),
        cafe=payload.cafe,
        quantidade_pessoas=payload.quantidade_pessoas if payload.cafe else None,
        descricao=payload.descricao.strip() if payload.descricao else None,
        criado_por_email=current_user["email"],
    )

    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return reserva


@router.put("/{reserva_id}", response_model=ReservaResponse)
def update_reserva(
    reserva_id: int,
    payload: ReservaUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> Reserva | JSONResponse:
    _ = current_user

    reserva = db.get(Reserva, reserva_id)
    if reserva is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

    data = payload.model_dump(exclude_unset=True)

    new_local_id = data.get("local_id", reserva.local_id)
    new_sala_id = data.get("sala_id", reserva.sala_id)
    new_inicio = data.get("inicio", reserva.inicio)
    new_fim = data.get("fim", reserva.fim)

    if new_fim <= new_inicio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data/hora de fim precisa ser maior que a de início.",
        )

    new_cafe = data.get("cafe", reserva.cafe)

    if "quantidade_pessoas" in data:
        new_quantidade = data.get("quantidade_pessoas")
    else:
        new_quantidade = reserva.quantidade_pessoas

    if not new_cafe:
        new_quantidade = None

    if new_cafe and not new_quantidade:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe a quantidade de pessoas quando café for true.",
        )

    validate_sala_local_pair(db, new_local_id, new_sala_id)

    if has_schedule_conflict(
        db,
        local_id=new_local_id,
        sala_id=new_sala_id,
        inicio=new_inicio,
        fim=new_fim,
        ignore_reserva_id=reserva.id,
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Conflito de horário",
                "detail": "A sala já está reservada neste período.",
            },
        )

    reserva.local_id = new_local_id
    reserva.sala_id = new_sala_id
    reserva.inicio = new_inicio
    reserva.fim = new_fim
    reserva.cafe = new_cafe
    reserva.quantidade_pessoas = new_quantidade

    if "responsavel" in data:
        reserva.responsavel = data["responsavel"].strip()

    if "descricao" in data:
        reserva.descricao = data["descricao"].strip() if data["descricao"] else None

    db.commit()
    db.refresh(reserva)
    return reserva


@router.delete("/batch", response_model=ReservaBatchDeleteResponse)
def batch_delete_reservas(
    payload: ReservaBatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> ReservaBatchDeleteResponse:
    _ = current_user

    result = db.execute(delete(Reserva).where(Reserva.id.in_(payload.reserva_ids)))
    db.commit()

    return ReservaBatchDeleteResponse(deleted_count=result.rowcount or 0)


@router.delete("/{reserva_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> Response:
    _ = current_user

    reserva = db.get(Reserva, reserva_id)
    if reserva is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

    db.delete(reserva)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
