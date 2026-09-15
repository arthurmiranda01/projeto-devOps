from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from app import shortener, storage
from app.config import BASE_URL
from app.schemas import LinkEntrada, LinkSaida


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.criar_tabelas()
    yield


app = FastAPI(
    title="Encurtador de URLs",
    description="API simples para encurtar links e acompanhar os acessos",
    version="1.0.0",
    lifespan=lifespan,
)


def montar_resposta(link):
    return LinkSaida(
        codigo=link["codigo"],
        url=link["url"],
        url_curta=f"{BASE_URL}/{link['codigo']}",
        criado_em=link["criado_em"],
        acessos=link["acessos"],
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/links", response_model=LinkSaida, status_code=201)
def criar_link(entrada: LinkEntrada):
    try:
        link = shortener.encurtar(entrada.url, entrada.codigo)
    except (shortener.UrlInvalida, shortener.CodigoInvalido) as erro:
        raise HTTPException(status_code=400, detail=str(erro))
    except shortener.CodigoEmUso as erro:
        raise HTTPException(status_code=409, detail=str(erro))
    return montar_resposta(link)


@app.get("/links", response_model=list[LinkSaida])
def listar_links(limite: int = 50):
    return [montar_resposta(link) for link in storage.listar_links(limite)]


@app.get("/links/{codigo}", response_model=LinkSaida)
def detalhar_link(codigo: str):
    link = storage.buscar_link(codigo)
    if not link:
        raise HTTPException(status_code=404, detail="Link nao encontrado")
    return montar_resposta(link)


@app.delete("/links/{codigo}", status_code=204)
def remover_link(codigo: str):
    if not storage.remover_link(codigo):
        raise HTTPException(status_code=404, detail="Link nao encontrado")


@app.get("/{codigo}")
def redirecionar(codigo: str):
    link = shortener.resolver(codigo)
    if not link:
        raise HTTPException(status_code=404, detail="Link nao encontrado")
    return RedirectResponse(link["url"], status_code=307)
