
from pathlib import Path

import pandas as pd

from src.config import PASTA_DADOS
from datetime import datetime
from zoneinfo import ZoneInfo


ARQUIVO_ROTAS_SALVAS = PASTA_DADOS / "rotas_salvas.csv"

COLUNAS_ROTAS = [
    "apelido",
    "nome",
    "origem_texto",
    "destino_texto",
    "origem_lat",
    "origem_lon",
    "destino_lat",
    "destino_lon",
    "criado_em",
]


def _ler_arquivo_rotas():
    """Lê o CSV de rotas salvas ou retorna uma tabela vazia."""

    if not ARQUIVO_ROTAS_SALVAS.exists():
        return pd.DataFrame(columns=COLUNAS_ROTAS)

    rotas = pd.read_csv(
        ARQUIVO_ROTAS_SALVAS,
        dtype={"apelido": "string", "nome": "string"},
    )

    return rotas.reindex(columns=COLUNAS_ROTAS)



def listar_rotas(apelido):
    """Lista as rotas salvas de um apelido."""

    apelido = apelido.strip()

    if not apelido:
        raise ValueError("Informe um apelido.")

    rotas = _ler_arquivo_rotas()

    return rotas.loc[
        rotas["apelido"] == apelido
    ].copy()


def salvar_rota(apelido, nome, origem, destino):
    """Salva uma rota no CSV, respeitando o limite por apelido."""

    apelido = apelido.strip()
    nome = nome.strip()

    if not apelido or not nome:
        raise ValueError("Informe o apelido e o nome da rota.")

    for ponto in (origem, destino):
        if not all(
            campo in ponto
            for campo in ("texto", "lat", "lon")
        ):
            raise ValueError("Origem ou destino incompleto.")

    rotas = _ler_arquivo_rotas()

    mesma_rota = (
        (rotas["apelido"] == apelido)
        & (rotas["nome"] == nome)
    )

    quantidade = (rotas["apelido"] == apelido).sum()

    if not mesma_rota.any() and quantidade >= 10:
        raise ValueError(
            "Limite de 10 rotas por apelido atingido."
        )

    rotas = rotas.loc[~mesma_rota].copy()

    nova_rota = {
        "apelido": apelido,
        "nome": nome,
        "origem_texto": origem["texto"],
        "destino_texto": destino["texto"],
        "origem_lat": float(origem["lat"]),
        "origem_lon": float(origem["lon"]),
        "destino_lat": float(destino["lat"]),
        "destino_lon": float(destino["lon"]),
        "criado_em": datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).isoformat(timespec="seconds"),
    }

    rotas = pd.concat(
        [rotas, pd.DataFrame([nova_rota])],
        ignore_index=True,
    )

    ARQUIVO_ROTAS_SALVAS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rotas.to_csv(
        ARQUIVO_ROTAS_SALVAS,
        index=False,
        encoding="utf-8",
    )

    return True

def excluir_rota(apelido, nome):
    """Exclui uma rota salva pelo apelido e nome."""

    apelido = apelido.strip()
    nome = nome.strip()

    if not apelido or not nome:
        raise ValueError("Informe o apelido e o nome da rota.")

    rotas = _ler_arquivo_rotas()

    encontrada = (
        (rotas["apelido"] == apelido)
        & (rotas["nome"] == nome)
    )

    if not encontrada.any():
        return False

    rotas = rotas.loc[~encontrada].copy()

    rotas.to_csv(
        ARQUIVO_ROTAS_SALVAS,
        index=False,
        encoding="utf-8",
    )


    return True