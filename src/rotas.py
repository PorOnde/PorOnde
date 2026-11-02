"""Cálculo de rotas a pé na Vila Mariana."""
import math
from src.abrigos import listar_abrigos
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
def localizar_endereco(endereco):
    """Localiza um endereço e devolve latitude e longitude."""
    try:
        local = ox.geocode_to_gdf(f"{endereco}, São Paulo, SP, Brasil")
    except Exception as erro:
        raise ValueError(
            "Não foi possível localizar esse endereço. "
            "Tente informar rua, número e bairro."
        ) from erro

    ponto = local.geometry.iloc[0].centroid
    latitude = ponto.y
    longitude = ponto.x

    _validar_coordenada(latitude, longitude)

    return latitude, longitude

def _distancia_em_metros(lat1, lon1, lat2, lon2):
    """Calcula a distância aproximada entre dois pontos."""
    raio_terra = 6_371_000

    latitude_1 = math.radians(lat1)
    latitude_2 = math.radians(lat2)
    diferenca_latitude = math.radians(lat2 - lat1)
    diferenca_longitude = math.radians(lon2 - lon1)

    valor = (
        math.sin(diferenca_latitude / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(diferenca_longitude / 2) ** 2
    )

    return 2 * raio_terra * math.atan2(math.sqrt(valor), math.sqrt(1 - valor))


def locais_apoio_proximos(nos_da_rota, raio_metros=200):
    """Lista locais de apoio que ficam próximos ao trajeto."""
    coordenadas = coordenadas_da_rota(nos_da_rota)
    abrigos = listar_abrigos()
    proximos = []

    for _, abrigo in abrigos.iterrows():
        menor_distancia = min(
            _distancia_em_metros(
                abrigo["lat"],
                abrigo["lon"],
                latitude,
                longitude,
            )
            for longitude, latitude in coordenadas
        )

        if menor_distancia <= raio_metros:
            proximos.append(
                {
                    "nome": abrigo["nome"],
                    "tipo": abrigo["tipo"],
                    "grupo": abrigo["grupo"],
                    "lat": abrigo["lat"],
                    "lon": abrigo["lon"],
                    "distancia_metros": round(menor_distancia),
                }
            )

    proximos_ordenados = sorted(
        proximos,
        key=lambda local: local["distancia_metros"],
    )

    selecionados = []
    grupos_mostrados = set()
    nomes_mostrados = set()

    for local in proximos_ordenados:
        if (
            local["grupo"] not in grupos_mostrados
            and local["nome"] not in nomes_mostrados
        ):
            selecionados.append(local)
            grupos_mostrados.add(local["grupo"])
            nomes_mostrados.add(local["nome"])

    for local in proximos_ordenados:
        if len(selecionados) == 5:
            break

        if local["nome"] not in nomes_mostrados:
            selecionados.append(local)
            nomes_mostrados.add(local["nome"])

    return selecionados