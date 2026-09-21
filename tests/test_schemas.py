"""Testes unitarios dos modelos de dados e da montagem da resposta.

Sao funcoes puras: nao dependem de banco nem de requisicao HTTP.
"""

import pytest
from pydantic import ValidationError

from app import main
from app.schemas import LinkEntrada, LinkSaida


def test_link_entrada_aceita_so_a_url():
    entrada = LinkEntrada(url="https://pucpr.br")

    assert entrada.url == "https://pucpr.br"
    assert entrada.codigo is None


def test_link_entrada_sem_url_e_rejeitada():
    with pytest.raises(ValidationError):
        LinkEntrada()


def test_link_saida_exige_todos_os_campos():
    with pytest.raises(ValidationError):
        LinkSaida(codigo="pucpr", url="https://pucpr.br")


def test_montar_resposta_usa_a_base_url_configurada(monkeypatch):
    monkeypatch.setattr(main, "BASE_URL", "https://link.pucpr.br")

    resposta = main.montar_resposta(
        {
            "codigo": "pucpr",
            "url": "https://pucpr.br",
            "criado_em": "2026-01-01T00:00:00+00:00",
            "acessos": 7,
        }
    )

    assert resposta.url_curta == "https://link.pucpr.br/pucpr"
    assert resposta.acessos == 7


def test_montar_resposta_preserva_os_dados_do_link():
    link = {
        "codigo": "abc123",
        "url": "https://exemplo.com/caminho?a=1",
        "criado_em": "2026-01-01T00:00:00+00:00",
        "acessos": 0,
    }

    resposta = main.montar_resposta(link)

    assert resposta.codigo == link["codigo"]
    assert resposta.url == link["url"]
    assert resposta.criado_em == link["criado_em"]
