from pathlib import Path

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd

from .config import (
    LIMITE_AMARELO,
    LIMITE_PENALIDADE_ALERTA,
    LIMITE_VERDE,
    PENALIDADE_ALERTA,
    RAIO_ALERTA_ROTA_M,
)

TRATADOS = Path(__file__).resolve().parents[1] / "data" / "tratados"


def _contar_alertas_proximos(edge_ids, alertas):
    if alertas is None or alertas.empty:
        return 0

    if "id" in alertas.columns:
        alertas = alertas.drop_duplicates(subset="id")

    lat = pd.to_numeric(alertas["lat"], errors="raise")
    lon = pd.to_numeric(alertas["lon"], errors="raise")
    if not (lat.between(-90, 90) & lon.between(-180, 180)).all():
        raise ValueError("Há alertas com coordenadas ausentes ou inválidas.")

    grafo = ox.io.load_graphml(TRATADOS / "grafo_vila_mariana.graphml")
    grafo = ox.projection.project_graph(grafo, to_crs="EPSG:31983")
    arestas = ox.convert.graph_to_gdfs(grafo, nodes=False)

    linhas = arestas.geometry.copy()
    linhas.index = [f"{u}_{v}_{chave}" for u, v, chave in arestas.index]
    linha_rota = linhas.loc[edge_ids].union_all()

    pontos = gpd.GeoSeries(
        gpd.points_from_xy(lon, lat), crs="EPSG:4326"
    ).to_crs(linhas.crs)

    return int(pontos.distance(linha_rota).le(RAIO_ALERTA_ROTA_M).sum())


def avaliar_rota(edge_ids, alertas):
    """Avalia uma rota a partir dos trechos e dos alertas ativos recebidos."""
    edge_ids = list(edge_ids)
    if not edge_ids:
        raise ValueError("A rota precisa ter pelo menos um trecho.")

    arquivo = TRATADOS / "trechos_score.csv"
    dados_piloto = not arquivo.is_file()
    if dados_piloto:
        arquivo = TRATADOS / "trechos_score_piloto.csv"

    scores = pd.read_csv(arquivo, dtype={"edge_id": "string"}).set_index(
        "edge_id", verify_integrity=True
    )
    rota = scores.loc[edge_ids]

    comprimentos = rota["comprimento_m"]
    if not np.isfinite(comprimentos).all() or comprimentos.lt(0).any():
        raise ValueError("A rota contém comprimentos inválidos.")
    if comprimentos.sum() <= 0:
        raise ValueError("O comprimento total da rota precisa ser positivo.")

    media_base = float(np.average(rota["score_base"], weights=comprimentos))
    n_alertas = _contar_alertas_proximos(edge_ids, alertas)
    penalidade = min(n_alertas * PENALIDADE_ALERTA, LIMITE_PENALIDADE_ALERTA)
    score_medio = max(0.0, min(100.0, media_base - penalidade))

    if score_medio >= LIMITE_VERDE:
        cor = "verde"
    elif score_medio >= LIMITE_AMARELO:
        cor = "amarelo"
    else:
        cor = "vermelho"

    n_trechos_com_luz = int(rota["n_luz"].gt(0).sum())
    n_ocorrencias = int(rota["n_ocorrencias"].sum())
    n_trechos_em_hotspot = int(rota["em_hotspot"].eq(1).sum())
    n_trechos_com_abrigos = None if dados_piloto else int(rota["n_abrigos"].gt(0).sum())

    favoraveis = []
    atencao = []
    if n_trechos_com_luz:
        favoraveis.append(f"{n_trechos_com_luz} trechos com iluminação cadastrada próxima.")
    if n_trechos_com_abrigos:
        favoraveis.append(f"{n_trechos_com_abrigos} trechos com locais de apoio próximos.")
    if n_ocorrencias:
        atencao.append(f"{n_ocorrencias} registros de ocorrência associados aos trechos.")
    if n_trechos_em_hotspot:
        atencao.append(f"{n_trechos_em_hotspot} trechos em áreas de concentração de registros.")
    if n_alertas:
        atencao.append(f"{n_alertas} alertas ativos próximos à rota.")
    if dados_piloto:
        atencao.append("Score piloto com dados de locais de apoio pendentes.")

    return {
        "score_medio": score_medio,
        "cor": cor,
        "pior_trecho": str(rota["score_base"].idxmin()),
        "n_alertas_na_rota": n_alertas,
        "penalidade_alertas": penalidade,
        "n_trechos_com_luz": n_trechos_com_luz,
        "n_ocorrencias": n_ocorrencias,
        "n_trechos_com_abrigos": n_trechos_com_abrigos,
        "n_trechos_em_hotspot": n_trechos_em_hotspot,
        "fatores_favoraveis": favoraveis,
        "fatores_atencao": atencao,
        "dados_piloto": dados_piloto,
    }