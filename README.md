# projeto-devOps

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
| GitHub Actions | Pipeline de CI |

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

## Testes

```bash
pytest
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
.github/workflows/ci.yml   pipeline de CI
```

## Fluxo de trabalho

O desenvolvimento acontece em branches `feature/*` e o merge para a `main` so e feito
depois que o pipeline de CI passa (testes nas versoes 3.10 e 3.12 do Python e build da
imagem Docker).
