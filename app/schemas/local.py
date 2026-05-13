from pydantic import BaseModel, ConfigDict, Field


class LocalBase(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=1000)


class LocalCreate(LocalBase):
    pass


class LocalUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    descricao: str | None = Field(default=None, max_length=1000)


class LocalResponse(LocalBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
