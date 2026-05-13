from app.schemas.local import LocalCreate, LocalResponse, LocalUpdate
from app.schemas.reserva import (
    ReservaBatchDeleteRequest,
    ReservaBatchDeleteResponse,
    ReservaCreate,
    ReservaResponse,
    ReservaUpdate,
)
from app.schemas.sala import SalaCreate, SalaResponse, SalaUpdate

__all__ = [
    "LocalCreate",
    "LocalUpdate",
    "LocalResponse",
    "SalaCreate",
    "SalaUpdate",
    "SalaResponse",
    "ReservaCreate",
    "ReservaUpdate",
    "ReservaResponse",
    "ReservaBatchDeleteRequest",
    "ReservaBatchDeleteResponse",
]
