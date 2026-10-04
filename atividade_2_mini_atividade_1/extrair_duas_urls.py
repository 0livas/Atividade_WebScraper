"""Extrai o conteúdo estruturado de duas URLs e gera um CSV para cada uma."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CAMPOS = ["url_origem", "tipo", "indice", "rotulo", "conteudo", "url_destino"]


def extrair(url: str) -> list[dict[str, str | int]]:
    resposta = requests.get(
        url, timeout=30, headers={"User-Agent": "Atividade-WebScraper/1.0"}
    )
    resposta.raise_for_status()
    soup = BeautifulSoup(resposta.text, "html.parser")
    registros: list[dict[str, str | int]] = []

    titulo = soup.title.get_text(" ", strip=True) if soup.title else ""
    registros.append({"url_origem": url, "tipo": "titulo_pagina", "indice": 1,
                      "rotulo": "title", "conteudo": titulo, "url_destino": ""})

    seletores = {"titulo": "h1, h2, h3, h4, h5, h6", "paragrafo": "p", "item": "li"}
    for tipo, seletor in seletores.items():
        for indice, elemento in enumerate(soup.select(seletor), start=1):
            conteudo = elemento.get_text(" ", strip=True)
            if conteudo:
                registros.append({"url_origem": url, "tipo": tipo, "indice": indice,
                                  "rotulo": elemento.name, "conteudo": conteudo,
                                  "url_destino": ""})

    for indice, ancora in enumerate(soup.select("a[href]"), start=1):
        registros.append({"url_origem": url, "tipo": "link", "indice": indice,
                          "rotulo": ancora.get_text(" ", strip=True), "conteudo": "",
                          "url_destino": urljoin(url, ancora["href"])})

    for indice, tabela in enumerate(soup.select("table"), start=1):
        for linha in tabela.select("tr"):
            celulas = [c.get_text(" ", strip=True) for c in linha.select("th, td")]
            if celulas:
                registros.append({"url_origem": url, "tipo": "tabela", "indice": indice,
                                  "rotulo": "linha", "conteudo": " | ".join(celulas),
                                  "url_destino": ""})
    return registros


def salvar(registros: list[dict[str, str | int]], destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS, delimiter=";")
        escritor.writeheader()
        escritor.writerows(registros)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", action="append", required=True, help="Informe duas vezes")
    parser.add_argument("--saida", action="append", type=Path, required=True, help="Informe duas vezes")
    args = parser.parse_args()
    if len(args.url) != 2 or len(args.saida) != 2:
        parser.error("informe exatamente duas --url e duas --saida")
    for url, destino in zip(args.url, args.saida):
        registros = extrair(url)
        salvar(registros, destino)
        print(f"{len(registros)} registros de {url} salvos em {destino}")


if __name__ == "__main__":
    main()

