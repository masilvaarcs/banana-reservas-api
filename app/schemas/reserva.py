from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReservaBase(BaseModel):
    local_id: int = Field(gt=0)
    sala_id: int = Field(gt=0)
    inicio: datetime
    fim: datetime
    responsavel: str = Field(min_length=2, max_length=120)
    cafe: bool = False
    quantidade_pessoas: int | None = Field(default=None, gt=0)
    descricao: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_period_and_cafe(self) -> "ReservaBase":
        if self.fim <= self.inicio:
            raise ValueError("A data/hora de fim precisa ser maior que a de início.")

        if self.cafe and not self.quantidade_pessoas:
            raise ValueError("Informe a quantidade de pessoas quando café for true.")

        if not self.cafe:
            self.quantidade_pessoas = None

        return self


class ReservaCreate(ReservaBase):
    pass


class ReservaUpdate(BaseModel):
    local_id: int | None = Field(default=None, gt=0)
    sala_id: int | None = Field(default=None, gt=0)
    inicio: datetime | None = None
    fim: datetime | None = None
    responsavel: str | None = Field(default=None, min_length=2, max_length=120)
    cafe: bool | None = None
    quantidade_pessoas: int | None = Field(default=None, gt=0)
    descricao: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_period_and_cafe(self) -> "ReservaUpdate":
        if self.inicio and self.fim and self.fim <= self.inicio:
            raise ValueError("A data/hora de fim precisa ser maior que a de início.")

        if self.cafe is True and not self.quantidade_pessoas:
            raise ValueError("Informe a quantidade de pessoas quando café for true.")

        if self.cafe is False:
            self.quantidade_pessoas = None

        return self


class ReservaResponse(BaseModel):
    id: int
    local_id: int
    sala_id: int
    inicio: datetime
    fim: datetime
    responsavel: str
    cafe: bool
    quantidade_pessoas: int | None
    descricao: str | None
    criado_por_email: str | None

    model_config = ConfigDict(from_attributes=True)


class ReservaBatchDeleteRequest(BaseModel):
    reserva_ids: list[int] = Field(min_length=1)


class ReservaBatchDeleteResponse(BaseModel):
    deleted_count: int
