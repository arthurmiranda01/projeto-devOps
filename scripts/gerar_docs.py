"""Gera a documentacao estatica da API publicada no GitHub Pages."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

SAIDA = Path("site")

PAGINA = """<!doctype html>
<html lang="pt-br">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{titulo} - Documentacao</title>
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap"
      rel="stylesheet"
    />
    <style>
      body {{ margin: 0; font-family: Inter, system-ui, sans-serif; }}
    </style>
  </head>
  <body>
    <redoc spec-url="openapi.json"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
  </body>
</html>
"""


def main():
    SAIDA.mkdir(exist_ok=True)

    especificacao = app.openapi()
    (SAIDA / "openapi.json").write_text(
        json.dumps(especificacao, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (SAIDA / "index.html").write_text(
        PAGINA.format(titulo=especificacao["info"]["title"]), encoding="utf-8"
    )
    (SAIDA / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Documentacao gerada em {SAIDA.resolve()}")


if __name__ == "__main__":
    main()
