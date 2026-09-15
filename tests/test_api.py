def test_health(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_criar_link(client):
    resposta = client.post("/links", json={"url": "https://pucpr.br"})
    assert resposta.status_code == 201

    corpo = resposta.json()
    assert corpo["url"] == "https://pucpr.br"
    assert corpo["acessos"] == 0
    assert corpo["url_curta"].endswith(corpo["codigo"])


def test_criar_link_com_codigo_personalizado(client):
    resposta = client.post(
        "/links", json={"url": "https://pucpr.br", "codigo": "pucpr"}
    )
    assert resposta.status_code == 201
    assert resposta.json()["codigo"] == "pucpr"


def test_criar_link_com_url_invalida(client):
    resposta = client.post("/links", json={"url": "isso-nao-e-uma-url"})
    assert resposta.status_code == 400


def test_codigo_duplicado_retorna_conflito(client):
    client.post("/links", json={"url": "https://pucpr.br", "codigo": "pucpr"})
    resposta = client.post("/links", json={"url": "https://a.com", "codigo": "pucpr"})
    assert resposta.status_code == 409


def test_redirecionamento(client):
    codigo = client.post("/links", json={"url": "https://pucpr.br"}).json()["codigo"]

    resposta = client.get(f"/{codigo}", follow_redirects=False)
    assert resposta.status_code == 307
    assert resposta.headers["location"] == "https://pucpr.br"


def test_redirecionamento_incrementa_acessos(client):
    codigo = client.post("/links", json={"url": "https://pucpr.br"}).json()["codigo"]
    client.get(f"/{codigo}", follow_redirects=False)
    client.get(f"/{codigo}", follow_redirects=False)

    assert client.get(f"/links/{codigo}").json()["acessos"] == 2


def test_codigo_inexistente_retorna_404(client):
    assert client.get("/naoexiste", follow_redirects=False).status_code == 404


def test_listar_links(client):
    client.post("/links", json={"url": "https://pucpr.br"})
    client.post("/links", json={"url": "https://github.com"})

    resposta = client.get("/links")
    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_remover_link(client):
    codigo = client.post("/links", json={"url": "https://pucpr.br"}).json()["codigo"]

    assert client.delete(f"/links/{codigo}").status_code == 204
    assert client.get(f"/links/{codigo}").status_code == 404
    assert client.delete(f"/links/{codigo}").status_code == 404
