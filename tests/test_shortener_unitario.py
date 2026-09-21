"""Testes unitarios do shortener com a camada de banco substituida por dublês.

Aqui o storage e trocado por funcoes falsas com monkeypatch, entao cada teste
verifica so a regra de negocio da funcao, sem depender do SQLite.
"""

import string

import pytest

from app import shortener


@pytest.fixture
def storage_falso(monkeypatch):
    """Substitui o storage por um dicionario em memoria e registra as chamadas."""

    estado = {"links": {}, "chamadas": []}

    def buscar_link(codigo):
        estado["chamadas"].append(("buscar_link", codigo))
        return estado["links"].get(codigo)

    def buscar_por_url(url):
        estado["chamadas"].append(("buscar_por_url", url))
        for link in estado["links"].values():
            if link["url"] == url:
                return link
        return None

    def salvar_link(codigo, url):
        estado["chamadas"].append(("salvar_link", codigo, url))
        link = {"codigo": codigo, "url": url, "criado_em": "2026-01-01", "acessos": 0}
        estado["links"][codigo] = link
        return link

    def registrar_acesso(codigo):
        estado["chamadas"].append(("registrar_acesso", codigo))
        estado["links"][codigo]["acessos"] += 1

    monkeypatch.setattr(shortener.storage, "buscar_link", buscar_link)
    monkeypatch.setattr(shortener.storage, "buscar_por_url", buscar_por_url)
    monkeypatch.setattr(shortener.storage, "salvar_link", salvar_link)
    monkeypatch.setattr(shortener.storage, "registrar_acesso", registrar_acesso)
    return estado


def nomes_chamados(estado):
    return [chamada[0] for chamada in estado["chamadas"]]


# --- gerar_codigo -----------------------------------------------------------


def test_gerar_codigo_usa_apenas_letras_e_numeros():
    permitidos = set(string.ascii_letters + string.digits)

    assert set(shortener.gerar_codigo(200)) <= permitidos


def test_gerar_codigo_com_tamanho_zero_devolve_string_vazia():
    assert shortener.gerar_codigo(0) == ""


# --- gerar_codigo_livre -----------------------------------------------------


def test_gerar_codigo_livre_tenta_de_novo_quando_o_codigo_ja_existe(monkeypatch):
    sequencia = iter(["ocupado1", "ocupado2", "livre"])
    monkeypatch.setattr(shortener, "gerar_codigo", lambda: next(sequencia))
    monkeypatch.setattr(
        shortener.storage,
        "buscar_link",
        lambda codigo: None if codigo == "livre" else {"codigo": codigo},
    )

    assert shortener.gerar_codigo_livre() == "livre"


def test_gerar_codigo_livre_desiste_depois_do_limite_de_tentativas(monkeypatch):
    tentativas = []
    monkeypatch.setattr(shortener, "gerar_codigo", lambda: "sempre-o-mesmo")
    monkeypatch.setattr(
        shortener.storage,
        "buscar_link",
        lambda codigo: tentativas.append(codigo) or {"codigo": codigo},
    )

    with pytest.raises(RuntimeError, match="codigo livre"):
        shortener.gerar_codigo_livre(tentativas=3)

    assert len(tentativas) == 3


# --- validar_url ------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        None,
        "   ",
        "javascript:alert(1)",
        "file:///etc/passwd",
        "//sem-esquema.com",
        "https://",
    ],
)
def test_validar_url_rejeita_entradas_perigosas_ou_incompletas(url):
    with pytest.raises(shortener.UrlInvalida):
        shortener.validar_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://exemplo.com",
        "https://exemplo.com",
        "https://exemplo.com/caminho?busca=1#ancora",
        "https://sub.dominio.exemplo.com:8443/a",
    ],
)
def test_validar_url_aceita_http_e_https(url):
    assert shortener.validar_url(url) == url


def test_validar_url_remove_espacos_das_pontas():
    assert shortener.validar_url("\t https://pucpr.br \n") == "https://pucpr.br"


# --- validar_codigo ---------------------------------------------------------


@pytest.mark.parametrize(
    "codigo", ["abc", "c" * 32, "com_underline", "com-hifen", "aB9"]
)
def test_validar_codigo_aceita_o_formato_esperado(codigo):
    assert shortener.validar_codigo(codigo) == codigo


@pytest.mark.parametrize(
    "codigo", [None, "", "ab", "c" * 33, "com espaco", "aqui!", "ç" * 5]
)
def test_validar_codigo_rejeita_fora_do_formato(codigo):
    with pytest.raises(shortener.CodigoInvalido):
        shortener.validar_codigo(codigo)


# --- encurtar ---------------------------------------------------------------


def test_encurtar_nao_toca_no_banco_quando_a_url_e_invalida(storage_falso):
    with pytest.raises(shortener.UrlInvalida):
        shortener.encurtar("nao-e-url")

    assert storage_falso["chamadas"] == []


def test_encurtar_nao_toca_no_banco_quando_o_codigo_e_invalido(storage_falso):
    with pytest.raises(shortener.CodigoInvalido):
        shortener.encurtar("https://pucpr.br", "ab")

    assert "salvar_link" not in nomes_chamados(storage_falso)


def test_encurtar_com_codigo_personalizado_salva_o_codigo_pedido(storage_falso):
    link = shortener.encurtar("https://pucpr.br", "pucpr")

    assert link["codigo"] == "pucpr"
    assert ("salvar_link", "pucpr", "https://pucpr.br") in storage_falso["chamadas"]


def test_encurtar_com_codigo_personalizado_nao_procura_pela_url(storage_falso):
    shortener.encurtar("https://pucpr.br", "pucpr")

    assert "buscar_por_url" not in nomes_chamados(storage_falso)


def test_encurtar_reaproveita_o_link_existente_sem_salvar_de_novo(storage_falso):
    primeiro = shortener.encurtar("https://pucpr.br")
    storage_falso["chamadas"].clear()

    segundo = shortener.encurtar("https://pucpr.br")

    assert segundo == primeiro
    assert "salvar_link" not in nomes_chamados(storage_falso)


def test_encurtar_salva_a_url_ja_limpa(storage_falso):
    shortener.encurtar("  https://pucpr.br  ")

    salvas = [c for c in storage_falso["chamadas"] if c[0] == "salvar_link"]
    assert salvas[0][2] == "https://pucpr.br"


# --- resolver ---------------------------------------------------------------


def test_resolver_registra_o_acesso_do_link_encontrado(storage_falso):
    link = shortener.encurtar("https://pucpr.br", "pucpr")
    storage_falso["chamadas"].clear()

    assert shortener.resolver("pucpr") == link
    assert ("registrar_acesso", "pucpr") in storage_falso["chamadas"]


def test_resolver_nao_registra_acesso_de_codigo_inexistente(storage_falso):
    assert shortener.resolver("nao-existe") is None
    assert "registrar_acesso" not in nomes_chamados(storage_falso)
