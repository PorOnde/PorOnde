"""Gera scores fictícios para desenvolver as rotas antes da Parte A."""

import random

import pandas as pd

from src import config
from src.grafo import carregar_grafo


def _nome_rua(valor):
    if valor is None:
        return ""

    if isinstance(valor, list):
        return " / ".join(str(nome) for nome in valor)

    return str(valor)


def _cor_do_score(score):
    if score >= 70:
        return "verde"

    if score >= 40:
        return "amarelo"

    return "vermelho"


def gerar_score_exemplo():
    grafo = carregar_grafo()
    sorteio = random.Random(42)
    linhas = []

    for no_origem, no_destino, chave, dados in grafo.edges(
        keys=True,
        data=True,
    ):
        latitude_meio = (
            float(grafo.nodes[no_origem]["y"])
            + float(grafo.nodes[no_destino]["y"])
        ) / 2

        longitude_meio = (
            float(grafo.nodes[no_origem]["x"])
            + float(grafo.nodes[no_destino]["x"])
        ) / 2

        score_iluminacao = sorteio.randint(20, 100)
        score_base = sorteio.randint(20, 100)

        linhas.append(
            {
                "edge_id": f"{no_origem}_{no_destino}_{chave}",
                "nome_rua": _nome_rua(dados.get("name")),
                "comprimento_m": round(float(dados.get("length", 0)), 2),
                "lat_meio": latitude_meio,
                "lon_meio": longitude_meio,
                "n_luz": sorteio.randint(0, 5),
                "n_ocorrencias": sorteio.randint(0, 3),
                "n_abrigos": sorteio.randint(0, 3),
                "em_hotspot": sorteio.randint(0, 1),
                "score_iluminacao": score_iluminacao,
                "score_base": score_base,
                "cor": _cor_do_score(score_base),
            }
        )

    tabela_scores = pd.DataFrame(linhas)

    config.PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)
    tabela_scores.to_csv(
        config.ARQUIVO_SCORE_EXEMPLO,
        index=False,
        encoding="utf-8",
    )

    return tabela_scores


if __name__ == "__main__":
    tabela_gerada = gerar_score_exemplo()

    print(f"Arquivo criado: {config.ARQUIVO_SCORE_EXEMPLO}")
    print(f"Trechos com score de exemplo: {len(tabela_gerada)}")