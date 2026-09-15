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

## Testes e qualidade

```bash
pytest                 # testes + cobertura (minimo de 85%)
ruff check .           # lint
ruff format --check .  # formatacao
```

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
tests/           testes com pytest
scripts/         geracao da documentacao estatica
.github/workflows/
  ci.yml         lint, testes e build da imagem
  cd.yml         entrega da imagem e deploy da documentacao
  codeql.yml     analise estatica de seguranca
```

## Pipeline de CI/CD

Os workflows ficam em [.github/workflows](.github/workflows).

### CI (`ci.yml`)

Roda a cada push nos branches `feature/**`, em toda pull request para a `main` e
tambem sob demanda:

1. **Qualidade de codigo** - `ruff check` e `ruff format --check`.
2. **Testes** - pytest com cobertura nas versoes 3.10 e 3.12 do Python; o build falha
   se a cobertura ficar abaixo de 85% e o relatorio fica salvo como artefato.
3. **Build da imagem** - constroi a imagem Docker, sobe o container e valida o
   `/health`, a criacao de um link e o redirecionamento.

### CodeQL (`codeql.yml`)

Analise estatica de seguranca e qualidade do GitHub, executada nas pull requests e
toda segunda-feira de manha.

### CD (`cd.yml`)

Roda nas pull requests em modo de validacao e efetiva a entrega quando o codigo chega
na `main`:

1. **Entrega da imagem no GHCR** - publica a imagem em
   `ghcr.io/arthurmiranda01/projeto-devops` com as tags `latest` e o hash do commit.
   Em pull request a imagem so e construida, sem publicar.
2. **Build da documentacao** - gera o site estatico a partir do OpenAPI da API.
3. **Deploy no GitHub Pages** - publica a documentacao em
   https://arthurmiranda01.github.io/projeto-devOps/ (apenas a partir da `main`).

Baixando e rodando a imagem publicada:

```bash
docker run -p 8000:8000 ghcr.io/arthurmiranda01/projeto-devops:latest
```

## Fluxo de trabalho

O desenvolvimento acontece em branches `feature/*`. Toda mudanca entra na `main` por
pull request e so pode ser mesclada depois que os workflows de CI, CodeQL e CD passam.
Com o merge na `main`, o CD publica a imagem no GHCR e atualiza a documentacao no
GitHub Pages.
