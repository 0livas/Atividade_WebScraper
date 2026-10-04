"""Extrai programas de pós-graduação da API pública Sucupira."""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

QUANTIDADE = 500 # Quantidade de programas que o usuário queira extrair, limitado à 500 por causa da API.
API = "https://apigw-proxy.capes.gov.br/observatorio/data/online/ppg"
CAMPOS = [
    "codigo", "areaBasica", "areaAvaliacao", "situacao", "cidade",
    "mestrado", "nota", "situacaoMestrado", "doutorado", "codigoMestrado",
    "situacaoDoutorado", "notaMestrado", "codigoDoutorado", "cep", "inicio",
    "universidade",
]


def requisitar_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    resposta = requests.get(
        url,
        params=params,
        timeout=40,
        headers={"User-Agent": "Atividade-WebScraper/1.0 (atividade academica)"},
    )
    resposta.raise_for_status()
    return resposta.json()


def buscar_programas(limite: int) -> list[dict[str, Any]]:
    dados = requisitar_json(API, {"page": 0, "size": limite})
    return dados.get("content", [])[:limite]


def curso_por_grau(cursos: list[dict[str, Any]], grau: str) -> dict[str, Any]:
    return next((curso for curso in cursos if grau.lower() in curso.get("grau", "").lower()), {})


def normalizar(detalhe: dict[str, Any]) -> dict[str, Any]:
    online = detalhe.get("online") or {}
    cursos = online.get("cursos") or []
    mestrado = curso_por_grau(cursos, "mestrado")
    doutorado = curso_por_grau(cursos, "doutorado")
    instituicoes = online.get("instituicoes") or []
    principal = next((item for item in instituicoes if item.get("principal") == 1), {})

    return {
        "codigo": online.get("codigo") or detalhe.get("codigo", ""),
        "areaBasica": online.get("nomeAreaConhecimento") or detalhe.get("nomeAreaConhecimento", ""),
        "areaAvaliacao": online.get("nomeAreaAvaliacao") or detalhe.get("nomeAreaAvaliacao", ""),
        "situacao": online.get("situacao") or detalhe.get("situacao", ""),
        "cidade": online.get("endMunicipio", ""),
        "mestrado": "Sim" if mestrado else "Não",
        "nota": online.get("conceito") or detalhe.get("conceito", ""),
        "situacaoMestrado": mestrado.get("situacao", ""),
        "doutorado": "Sim" if doutorado else "Não",
        "codigoMestrado": mestrado.get("codigo", ""),
        "situacaoDoutorado": doutorado.get("situacao", ""),
        "notaMestrado": mestrado.get("conceito", ""),
        "codigoDoutorado": doutorado.get("codigo", ""),
        "cep": online.get("endCep", ""),
        "inicio": online.get("anoInicio") or mestrado.get("dataInicio") or doutorado.get("dataInicio", ""),
        "universidade": principal.get("nomeIes") or online.get("siglaIes") or detalhe.get("siglaIes", ""),
    }


def buscar_detalhe(programa: dict[str, Any]) -> dict[str, Any]:
    identificador = programa.get("idPrograma") or programa.get("id")
    return requisitar_json(f"{API}/{identificador}")


def coletar(limite: int, trabalhadores: int) -> list[dict[str, Any]]:
    programas = buscar_programas(limite)
    resultados: list[dict[str, Any] | None] = [None] * len(programas)
    with ThreadPoolExecutor(max_workers=trabalhadores) as executor:
        futuros = {executor.submit(buscar_detalhe, p): i for i, p in enumerate(programas)}
        for concluido, futuro in enumerate(as_completed(futuros), start=1):
            indice = futuros[futuro]
            try:
                resultados[indice] = normalizar(futuro.result())
                print(f"[{concluido}/{len(programas)}] {resultados[indice]['codigo']}")
            except (requests.RequestException, ValueError) as erro:
                print(f"Falha no programa {programas[indice].get('idPrograma')}: {erro}")
    return [registro for registro in resultados if registro is not None]


def salvar_csv(registros: list[dict[str, Any]], destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS, delimiter=";")
        escritor.writeheader()
        escritor.writerows(registros)


def main() -> None:
    padrao = Path(__file__).parent / "saida" / "programas_sucupira.csv"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limite", type=int, default=QUANTIDADE)
    parser.add_argument("--trabalhadores", type=int, default=8)
    parser.add_argument("--saida", type=Path, default=padrao)
    args = parser.parse_args()
    if not 1 <= args.limite <= QUANTIDADE:
        parser.error(f"--limite deve estar entre 1 e {QUANTIDADE}")
    registros = coletar(args.limite, args.trabalhadores)
    salvar_csv(registros, args.saida)
    print(f"Concluído: {len(registros)} registros salvos em {args.saida}")


if __name__ == "__main__":
    main()

