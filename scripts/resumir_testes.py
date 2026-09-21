"""Transforma o JUnit XML do pytest em um resumo Markdown.

Usado pelo CI para escrever o resultado dos testes no resumo da execucao,
que fica visivel direto na pull request.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def ler_totais(raiz):
    suites = raiz.iter("testsuite") if raiz.tag == "testsuites" else [raiz]
    totais = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    for suite in suites:
        for chave in ("tests", "failures", "errors", "skipped"):
            totais[chave] += int(suite.get(chave, 0))
        totais["time"] += float(suite.get("time", 0))
    return totais


def listar_problemas(raiz):
    problemas = []
    for caso in raiz.iter("testcase"):
        for tipo in ("failure", "error"):
            no = caso.find(tipo)
            if no is not None:
                nome = f"{caso.get('classname', '')}::{caso.get('name', '')}"
                problemas.append((nome, (no.get("message") or "").strip()))
    return problemas


def main():
    caminho = Path(sys.argv[1] if len(sys.argv) > 1 else "test-results.xml")
    if not caminho.is_file():
        print("## Testes unitarios\n\nRelatorio nao encontrado.")
        return 0

    raiz = ET.parse(caminho).getroot()
    totais = ler_totais(raiz)
    quebrados = totais["failures"] + totais["errors"]
    passaram = totais["tests"] - quebrados - totais["skipped"]
    icone = "white_check_mark" if quebrados == 0 else "x"

    print(f"## :{icone}: Testes unitarios\n")
    print("| Total | Passaram | Falharam | Pulados | Tempo |")
    print("| --- | --- | --- | --- | --- |")
    print(
        f"| {totais['tests']} | {passaram} | {quebrados} "
        f"| {totais['skipped']} | {totais['time']:.2f}s |"
    )

    problemas = listar_problemas(raiz)
    if problemas:
        print("\n### Testes que falharam\n")
        for nome, mensagem in problemas:
            primeira = mensagem.splitlines()[0] if mensagem else "sem mensagem"
            print(f"- `{nome}` - {primeira}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
