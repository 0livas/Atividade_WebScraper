"""Baixa tirinhas do XKCD seguindo o link Previous Comic até a primeira."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

INICIO = "https://xkcd.com/"


def nome_seguro(url: str, numero: str) -> str:
    nome = Path(urlparse(url).path).name or f"{numero}.img"
    nome = re.sub(r"[^A-Za-z0-9._-]", "_", nome)
    return f"{numero}_{nome}"


def baixar(destino: Path, limite: int | None = None, inicio: str = INICIO) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    sessao = requests.Session()
    sessao.headers.update({"User-Agent": "Atividade-WebScraper/1.0 (atividade academica)"})
    url = inicio
    quantidade = 0

    while url and (limite is None or quantidade < limite):
        resposta = sessao.get(url, timeout=30)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, "html.parser")
        imagem = soup.select_one("#comic img")
        if imagem is None or not imagem.get("src"):
            print(f"Nenhuma tirinha encontrada em {url}")
            break

        imagem_url = urljoin(url, imagem["src"])
        numero = urlparse(resposta.url).path.strip("/") or "atual"
        arquivo = destino / nome_seguro(imagem_url, numero)
        with sessao.get(imagem_url, stream=True, timeout=30) as conteudo:
            conteudo.raise_for_status()
            with arquivo.open("wb") as saida:
                for bloco in conteudo.iter_content(chunk_size=8192):
                    if bloco:
                        saida.write(bloco)
        quantidade += 1
        print(f"[{quantidade}] {arquivo.name}")

        anterior = soup.select_one('a[rel="prev"]') or soup.find("a", string="< Prev")
        if anterior is None or not anterior.get("href") or anterior["href"] == "#":
            break
        proxima_url = urljoin(url, anterior["href"])
        if proxima_url == url:
            break
        url = proxima_url
    return quantidade


def main() -> None:
    padrao = Path(__file__).parent / "tirinhas"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=padrao)
    parser.add_argument("--limite", type=int)
    parser.add_argument("--inicio", default=INICIO)
    args = parser.parse_args()
    if args.limite is not None and args.limite < 1:
        parser.error("--limite deve ser maior que zero")
    total = baixar(args.destino, args.limite, args.inicio)
    print(f"Concluído: {total} tirinhas salvas em {args.destino}")


if __name__ == "__main__":
    main()

