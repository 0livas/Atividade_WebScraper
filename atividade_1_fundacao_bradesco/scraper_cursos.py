"""Coleta o catálogo de cursos da Escola Virtual Fundação Bradesco."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://www.ev.org.br"
CATALOGO_URL = f"{BASE_URL}/cursos"
CAMPOS = [
    "titulo",
    "area_tema",
    "descricao",
    "carga_horaria",
    "nivel_dificuldade",
    "link_direto",
    "conteudo",
    "detalhes",
]


def texto(elemento: Tag | None) -> str:
    """volta o texto normalizado de um elemento HTML."""
    return elemento.get_text(" ", strip=True) if elemento else ""


def criar_sessao() -> requests.Session:
    sessao = requests.Session()
    sessao.headers.update(
        {"User-Agent": "Atividade-WebScraper/1.0 (atividade academica)"}
    )
    return sessao


def baixar_html(sessao: requests.Session, url: str) -> BeautifulSoup:
    resposta = sessao.get(url, timeout=30)
    resposta.raise_for_status()
    return BeautifulSoup(resposta.text, "html.parser")


def links_do_catalogo(sessao: requests.Session) -> list[str]:
    """Percorre a paginação e devolve links únicos de todos os cursos."""
    links: list[str] = []
    vistos: set[str] = set()
    pagina = 1

    while True:
        soup = baixar_html(sessao, CATALOGO_URL)
        if pagina > 1:
            soup = baixar_html(sessao, f"{CATALOGO_URL}?pagina={pagina}")

        novos = []
        for cartao in soup.select("article.m-card"):
            ancora = cartao.select_one("a.m-card_link[href]")
            if ancora:
                link = urljoin(BASE_URL, ancora["href"])
                if link not in vistos:
                    vistos.add(link)
                    links.append(link)
                    novos.append(link)

        if not novos:
            break
        pagina += 1

    return links


def extrair_detalhes(sessao: requests.Session, url: str) -> dict[str, str]:
    soup = baixar_html(sessao, url)
    informacoes = soup.select(".o-internal-desc_info .m-info_desc")
    carga = texto(informacoes[0].find("strong")) if informacoes else ""
    nivel = texto(informacoes[1].find("strong")) if len(informacoes) > 1 else ""

    conteudo = soup.select_one("#eenie")
    detalhes: list[str] = []
    for bloco in soup.select("#meenie .o-tabs_txt"):
        chave = texto(bloco.select_one(".o-tabs_title"))
        valor = texto(bloco.select_one(".o-tabs_desc"))
        if chave or valor:
            detalhes.append(f"{chave}: {valor}" if chave else valor)

    return {
        "titulo": texto(soup.select_one("h1.o-internal-desc_title")),
        "area_tema": texto(soup.select_one(".m-head-title_title")),
        "descricao": texto(soup.select_one(".o-internal-desc_txt")),
        "carga_horaria": carga,
        "nivel_dificuldade": nivel,
        "link_direto": url,
        "conteudo": texto(conteudo),
        "detalhes": " | ".join(detalhes),
    }


def salvar_csv(cursos: list[dict[str, str]], destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS, delimiter=";")
        escritor.writeheader()
        escritor.writerows(cursos)


def executar(destino: Path, pausa: float = 0.15) -> int:
    sessao = criar_sessao()
    links = links_do_catalogo(sessao)
    cursos = []
    for indice, link in enumerate(links, start=1):
        try:
            cursos.append(extrair_detalhes(sessao, link))
            print(f"[{indice}/{len(links)}] {cursos[-1]['titulo']}")
        except requests.RequestException as erro:
            print(f"Falha em {link}: {erro}")
        time.sleep(pausa)
    salvar_csv(cursos, destino)
    return len(cursos)


def main() -> None:
    padrao = Path(__file__).parent / "saida" / "cursos_fundacao_bradesco.csv"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=padrao)
    parser.add_argument("--pausa", type=float, default=0.15)
    args = parser.parse_args()
    total = executar(args.saida, args.pausa)
    print(f"Concluído: {total} cursos salvos em {args.saida}")


if __name__ == "__main__":
    main()

