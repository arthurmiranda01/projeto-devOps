import pytest

from app import shortener


def test_codigo_gerado_tem_o_tamanho_pedido():
    assert len(shortener.gerar_codigo(8)) == 8


def test_codigos_gerados_sao_diferentes():
    codigos = {shortener.gerar_codigo() for _ in range(100)}
    assert len(codigos) == 100


@pytest.mark.parametrize("url", ["", "sem-esquema.com", "ftp://arquivo.com", "http://"])
def test_url_invalida_e_rejeitada(url):
    with pytest.raises(shortener.UrlInvalida):
        shortener.validar_url(url)


def test_url_valida_e_aceita():
    assert shortener.validar_url(" https://pucpr.br ") == "https://pucpr.br"


@pytest.mark.parametrize("codigo", ["ab", "codigo com espaco", "c" * 33, "aqui!"])
def test_codigo_fora_do_padrao_e_rejeitado(codigo):
    with pytest.raises(shortener.CodigoInvalido):
        shortener.validar_codigo(codigo)


def test_mesma_url_reaproveita_o_codigo():
    primeiro = shortener.encurtar("https://pucpr.br")
    segundo = shortener.encurtar("https://pucpr.br")
    assert primeiro["codigo"] == segundo["codigo"]


def test_codigo_personalizado_duplicado_gera_erro():
    shortener.encurtar("https://pucpr.br", "pucpr")
    with pytest.raises(shortener.CodigoEmUso):
        shortener.encurtar("https://outro.com", "pucpr")


def test_resolver_conta_o_acesso():
    link = shortener.encurtar("https://pucpr.br")
    shortener.resolver(link["codigo"])
    shortener.resolver(link["codigo"])
    assert shortener.resolver(link["codigo"])["acessos"] == 2


def test_resolver_codigo_inexistente_retorna_none():
    assert shortener.resolver("nada") is None
