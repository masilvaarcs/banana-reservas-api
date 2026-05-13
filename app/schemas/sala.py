from pydantic import BaseModel, ConfigDict, Field


class SalaBase(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    capacidade: int | None = Field(default=None, gt=0)


class SalaCreate(SalaBase):
    local_id: int = Field(gt=0)


class SalaUpdate(BaseModel):
    local_id: int | None = Field(default=None, gt=0)
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    capacidade: int | None = Field(default=None, gt=0)


class SalaResponse(SalaBase):
    id: int
    local_id: int

    model_config = ConfigDict(from_attributes=True)
