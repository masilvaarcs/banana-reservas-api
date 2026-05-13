from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.local import Local
from app.schemas.local import LocalCreate, LocalResponse, LocalUpdate
from app.services.auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/locais", tags=["locais"])


@router.get("", response_model=list[LocalResponse])
def list_locais(
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> list[Local]:
    _ = current_user
    return db.execute(select(Local).order_by(Local.nome)).scalars().all()


@router.post("", response_model=LocalResponse, status_code=status.HTTP_201_CREATED)
def create_local(
    payload: LocalCreate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> Local:
    _ = current_user

    local = Local(
        nome=payload.nome.strip(),
        descricao=payload.descricao.strip() if payload.descricao else None,
    )

    db.add(local)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um local com esse nome.",
        ) from exc

    db.refresh(local)
    return local


@router.put("/{local_id}", response_model=LocalResponse)
def update_local(
    local_id: int,
    payload: LocalUpdate,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> Local:
    _ = current_user

    local = db.get(Local, local_id)
    if local is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local não encontrado.")

    if payload.nome is not None:
        local.nome = payload.nome.strip()

    if payload.descricao is not None:
        local.descricao = payload.descricao.strip() if payload.descricao else None

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um local com esse nome.",
        ) from exc

    db.refresh(local)
    return local


@router.delete("/{local_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_local(
    local_id: int,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> Response:
    _ = current_user

    local = db.get(Local, local_id)
    if local is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Local não encontrado.")

    db.delete(local)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
