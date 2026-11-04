"""Cálculo de rotas a pé na Vila Mariana."""
import json
import math
import time
import pandas as pd
from src.abrigos import listar_abrigos
import networkx as nx
import osmnx as ox

from src import config
from src.grafo import carregar_grafo


VELOCIDADE_MEDIA_METROS_POR_MINUTO = 80

def aplicar_scores_ao_grafo(grafo):
    """Lê o CSV de score e adiciona os dados a cada trecho do grafo."""

    if not config.ARQUIVO_SCORE.exists():
        raise FileNotFoundError(
            "Não foi encontrado nenhum arquivo de score para os trechos."
        )

    tabela_scores = pd.read_csv(config.ARQUIVO_SCORE)

    colunas_obrigatorias = {
        "edge_id",
        "nome_rua",
        "comprimento_m",
        "lat_meio",
        "lon_meio",
        "n_luz",
        "n_ocorrencias",
        "n_abrigos",
        "em_hotspot",
        "score_iluminacao",
        "score_base",
        "cor",
    }

    colunas_ausentes = colunas_obrigatorias - set(tabela_scores.columns)

    if colunas_ausentes:
        raise ValueError(
            "O arquivo de score está sem as colunas: "
            f"{sorted(colunas_ausentes)}"
        )

    if tabela_scores["edge_id"].duplicated().any():
        raise ValueError(
            "O arquivo de score possui edge_id duplicado."
        )

    scores_por_trecho = tabela_scores.set_index("edge_id")
    trechos_sem_score = []

    for no_origem, no_destino, chave, dados in grafo.edges(
        keys=True,
        data=True,
    ):
        edge_id = f"{no_origem}_{no_destino}_{chave}"

        if edge_id not in scores_por_trecho.index:
            trechos_sem_score.append(edge_id)
            continue

        score = scores_por_trecho.loc[edge_id]

        dados["score_iluminacao"] = float(
            score["score_iluminacao"]
        )
        dados["score_base"] = float(score["score_base"])
        dados["cor"] = str(score["cor"])

        dados["n_luz"] = int(score["n_luz"])
        dados["n_ocorrencias"] = int(score["n_ocorrencias"])
        dados["n_abrigos"] = int(score["n_abrigos"])
        dados["em_hotspot"] = int(score["em_hotspot"])

    if trechos_sem_score:
        raise ValueError(
            "Existem trechos do grafo sem score: "
            f"{len(trechos_sem_score)}"
        )


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
    aplicar_scores_ao_grafo(grafo)

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
def _normalizar_endereco(endereco):
    """Cria uma chave padronizada para o cache."""
    return " ".join(endereco.lower().split())


def _ler_cache_geocodificacao():
    """Lê os endereços já consultados, se existirem."""
    if not config.ARQUIVO_CACHE_GEOCODIFICACAO.exists():
        return {}

    try:
        with open(
            config.ARQUIVO_CACHE_GEOCODIFICACAO,
            "r",
            encoding="utf-8",
        ) as arquivo:
            cache = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return {}

    return cache if isinstance(cache, dict) else {}


def _salvar_cache_geocodificacao(cache):
    """Salva no disco os endereços localizados."""
    config.PASTA_CACHE.mkdir(parents=True, exist_ok=True)

    with open(
        config.ARQUIVO_CACHE_GEOCODIFICACAO,
        "w",
        encoding="utf-8",
    ) as arquivo:
        json.dump(
            cache,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )


def localizar_endereco(endereco):
    """Localiza um endereço e usa cache para evitar consultas repetidas."""
    endereco = endereco.strip()

    if not endereco:
        raise ValueError("Informe um endereço.")

    chave = _normalizar_endereco(endereco)
    cache = _ler_cache_geocodificacao()

    if chave in cache:
        latitude = float(cache[chave]["latitude"])
        longitude = float(cache[chave]["longitude"])
        _validar_coordenada(latitude, longitude)
        return latitude, longitude

    try:
        time.sleep(1)
        local = ox.geocode_to_gdf(
            f"{endereco}, São Paulo, SP, Brasil"
        )
    except Exception as erro:
        raise ValueError(
            "Não foi possível localizar esse endereço. "
            "Tente informar rua, número e bairro."
        ) from erro

    if local.empty:
        raise ValueError(
            "Não foi possível localizar esse endereço. "
            "Tente informar rua, número e bairro."
        )

    ponto = local.geometry.iloc[0].centroid
    latitude = float(ponto.y)
    longitude = float(ponto.x)

    _validar_coordenada(latitude, longitude)

    cache[chave] = {
        "latitude": latitude,
        "longitude": longitude,
    }
    _salvar_cache_geocodificacao(cache)

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