import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATABASE_PATH", str(tmp_path / "teste.db"))
    storage.criar_tabelas()
    yield


@pytest.fixture
def client():
    with TestClient(app) as cliente:
        yield cliente
