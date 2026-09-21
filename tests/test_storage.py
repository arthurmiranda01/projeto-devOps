"""Testes unitarios da camada de armazenamento.

Cada teste chama o modulo storage diretamente, sem passar pela API, para
isolar o comportamento do banco.
"""

import sqlite3
from datetime import datetime

import pytest

from app import storage


def test_salvar_link_devolve_o_registro_completo():
    link = storage.salvar_link("pucpr", "https://pucpr.br")

    assert link["codigo"] == "pucpr"
    assert link["url"] == "https://pucpr.br"
    assert link["acessos"] == 0
    assert datetime.fromisoformat(link["criado_em"]).tzinfo is not None


def test_buscar_link_inexistente_devolve_none():
    assert storage.buscar_link("nao-existe") is None


def test_buscar_por_url_encontra_o_codigo_salvo():
    storage.salvar_link("pucpr", "https://pucpr.br")

    assert storage.buscar_por_url("https://pucpr.br")["codigo"] == "pucpr"


def test_buscar_por_url_nao_confunde_urls_parecidas():
    storage.salvar_link("pucpr", "https://pucpr.br")

    assert storage.buscar_por_url("https://pucpr.br/cursos") is None


def test_codigo_duplicado_viola_a_chave_primaria():
    storage.salvar_link("pucpr", "https://pucpr.br")

    with pytest.raises(sqlite3.IntegrityError):
        storage.salvar_link("pucpr", "https://outro.com")


def test_registrar_acesso_incrementa_o_contador():
    storage.salvar_link("pucpr", "https://pucpr.br")

    storage.registrar_acesso("pucpr")
    storage.registrar_acesso("pucpr")

    assert storage.buscar_link("pucpr")["acessos"] == 2


def test_registrar_acesso_em_codigo_inexistente_nao_quebra():
    storage.registrar_acesso("nao-existe")

    assert storage.buscar_link("nao-existe") is None


def test_listar_links_devolve_do_mais_novo_para_o_mais_antigo():
    storage.salvar_link("antigo", "https://antigo.com")
    storage.salvar_link("novo", "https://novo.com")

    codigos = [link["codigo"] for link in storage.listar_links()]

    assert codigos.index("novo") < codigos.index("antigo")


def test_listar_links_respeita_o_limite():
    for indice in range(5):
        storage.salvar_link(f"link{indice}", f"https://exemplo{indice}.com")

    assert len(storage.listar_links(limite=2)) == 2


def test_listar_links_com_banco_vazio_devolve_lista_vazia():
    assert storage.listar_links() == []


def test_remover_link_existente_devolve_true():
    storage.salvar_link("pucpr", "https://pucpr.br")

    assert storage.remover_link("pucpr") is True
    assert storage.buscar_link("pucpr") is None


def test_remover_link_inexistente_devolve_false():
    assert storage.remover_link("nao-existe") is False


def test_criar_tabelas_pode_rodar_mais_de_uma_vez():
    storage.salvar_link("pucpr", "https://pucpr.br")

    storage.criar_tabelas()

    assert storage.buscar_link("pucpr") is not None


def test_conectar_cria_o_diretorio_do_banco(tmp_path, monkeypatch):
    destino = tmp_path / "novo" / "sub" / "links.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", str(destino))

    storage.criar_tabelas()

    assert destino.parent.is_dir()
