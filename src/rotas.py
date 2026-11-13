"""Cálculo de rotas a pé na Vila Mariana."""
import json
import math
import time

import networkx as nx
import osmnx as ox
import pandas as pd

from src import config
from src.abrigos import listar_abrigos
from src.grafo import carregar_grafo
from src.score import avaliar_rota
from src.supabase_db import listar_alertas_ativos_supabase


VELOCIDADE_MEDIA_METROS_POR_MINUTO = 80
FATOR_MAXIMO_ALTERNATIVA = 1.4
LIMITE_CANDIDATOS_ALTERNATIVAS = 30
FRACAO_MINIMA_DIFERENTE = 0.30


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

    colunas_ausentes = colunas_obrigatorias - set(
        tabela_scores.columns
    )

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


def criar_grafo_simples_para_alternativas(grafo):
    """Converte o multigrafo em um grafo simples para gerar caminhos."""
    grafo_simples = nx.DiGraph()

    for no_origem, no_destino, chave, dados in grafo.edges(
        keys=True,
        data=True,
    ):
        comprimento = float(dados.get("length", 0))

        if (
            not grafo_simples.has_edge(no_origem, no_destino)
            or comprimento
            < grafo_simples[no_origem][no_destino]["length"]
        ):
            grafo_simples.add_edge(
                no_origem,
                no_destino,
                length=comprimento,
                origem_no=no_origem,
                destino_no=no_destino,
                score_iluminacao=float(
                    dados.get("score_iluminacao", 0)
                ),
                score_base=float(dados.get("score_base", 0)),
                n_luz=int(dados.get("n_luz", 0)),
                n_ocorrencias=int(dados.get("n_ocorrencias", 0)),
                n_abrigos=int(dados.get("n_abrigos", 0)),
                em_hotspot=int(dados.get("em_hotspot", 0)),
                edge_id=f"{no_origem}_{no_destino}_{chave}",
            )

    return grafo_simples


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
        raise ValueError(
            "Não foi possível calcular uma rota entre os pontos."
        ) from erro

    distancia_metros = nx.shortest_path_length(
        grafo,
        no_origem,
        no_destino,
        weight="length",
    )

    tempo_minutos = (
        distancia_metros / VELOCIDADE_MEDIA_METROS_POR_MINUTO
    )

    return {
        "nos": nos_da_rota,
        "distancia_metros": round(distancia_metros),
        "tempo_minutos": round(tempo_minutos, 1),
    }


def _distancia_da_rota(grafo, nos_da_rota):
    """Soma o comprimento dos trechos usados pela rota."""
    distancia = 0

    for no_origem, no_destino in zip(
        nos_da_rota,
        nos_da_rota[1:],
    ):
        opcoes = grafo.get_edge_data(no_origem, no_destino)

        if not opcoes:
            raise ValueError(
                "Não foi possível medir um trecho da rota."
            )

        if grafo.is_multigraph():
            trecho = min(
                opcoes.values(),
                key=lambda dados: float(dados.get("length", 0)),
            )
            distancia += float(trecho.get("length", 0))
        else:
            distancia += float(opcoes.get("length", 0))

    return distancia


def _score_medio_da_rota(grafo, nos_da_rota, campo_score):
    """Calcula a média ponderada de um score pelos trechos da rota."""
    total_pontos = 0
    total_comprimento = 0

    for no_origem, no_destino in zip(
        nos_da_rota,
        nos_da_rota[1:],
    ):
        dados = grafo[no_origem][no_destino]
        comprimento = float(dados.get("length", 0))
        score = float(dados.get(campo_score, 0))

        total_pontos += comprimento * score
        total_comprimento += comprimento

    if total_comprimento == 0:
        return 0

    return total_pontos / total_comprimento
def _identificar_pior_trecho(grafo, nos_da_rota):
    """Identifica o trecho com menor score de contexto."""

    pior_trecho = None

    for origem, destino in zip(nos_da_rota, nos_da_rota[1:]):
        dados = grafo[origem][destino]
        score = float(dados.get("score_base", 0))

        if pior_trecho is None or score < pior_trecho["score"]:
            pior_trecho = {
                "origem_no": origem,
                "destino_no": destino,
                "score": round(score, 1),
                "n_luz": int(dados.get("n_luz", 0)),
                "n_ocorrencias": int(dados.get("n_ocorrencias", 0)),
                "n_abrigos": int(dados.get("n_abrigos", 0)),
                "em_hotspot": int(dados.get("em_hotspot", 0)),
            }

    return pior_trecho

def _analisar_fatores_rota(candidata):
    """Organiza os indicadores disponíveis para explicar a rota."""

    return {
        "score_iluminacao": round(candidata["score_iluminacao"], 1),
        "score_contexto": round(candidata["score_contexto"], 1),
        "menor_score_contexto": candidata["pior_trecho"]["score"],
    }


def _formatar_alternativa(nome, candidata):
    """Prepara os dados e a justificativa de cada alternativa."""

    justificativas = {
        "Mais curta": (
            "Menor distância entre os caminhos calculados."
        ),
        "Melhor iluminação": (
            "Maior score de iluminação entre as alternativas "
            "avaliadas, utilizando os dados disponíveis."
        ),
        "Melhor contexto": (
            "Maior score de contexto entre as alternativas "
            "avaliadas, utilizando os dados disponíveis."
        ),
    }

    return {
        "nome": nome,
        "nos": candidata["nos"],
        "distancia_metros": round(candidata["distancia_metros"]),
        "tempo_minutos": round(candidata["tempo_minutos"], 1),
        "score_iluminacao": round(candidata["score_iluminacao"], 1),
        "score_contexto": round(candidata["score_contexto"], 1),
        "justificativa": justificativas[nome],
        "pior_trecho": candidata["pior_trecho"],
        "fatores": _analisar_fatores_rota(candidata),
        "avaliacao": candidata["avaliacao"],
    }

def obter_edge_ids(grafo, nos_da_rota):
    return [
        grafo[origem][destino]["edge_id"]
        for origem, destino in zip(
            nos_da_rota,
            nos_da_rota[1:]
        )
    ]

def rotas_suficientemente_diferentes(candidata, selecionadas):
    """Verifica se pelo menos 30% da rota é diferente das já escolhidas."""

    trechos_candidata = set(candidata["edge_ids"])

    for selecionada in selecionadas:
        trechos_selecionada = set(selecionada["edge_ids"])

        sobreposicao = len(
            trechos_candidata & trechos_selecionada
        )

        proporcao_diferente = (
            1 - sobreposicao / len(trechos_candidata)
        )

        if proporcao_diferente < FRACAO_MINIMA_DIFERENTE:
            return False

    return True

def calcular_alternativas(
    latitude_origem,
    longitude_origem,
    latitude_destino,
    longitude_destino,
):
    """Calcula até três rotas diferentes dentro do limite permitido."""
    _validar_coordenada(latitude_origem, longitude_origem)
    _validar_coordenada(latitude_destino, longitude_destino)

    grafo = carregar_grafo()
    aplicar_scores_ao_grafo(grafo)

    grafo_simples = criar_grafo_simples_para_alternativas(
        grafo
    )

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

    candidatas = []
    alertas_ativos = listar_alertas_ativos_supabase()

    try:
        gerador_de_caminhos = nx.shortest_simple_paths(
            grafo_simples,
            no_origem,
            no_destino,
            weight="length",
        )

        for nos_da_rota in gerador_de_caminhos:
            distancia_metros = _distancia_da_rota(
                grafo_simples,
                nos_da_rota,
            )

            if candidatas:
                distancia_mais_curta = candidatas[0][
                    "distancia_metros"
                ]

                if (
                    distancia_metros
                    > distancia_mais_curta
                    * FATOR_MAXIMO_ALTERNATIVA
                ):
                    break

            candidata = {
                "nos": nos_da_rota,
                "distancia_metros": distancia_metros,
                "tempo_minutos": (
                    distancia_metros
                    / VELOCIDADE_MEDIA_METROS_POR_MINUTO
                ),
                "score_iluminacao": _score_medio_da_rota(
                    grafo_simples,
                    nos_da_rota,
                    "score_iluminacao",
                ),
                "score_contexto": _score_medio_da_rota(
                    grafo_simples,
                    nos_da_rota,
                    "score_base",
                ),
            }
            candidata["pior_trecho"] = _identificar_pior_trecho(
                grafo_simples,
                nos_da_rota,
            )

            edge_ids = obter_edge_ids(grafo_simples, nos_da_rota)
            candidata["edge_ids"] = edge_ids

            avaliacao = avaliar_rota(edge_ids, alertas_ativos)

            candidata["score_contexto"] = avaliacao["score_medio"]
            candidata["avaliacao"] = avaliacao

            candidatas.append(candidata)

            if (
                len(candidatas)
                >= LIMITE_CANDIDATOS_ALTERNATIVAS
            ):
                break

    except nx.NetworkXNoPath as erro:
        raise ValueError(
            "Não foi possível calcular uma rota entre os pontos."
        ) from erro

    if not candidatas:
        raise ValueError(
            "Não foi possível calcular uma rota entre os pontos."
        )

    alternativas = [
        _formatar_alternativa("Mais curta", candidatas[0])
    ]

    caminhos_usados = {tuple(candidatas[0]["nos"])}

    rotas_selecionadas = [candidatas[0]]

    criterios = [
        ("Melhor iluminação", "score_iluminacao"),
        ("Melhor contexto", "score_contexto"),
    ]

    for nome, campo_score in criterios:
        elegiveis = [
            candidata
            for candidata in candidatas
            if (
                tuple(candidata["nos"]) not in caminhos_usados
                and rotas_suficientemente_diferentes(
                candidata, rotas_selecionadas
    )
)
        ]

        if not elegiveis:
            continue

        melhor_candidata = max(
            elegiveis,
            key=lambda candidata: (
                candidata[campo_score],
                -candidata["distancia_metros"],
            ),
        )

        alternativas.append(
            _formatar_alternativa(nome, melhor_candidata)
        )
        caminhos_usados.add(tuple(melhor_candidata["nos"]))
        rotas_selecionadas.append(melhor_candidata)

    return alternativas


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
def coordenadas_do_pior_trecho(pior_trecho):
    """Obtém as coordenadas dos dois nós do pior trecho."""

    if pior_trecho is None:
        return []

    grafo = carregar_grafo()

    origem = pior_trecho["origem_no"]
    destino = pior_trecho["destino_no"]

    return [
        [
            grafo.nodes[origem]["y"],
            grafo.nodes[origem]["x"],
        ],
        [
            grafo.nodes[destino]["y"],
            grafo.nodes[destino]["x"],
        ],
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
        latitude, longitude = ox.geocode(
            f"{endereco}, São Paulo, SP, Brasil"
        )
    except Exception as erro:
        raise ValueError(
            "Não foi possível localizar esse endereço. "
            "Confira a rua, o número e o bairro."
        ) from erro

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

    return 2 * raio_terra * math.atan2(
        math.sqrt(valor),
        math.sqrt(1 - valor),
    )


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