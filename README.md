# projeto-devOps

[![CI](https://github.com/arthurmiranda01/projeto-devOps/actions/workflows/ci.yml/badge.svg)](https://github.com/arthurmiranda01/projeto-devOps/actions/workflows/ci.yml)
[![CD](https://github.com/arthurmiranda01/projeto-devOps/actions/workflows/cd.yml/badge.svg)](https://github.com/arthurmiranda01/projeto-devOps/actions/workflows/cd.yml)
[![CodeQL](https://github.com/arthurmiranda01/projeto-devOps/actions/workflows/codeql.yml/badge.svg)](https://github.com/arthurmiranda01/projeto-devOps/actions/workflows/codeql.yml)

Projeto da disciplina de DevOps da PUCPR: uma API de encurtador de URLs escrita em
Python com FastAPI, com testes automatizados, empacotamento em Docker e pipeline de
integracao continua no GitHub Actions.

## Funcionalidades

- Encurtar uma URL e receber um codigo curto gerado automaticamente
- Definir um codigo personalizado (ex.: `/pucpr`)
- Redirecionar o visitante para a URL original
- Contar quantos acessos cada link recebeu
- Listar, consultar e remover os links cadastrados

## Tecnologias

| Item | Uso |
| --- | --- |
| FastAPI + Uvicorn | API HTTP e documentacao automatica |
| SQLite | Armazenamento dos links |
| pytest | Testes automatizados |
| Docker / Docker Compose | Empacotamento e execucao |
| ruff | Lint e formatacao |
| GitHub Actions | Pipelines de CI e CD |

## Rodando localmente

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000` e a documentacao interativa fica em
`http://localhost:8000/docs`.

## Rodando com Docker

```bash
docker compose up --build
```

A API fica disponivel em `http://localhost:8000` e os dados ficam em um volume
chamado `dados`, entao os links sobrevivem ao reinicio do container.

Sem o compose:

```bash
docker build -t encurtador-url .
docker run -p 8000:8000 -v encurtador-dados:/app/data encurtador-url
```

### Como a imagem foi montada

- Build em dois estagios: o primeiro instala as dependencias em um virtualenv e o
  segundo copia apenas esse virtualenv, deixando o `pip` e o cache fora da imagem final.
- Baseada na `python:3.12-slim`, com a versao parametrizada pelo build arg
  `PYTHON_VERSION`.
- A aplicacao roda com o usuario `appuser` (uid 10001), sem privilegios de root.
- `HEALTHCHECK` consultando `/health`, usado tanto pelo Docker quanto pelo compose.
- O `.dockerignore` mantem testes, scripts e o ambiente virtual local fora do contexto.

### Testando o container

```bash
bash scripts/testar_container.sh
```

O script constroi a imagem, sobe o container, espera o healthcheck ficar saudavel,
confere que o processo nao roda como root e testa a criacao de um link, o
redirecionamento, o contador de acessos e a remocao. E o mesmo script usado no CI.

## Testes e qualidade

```bash
pytest                 # testes + cobertura (minimo de 85%)
ruff check .           # lint
ruff format --check .  # formatacao
```

A suite tem 79 testes e cobre 100% do pacote `app`. Ela e dividida em tres niveis:

**Testes unitarios isolados** - `tests/test_shortener_unitario.py` troca o modulo
`storage` por dublês em memoria com `monkeypatch`. Assim cada funcao do shortener e
verificada sozinha, sem SQLite: o sorteio de codigos, as tentativas de
`gerar_codigo_livre` ate achar um codigo livre (e o erro quando esgota), a validacao de
URL e de codigo, e quais chamadas ao banco cada caminho deve ou nao fazer. Por exemplo,
uma URL invalida precisa falhar **antes** de qualquer acesso ao banco.

**Testes unitarios por modulo** - `tests/test_storage.py` exercita a persistencia
direto, sem passar pela API (ordenacao, limite, contador de acessos, remocao, chave
duplicada). `tests/test_schemas.py` cobre as funcoes puras: validacao dos modelos
Pydantic e a montagem da `url_curta` a partir da `BASE_URL`.

**Testes de integracao** - `tests/test_api.py` sobe a aplicacao com o `TestClient` do
FastAPI e verifica as rotas de ponta a ponta, incluindo os codigos de status
(201, 307, 400, 404, 409). `scripts/testar_container.sh` vai um nivel acima e testa a
imagem Docker ja construida.

Cada teste roda contra um banco SQLite temporario, criado pela fixture `banco_temporario`
do `tests/conftest.py`, entao a ordem de execucao nao importa e nada fica sujo entre eles.

## Endpoints

| Metodo | Rota | Descricao |
| --- | --- | --- |
| GET | `/health` | Verifica se a API esta no ar |
| POST | `/links` | Cria um link curto |
| GET | `/links` | Lista os links cadastrados |
| GET | `/links/{codigo}` | Mostra os dados e os acessos de um link |
| DELETE | `/links/{codigo}` | Remove um link |
| GET | `/{codigo}` | Redireciona para a URL original |

Exemplo de uso:

```bash
curl -X POST http://localhost:8000/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://pucpr.br", "codigo": "pucpr"}'
```

```json
{
  "codigo": "pucpr",
  "url": "https://pucpr.br",
  "url_curta": "http://localhost:8000/pucpr",
  "criado_em": "2025-09-14T21:30:00+00:00",
  "acessos": 0
}
```

## Variaveis de ambiente

| Variavel | Padrao | Descricao |
| --- | --- | --- |
| `DATABASE_PATH` | `data/links.db` | Caminho do banco SQLite |
| `BASE_URL` | `http://localhost:8000` | Dominio usado para montar a URL curta |
| `CODE_LENGTH` | `6` | Tamanho do codigo gerado automaticamente |

## Estrutura

```
app/
  config.py      variaveis de ambiente
  storage.py     acesso ao banco SQLite
  shortener.py   geracao de codigos e validacoes
  schemas.py     modelos de entrada e saida
  main.py        rotas da API
tests/
  conftest.py                 fixtures de banco temporario e cliente HTTP
  test_shortener_unitario.py  unitarios do shortener com o banco mockado
  test_storage.py             unitarios da camada de persistencia
  test_schemas.py             unitarios dos modelos e da montagem da resposta
  test_shortener.py           regras de negocio com banco real
  test_api.py                 testes de integracao das rotas
scripts/
  gerar_docs.py        documentacao estatica
  resumir_testes.py    resumo dos testes no relatorio do CI
  testar_container.sh  teste de ponta a ponta do container
.github/workflows/
  ci.yml         lint, testes e build da imagem
  cd.yml         entrega da imagem e deploy da documentacao
  codeql.yml     analise estatica de seguranca
  alertas.yml    notificacoes no Discord
```

## Pipeline de CI/CD

Os workflows ficam em [.github/workflows](.github/workflows).

### CI (`ci.yml`)

Roda a cada push nos branches `feature/**`, em toda pull request para a `main` e
tambem sob demanda:

1. **Qualidade de codigo** - `ruff check` e `ruff format --check`.
2. **Testes** - pytest com cobertura nas versoes 3.10 e 3.12 do Python; o build falha
   se a cobertura ficar abaixo de 85%. O resultado e resumido em uma tabela no relatorio
   da execucao, visivel direto na pull request, e os relatorios de cobertura e de testes
   ficam salvos como artefato.
3. **Build e teste do container** - constroi a imagem Docker, sobe o container e valida o
   `/health`, a criacao de um link e o redirecionamento, pelo
   `scripts/testar_container.sh`.

### CodeQL (`codeql.yml`)

Analise estatica de seguranca e qualidade do GitHub, executada nas pull requests e
toda segunda-feira de manha.

### CD (`cd.yml`)

Roda nas pull requests em modo de validacao e efetiva a entrega quando o codigo chega
na `main`:

1. **Entrega da imagem no GHCR** - publica a imagem em
   `ghcr.io/arthurmiranda01/projeto-devops` com as tags `latest` e o hash do commit.
   Em pull request a imagem so e construida, sem publicar.
2. **Entrega da imagem no Docker Hub** - publica a mesma imagem em
   `<usuario>/encurtador-url`. A etapa depende dos segredos `DOCKERHUB_USERNAME` e
   `DOCKERHUB_TOKEN`; sem eles a publicacao e apenas ignorada, sem quebrar o pipeline.
3. **Build da documentacao** - gera o site estatico a partir do OpenAPI da API.
4. **Deploy no GitHub Pages** - publica a documentacao em
   https://arthurmiranda01.github.io/projeto-devOps/ (apenas a partir da `main`).

Baixando e rodando a imagem publicada:

```bash
docker run -p 8000:8000 ghcr.io/arthurmiranda01/projeto-devops:latest
```

### Alertas (`alertas.yml`)

Envia notificacoes para um canal do Discord por webhook. O alerta dispara em tres
situacoes:

1. **Push ou merge na `main`** - mostra a mensagem do commit, o autor, o hash curto e o
   link da comparacao. Merges recebem um titulo e uma cor proprios.
2. **Fim de uma execucao do CI ou do CD** - avisa se o pipeline terminou com sucesso,
   falhou ou foi cancelado, com link direto para a execucao.
3. **Disparo manual** (`workflow_dispatch`) - envia uma mensagem de teste, util para
   conferir a configuracao.

A URL do webhook fica no segredo `DISCORD_WEBHOOK` do repositorio. Sem o segredo o job
apenas registra o aviso no resumo da execucao e termina com sucesso, sem quebrar o
pipeline.

Para configurar:

1. No Discord, abra **Editar canal > Integracoes > Webhooks > Novo webhook** e copie a
   URL.
2. No GitHub, va em **Settings > Secrets and variables > Actions > New repository
   secret**, com o nome `DISCORD_WEBHOOK` e a URL copiada como valor.
3. Em **Actions > Alertas > Run workflow**, dispare o workflow para validar o envio.

## Fluxo de trabalho

O desenvolvimento acontece em branches `feature/*`. Toda mudanca entra na `main` por
pull request e so pode ser mesclada depois que os workflows de CI, CodeQL e CD passam.
Com o merge na `main`, o CD publica a imagem no GHCR e atualiza a documentacao no
GitHub Pages, e o workflow de alertas avisa no Discord.
