from pydantic import BaseModel, Field


class LinkEntrada(BaseModel):
    url: str = Field(..., description="URL original que sera encurtada")
    codigo: str | None = Field(None, description="Codigo personalizado opcional")


class LinkSaida(BaseModel):
    codigo: str
    url: str
    url_curta: str
    criado_em: str
    acessos: int
