"""Cálculo de rotas a pé na Vila Mariana."""

import networkx as nx
import osmnx as ox

from src import config
from src.grafo import carregar_grafo


VELOCIDADE_MEDIA_METROS_POR_MINUTO = 80


def _validar_coordenada(latitude, longitude):
    sul, norte, oeste, leste = config.BBOX_VM

    dentro_da_area = (
        sul <= latitude <= norte
        and oeste <= longitude <= leste
    )

    if not dentro_da_area:
        raise ValueError(
            "Os pontos da rota precisam estar dentro da Vila Mariana."
        )


def calcular_rota(
    latitude_origem,
    longitude_origem,
    latitude_destino,
    longitude_destino,
):
    """Calcula a rota a pé mais curta entre dois pontos."""

    _validar_coordenada(latitude_origem, longitude_origem)
    _validar_coordenada(latitude_destino, longitude_destino)

    grafo = carregar_grafo()

    no_origem = ox.distance.nearest_nodes(
        grafo,
        X=longitude_origem,
        Y=latitude_origem,
    )

    no_destino = ox.distance.nearest_nodes(
        grafo,
        X=longitude_destino,
        Y=latitude_destino,
    )

    try:
        nos_da_rota = nx.shortest_path(
            grafo,
            no_origem,
            no_destino,
            weight="length",
        )
    except nx.NetworkXNoPath as erro:
        raise ValueError("Não foi possível calcular uma rota entre os pontos.") from erro

    distancia_metros = nx.shortest_path_length(
        grafo,
        no_origem,
        no_destino,
        weight="length",
    )

    tempo_minutos = distancia_metros / VELOCIDADE_MEDIA_METROS_POR_MINUTO

    return {
        "nos": nos_da_rota,
        "distancia_metros": round(distancia_metros),
        "tempo_minutos": round(tempo_minutos, 1),
    }


def rota_para_geodataframe(nos_da_rota):
    """Converte os trechos de uma rota para um GeoDataFrame."""

    grafo = carregar_grafo()

    return ox.routing.route_to_gdf(
        grafo,
        nos_da_rota,
        weight="length",
    )
def coordenadas_da_rota(nos_da_rota):
    """Devolve os pontos da rota no formato longitude e latitude."""

    grafo = carregar_grafo()

    return [
        [
            grafo.nodes[no]["x"],
            grafo.nodes[no]["y"],
        ]
        for no in nos_da_rota
    ]