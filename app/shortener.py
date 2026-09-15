import re
import secrets
import string
from urllib.parse import urlparse

from app import storage
from app.config import CODE_LENGTH

ALFABETO = string.ascii_letters + string.digits
FORMATO_CODIGO = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
ESQUEMAS_VALIDOS = ("http", "https")


class UrlInvalida(Exception):
    pass


class CodigoInvalido(Exception):
    pass


class CodigoEmUso(Exception):
    pass


def gerar_codigo(tamanho=CODE_LENGTH):
    return "".join(secrets.choice(ALFABETO) for _ in range(tamanho))


def gerar_codigo_livre(tentativas=10):
    for _ in range(tentativas):
        codigo = gerar_codigo()
        if storage.buscar_link(codigo) is None:
            return codigo
    raise RuntimeError("Nao foi possivel gerar um codigo livre")


def validar_url(url):
    url = (url or "").strip()
    partes = urlparse(url)
    if partes.scheme not in ESQUEMAS_VALIDOS or not partes.netloc:
        raise UrlInvalida("Informe uma URL comecando com http:// ou https://")
    return url


def validar_codigo(codigo):
    if not FORMATO_CODIGO.match(codigo or ""):
        raise CodigoInvalido("O codigo deve ter de 3 a 32 letras, numeros, _ ou -")
    return codigo


def encurtar(url, codigo=None):
    url = validar_url(url)

    if codigo:
        validar_codigo(codigo)
        if storage.buscar_link(codigo):
            raise CodigoEmUso(f"O codigo '{codigo}' ja esta em uso")
    else:
        existente = storage.buscar_por_url(url)
        if existente:
            return existente
        codigo = gerar_codigo_livre()

    return storage.salvar_link(codigo, url)


def resolver(codigo):
    link = storage.buscar_link(codigo)
    if link:
        storage.registrar_acesso(codigo)
    return link
