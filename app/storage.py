import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    codigo TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    acessos INTEGER NOT NULL DEFAULT 0
)
"""


@contextmanager
def conectar():
    diretorio = os.path.dirname(DATABASE_PATH)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)

    conexao = sqlite3.connect(DATABASE_PATH)
    conexao.row_factory = sqlite3.Row
    try:
        yield conexao
        conexao.commit()
    finally:
        conexao.close()


def criar_tabelas():
    with conectar() as conexao:
        conexao.execute(SCHEMA)


def salvar_link(codigo, url):
    with conectar() as conexao:
        conexao.execute(
            "INSERT INTO links (codigo, url, criado_em) VALUES (?, ?, ?)",
            (codigo, url, datetime.now(timezone.utc).isoformat()),
        )
    return buscar_link(codigo)


def buscar_link(codigo):
    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT codigo, url, criado_em, acessos FROM links WHERE codigo = ?",
            (codigo,),
        ).fetchone()
    return dict(linha) if linha else None


def buscar_por_url(url):
    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT codigo, url, criado_em, acessos FROM links WHERE url = ?",
            (url,),
        ).fetchone()
    return dict(linha) if linha else None


def registrar_acesso(codigo):
    with conectar() as conexao:
        conexao.execute(
            "UPDATE links SET acessos = acessos + 1 WHERE codigo = ?", (codigo,)
        )


def listar_links(limite=50):
    with conectar() as conexao:
        linhas = conexao.execute(
            "SELECT codigo, url, criado_em, acessos FROM links "
            "ORDER BY criado_em DESC LIMIT ?",
            (limite,),
        ).fetchall()
    return [dict(linha) for linha in linhas]


def remover_link(codigo):
    with conectar() as conexao:
        cursor = conexao.execute("DELETE FROM links WHERE codigo = ?", (codigo,))
    return cursor.rowcount > 0
