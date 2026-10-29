import math
import random
from datetime import datetime, timedelta

import pandas as pd

from src.banco import conectar, criar_tabelas
from src.config import MODO_DADOS


COLUNAS_ALERTAS = [
    "id",
    "categoria",
    "descricao",
    "lat",
    "lon",
    "criado_em",
    "expira_em",
    "confirmacoes",
    "rejeicoes",
    "saldo",
    "simulado",
]


def _exigir_modo_demo():
    if MODO_DADOS != "demo":
        raise RuntimeError(
            "Relatos simulados só podem ser usados no modo demonstração."
        )


def _obter_bbox_vm():
    try:
        from src.config import BBOX_VM
    except ImportError as erro:
        raise RuntimeError(
            "BBOX_VM ainda não foi definido pela parte do grafo."
        ) from erro

    return BBOX_VM


def _ponto_no_bbox(sul, norte, oeste, leste, percentual_lat, percentual_lon):
    lat = sul + (norte - sul) * percentual_lat
    lon = oeste + (leste - oeste) * percentual_lon
    return lat, lon


def _ponto_proximo(lat, lon, metros_lat, metros_lon):
    novo_lat = lat + metros_lat / 111_320
    novo_lon = lon + metros_lon / (111_320 * math.cos(math.radians(lat)))
    return novo_lat, novo_lon


def limpar_simulados():
    _exigir_modo_demo()
    criar_tabelas()

    with conectar() as conexao:
        resultado = conexao.execute(
            "DELETE FROM relatos WHERE simulado = 1"
        )

    return resultado.rowcount


def gerar_relatos_simulados(semente=42):
    _exigir_modo_demo()
    criar_tabelas()

    sul, norte, oeste, leste = _obter_bbox_vm()
    gerador = random.Random(semente)
    agora = datetime.now()

    limpar_simulados()

    relatos = []

    grupos_ativos = [
        ("Rua mal iluminada ou escura", 0.20, 0.25),
        ("Via bloqueada ou obra", 0.50, 0.55),
        ("Aglomeração ou tumulto", 0.75, 0.35),
    ]

    for numero_grupo, (categoria, percentual_lat, percentual_lon) in enumerate(
        grupos_ativos, start=1
    ):
        lat_centro, lon_centro = _ponto_no_bbox(
            sul,
            norte,
            oeste,
            leste,
            percentual_lat,
            percentual_lon,
        )

        for numero_relato in range(1, 3):
            deslocamento_lat = gerador.uniform(-30, 30)
            deslocamento_lon = gerador.uniform(-30, 30)
            lat, lon = _ponto_proximo(
                lat_centro,
                lon_centro,
                deslocamento_lat,
                deslocamento_lon,
            )

            relatos.append(
                (
                    categoria,
                    f"Relato simulado do grupo ativo {numero_grupo}.",
                    lat,
                    lon,
                    agora.isoformat(timespec="seconds"),
                    (agora + timedelta(hours=12)).isoformat(timespec="seconds"),
                    "ativo",
                    0,
                    0,
                    f"demo_ativo_{numero_grupo}_{numero_relato}",
                    1,
                )
            )

    categorias_pendentes = [
        "Outro",
        "Transporte com problema (ônibus ou metrô)",
        "Rua mal iluminada ou escura",
        "Via bloqueada ou obra",
        "Aglomeração ou tumulto",
    ]

    for numero, categoria in enumerate(categorias_pendentes, start=1):
        lat, lon = _ponto_no_bbox(
            sul,
            norte,
            oeste,
            leste,
            0.12 + numero * 0.13,
            0.82,
        )

        relatos.append(
            (
                categoria,
                f"Relato simulado isolado {numero}.",
                lat,
                lon,
                agora.isoformat(timespec="seconds"),
                (agora + timedelta(hours=12)).isoformat(timespec="seconds"),
                "pendente",
                0,
                0,
                f"demo_pendente_{numero}",
                1,
            )
        )

    for numero in range(1, 3):
        lat, lon = _ponto_no_bbox(
            sul,
            norte,
            oeste,
            leste,
            0.25 + numero * 0.20,
            0.12,
        )

        relatos.append(
            (
                "Outro",
                f"Relato simulado rejeitado {numero}.",
                lat,
                lon,
                agora.isoformat(timespec="seconds"),
                (agora + timedelta(hours=12)).isoformat(timespec="seconds"),
                "rejeitado",
                0,
                1,
                f"demo_rejeitado_{numero}",
                1,
            )
        )

    for numero in range(1, 3):
        lat, lon = _ponto_no_bbox(
            sul,
            norte,
            oeste,
            leste,
            0.30 + numero * 0.22,
            0.90,
        )

        criado_em = agora - timedelta(hours=26)
        expira_em = agora - timedelta(hours=2)

        relatos.append(
            (
                "Rua mal iluminada ou escura",
                f"Relato simulado expirado {numero}.",
                lat,
                lon,
                criado_em.isoformat(timespec="seconds"),
                expira_em.isoformat(timespec="seconds"),
                "expirado",
                0,
                0,
                f"demo_expirado_{numero}",
                1,
            )
        )

    with conectar() as conexao:
        conexao.executemany(
            """
            INSERT INTO relatos (
                categoria, descricao, lat, lon, criado_em, expira_em,
                status, confirmacoes, rejeicoes, id_sessao, simulado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            relatos,
        )

    return len(relatos)


def listar_alertas_ativos():
    criar_tabelas()

    with conectar() as conexao:
        alertas = pd.read_sql_query(
            """
            SELECT
                id,
                categoria,
                descricao,
                lat,
                lon,
                criado_em,
                expira_em,
                confirmacoes,
                rejeicoes,
                confirmacoes - rejeicoes AS saldo,
                simulado
            FROM relatos
            WHERE status = 'ativo'
            ORDER BY criado_em DESC, id DESC
            """,
            conexao,
        )

    return alertas.reindex(columns=COLUNAS_ALERTAS)