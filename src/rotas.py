"""Cálculo de rotas a pé na Vila Mariana."""
import json
import math
import os
import time
from functools import lru_cache
from itertools import chain
from pathlib import Path
from threading import Lock

import networkx as nx
import osmnx as ox
import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.prepared import prep

from src import config
from src.abrigos import listar_abrigos
from src.grafo import carregar_grafo
from src.score import avaliar_rota
from src.supabase_db import listar_alertas_ativos_supabase


VELOCIDADE_MEDIA_METROS_POR_MINUTO = 80
FATOR_MAXIMO_ALTERNATIVA = 1.4
FRACAO_MINIMA_DIFERENTE = 0.50
RAIO_CORREDOR_METROS = 50
# Pesos de desvio: custo adicional nas ruas próximas às rotas selecionadas.
PENALIDADES_CORREDOR = (1.0, 3.0, 8.0)


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
    # O grafo original usa longitude/latitude; UTM 23S permite medir em metros.
    transformador = Transformer.from_crs(
        grafo.graph.get("crs", "EPSG:4326"), "EPSG:32723", always_xy=True
    )
    ids = list(grafo.nodes)
    xs, ys = transformador.transform(
        [float(grafo.nodes[no]["x"]) for no in ids],
        [float(grafo.nodes[no]["y"]) for no in ids],
    )
    posicoes = dict(zip(ids, zip(xs, ys)))
    grafo_simples.add_nodes_from(
        (no, {"posicao_m": posicoes[no]}) for no in ids
    )

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
                meio_m=Point(
                    (posicoes[no_origem][0] + posicoes[no_destino][0]) / 2,
                    (posicoes[no_origem][1] + posicoes[no_destino][1]) / 2,
                ),
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
            "Maior score de iluminação entre as opções exibidas, "
            "utilizando os dados disponíveis."
        ),
        "Melhor contexto": (
            "Maior score de contexto entre as opções exibidas, "
            "utilizando os dados disponíveis."
        ),
    }

    justificativa = (
        candidata["justificativa_alternativa"]
        if nome == "Alternativa" else justificativas[nome]
    )
    return {
        "nome": nome,
        "nos": candidata["nos"],
        "edge_ids": candidata["edge_ids"],
        "distancia_metros": round(candidata["distancia_metros"]),
        "tempo_minutos": round(candidata["tempo_minutos"], 1),
        "score_iluminacao": round(candidata["score_iluminacao"], 1),
        "score_contexto": round(candidata["score_contexto"], 1),
        "justificativa": justificativa,
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

def _menor_fracao_distinta(candidata, selecionadas):
    """Mede quanto cada caminho sai do corredor dos outros, nos dois sentidos."""
    if not selecionadas:
        return 1.0

    linha = candidata["linha_m"]
    if linha.length <= 0:
        return 0.0

    fracoes = []
    for selecionada in selecionadas:
        outra_linha = selecionada["linha_m"]
        if outra_linha.length <= 0:
            return 0.0

        # O menor valor evita aceitar uma rota curta quase contida em outra.
        fora_da_outra = linha.difference(selecionada["corredor_m"]).length
        fora_da_candidata = outra_linha.difference(candidata["corredor_m"]).length
        fracoes.append(min(
            fora_da_outra / linha.length,
            fora_da_candidata / outra_linha.length,
        ))

    return min(fracoes)


def rotas_suficientemente_diferentes(candidata, selecionadas):
    """Exige 50% fora do corredor de cada outra rota, em ambos os sentidos."""
    return _menor_fracao_distinta(candidata, selecionadas) >= FRACAO_MINIMA_DIFERENTE


def _linha_da_rota(grafo, nos):
    return LineString([grafo.nodes[no]["posicao_m"] for no in nos])


def _gerar_candidatos_diversos(grafo, origem, destino, selecionadas):
    """Busca caminhos por custos diferentes sem modificar o grafo em cache."""
    corredores = [prep(rota["corredor_m"]) for rota in selecionadas]
    trechos_usados = {
        frozenset((u, v))
        for rota in selecionadas
        for u, v in zip(rota["nos"], rota["nos"][1:])
    }
    cache_proximidade = {}

    def custo(u, v, dados, penalidade, campo_score):
        chave = (u, v)
        if chave not in cache_proximidade:
            cache_proximidade[chave] = (
                frozenset((u, v)) in trechos_usados
                or any(cobre.covers(dados["meio_m"]) for cobre in corredores)
            )

        fator = 1.0 + penalidade * int(cache_proximidade[chave])
        if campo_score is not None:
            score = float(dados.get(campo_score, 0))
            if not math.isfinite(score):
                score = 0
            score = max(0, min(100, score))
            fator += (100 - score) / 100

        return float(dados["length"]) * fator

    # Primeiro explora os critérios sem penalização; depois, estimula desvios.
    buscas = [(0, "score_iluminacao"), (0, "score_base")]
    buscas.extend(
        (penalidade, campo)
        for penalidade in PENALIDADES_CORREDOR
        for campo in (None, "score_iluminacao", "score_base")
    )

    for penalidade, campo in buscas:
        try:
            yield nx.shortest_path(
                grafo, origem, destino,
                weight=lambda u, v, dados: custo(u, v, dados, penalidade, campo),
                method="dijkstra",
            )
        except nx.NetworkXNoPath:
            continue


def _gerar_candidatos_por_desvio(grafo, origem, destino, selecionadas, limite_distancia):
    """Explora pontos intermediários afastados dentro do limite de distância."""
    dist_o, caminhos_o = nx.single_source_dijkstra(
        grafo, origem, cutoff=limite_distancia, weight="length"
    )
    dist_d, caminhos_d = nx.single_source_dijkstra(
        grafo.reverse(copy=False), destino, cutoff=limite_distancia, weight="length"
    )
    possibilidades = []
    for no, distancia in dist_o.items():
        if no in (origem, destino) or no not in dist_d:
            continue
        total = distancia + dist_d[no]
        if total > limite_distancia:
            continue
        ponto = Point(grafo.nodes[no]["posicao_m"])
        afastamento = min(ponto.distance(rota["linha_m"]) for rota in selecionadas)
        if afastamento <= RAIO_CORREDOR_METROS:
            continue
        possibilidades.append((afastamento, total, no, ponto))

    possibilidades.sort(key=lambda item: (-item[0], item[1]))
    pontos_testados = []
    for _, _, no, ponto in possibilidades:
        if any(ponto.distance(outro) < 60 for outro in pontos_testados):
            continue
        caminho = caminhos_o[no] + list(reversed(caminhos_d[no]))[1:]
        if len(caminho) != len(set(caminho)):
            continue
        pontos_testados.append(ponto)
        yield caminho
        if len(pontos_testados) >= 24:
            break


def _avaliar_candidata(grafo, nos, distancia, linha, alertas_ativos):
    edge_ids = obter_edge_ids(grafo, nos)
    avaliacao = avaliar_rota(edge_ids, alertas_ativos)
    return {
        "nos": nos,
        "edge_ids": edge_ids,
        "distancia_metros": distancia,
        "tempo_minutos": distancia / VELOCIDADE_MEDIA_METROS_POR_MINUTO,
        "score_iluminacao": _score_medio_da_rota(
            grafo, nos, "score_iluminacao"
        ),
        "score_contexto": avaliacao["score_medio"],
        "pior_trecho": _identificar_pior_trecho(grafo, nos),
        "avaliacao": avaliacao,
        "linha_m": linha,
        "corredor_m": linha.buffer(RAIO_CORREDOR_METROS),
    }


@lru_cache(maxsize=2)
def _grafos_para_alternativas(arquivo_grafo, versao_grafo, arquivo_score, versao_score):
    """Reutiliza grafos preparados, que são somente lidos na busca."""
    grafo = ox.load_graphml(arquivo_grafo)
    aplicar_scores_ao_grafo(grafo)
    return grafo, criar_grafo_simples_para_alternativas(grafo)


def calcular_alternativas(
    latitude_origem,
    longitude_origem,
    latitude_destino,
    longitude_destino,
    *,
    alertas_ativos=None,
):
    """Calcula de uma a três rotas distintas, respeitando o limite de distância."""
    _validar_coordenada(latitude_origem, longitude_origem)
    _validar_coordenada(latitude_destino, longitude_destino)

    arquivo_grafo = Path(config.CAMINHO_GRAFO).resolve()
    arquivo_score = config.ARQUIVO_SCORE
    grafo, grafo_simples = _grafos_para_alternativas(
        arquivo_grafo, arquivo_grafo.stat().st_mtime_ns,
        arquivo_score, arquivo_score.stat().st_mtime_ns,
    )
    no_origem, no_destino = ox.distance.nearest_nodes(
        grafo,
        X=[longitude_origem, longitude_destino],
        Y=[latitude_origem, latitude_destino],
    )

    if no_origem == no_destino:
        raise ValueError("Origem e destino estão no mesmo ponto da rede. Escolha outro endereço.")

    if alertas_ativos is None:
        alertas_ativos = listar_alertas_ativos_supabase()

    try:
        nos_curta = nx.shortest_path(
            grafo_simples, no_origem, no_destino, weight="length"
        )
    except nx.NetworkXNoPath as erro:
        raise ValueError(
            "Não foi possível calcular uma rota entre os pontos."
        ) from erro

    distancia_curta = _distancia_da_rota(grafo_simples, nos_curta)
    if distancia_curta <= 0:
        raise ValueError("Não foi possível medir a distância da rota.")

    limite_distancia = distancia_curta * FATOR_MAXIMO_ALTERNATIVA
    curta = _avaliar_candidata(
        grafo_simples, nos_curta, distancia_curta,
        _linha_da_rota(grafo_simples, nos_curta), alertas_ativos,
    )

    selecionadas = [curta]
    candidatas = []
    caminhos_vistos = {tuple(nos_curta)}

    def adicionar_caminhos(referencias):
        for nos in chain(
            _gerar_candidatos_diversos(grafo_simples, no_origem, no_destino, referencias),
            _gerar_candidatos_por_desvio(grafo_simples, no_origem, no_destino, referencias, limite_distancia),
        ):
            chave = tuple(nos)
            if chave in caminhos_vistos:
                continue
            caminhos_vistos.add(chave)

            distancia = _distancia_da_rota(grafo_simples, nos)
            if distancia <= 0 or distancia > limite_distancia:
                continue

            linha = _linha_da_rota(grafo_simples, nos)
            if not rotas_suficientemente_diferentes(
                {"linha_m": linha, "corredor_m": linha.buffer(RAIO_CORREDOR_METROS)},
                [curta],
            ):
                continue

            candidatas.append(_avaliar_candidata(
                grafo_simples, nos, distancia, linha, alertas_ativos
            ))

    # Contexto é a prioridade do PorOnde?. Iluminação vem em seguida.
    # Se não houver uma alternativa realmente distinta, retorna apenas a curta.
    for campo_score in ("score_contexto", "score_iluminacao"):
        adicionar_caminhos(selecionadas)
        elegiveis = [
            candidata for candidata in candidatas
            if all(candidata is not rota for rota in selecionadas)
            and rotas_suficientemente_diferentes(candidata, selecionadas)
        ]
        if not elegiveis:
            break

        melhor = max(
            elegiveis,
            key=lambda candidata: (
                candidata[campo_score],
                _menor_fracao_distinta(candidata, selecionadas),
                -candidata["distancia_metros"],
            ),
        )
        selecionadas.append(melhor)

    # Os nomes não devem prometer pontuação superior se isso não for verdade.
    # Compara os valores arredondados, iguais aos apresentados na interface.
    alternativas = [_formatar_alternativa("Mais curta", curta)]
    nomes_usados = set()
    for candidata in selecionadas[1:]:
        demais = [rota for rota in selecionadas if rota is not candidata]
        nome = "Alternativa"
        for rotulo, campo in (
            ("Melhor contexto", "score_contexto"),
            ("Melhor iluminação", "score_iluminacao"),
        ):
            if rotulo not in nomes_usados and all(
                round(candidata[campo], 1) > round(rota[campo], 1)
                for rota in demais
            ):
                nome = rotulo
                nomes_usados.add(rotulo)
                break

        if nome == "Alternativa":
            candidata = {
                **candidata,
                "justificativa_alternativa": (
                    "Caminho diferente das demais opções, dentro do limite "
                    "de distância. Compare os indicadores de contexto e iluminação."
                ),
            }
        alternativas.append(_formatar_alternativa(nome, candidata))

    # Mantém a ordem original de apresentação quando os rótulos se aplicam.
    ordem = {
        "Mais curta": 0, "Melhor iluminação": 1,
        "Melhor contexto": 2, "Alternativa": 3,
    }
    return sorted(alternativas, key=lambda rota: ordem[rota["nome"]])


def rota_para_geodataframe(nos_da_rota):
    """Converte os trechos de uma rota para um GeoDataFrame."""
    grafo = carregar_grafo()

    return ox.routing.route_to_gdf(
        grafo,
        nos_da_rota,
        weight="length",
    )



@lru_cache(maxsize=2)
def _posicoes_dos_nos(arquivo, versao):
    grafo = carregar_grafo()
    return {no: (dados["x"], dados["y"]) for no, dados in grafo.nodes(data=True)}


def coordenadas_da_rota(nos_da_rota):
    """Devolve os pontos da rota no formato longitude e latitude."""
    arquivo = Path(config.CAMINHO_GRAFO).resolve()
    posicoes = _posicoes_dos_nos(arquivo, arquivo.stat().st_mtime_ns)
    return [list(posicoes[no]) for no in nos_da_rota]


def coordenadas_do_pior_trecho(pior_trecho):
    """Obtém as coordenadas dos dois nós do pior trecho em latitude/longitude."""
    if pior_trecho is None:
        return []

    coordenadas = coordenadas_da_rota(
        [pior_trecho["origem_no"], pior_trecho["destino_no"]]
    )
    return [[latitude, longitude] for longitude, latitude in coordenadas]


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


_geocodificacao_lock = Lock()
_ultima_geocodificacao = 0.0

@lru_cache(maxsize=512)
def _geocodificar_memoria(chave):
    global _ultima_geocodificacao
    cache = _ler_cache_geocodificacao()
    if chave in cache:
        latitude = float(cache[chave]["latitude"])
        longitude = float(cache[chave]["longitude"])
        _validar_coordenada(latitude, longitude)
        return latitude, longitude
    try:
        # A consulta externa só ocorre no envio do formulário, nunca ao digitar.
        # Respeita o intervalo do provedor em um processo, sem gravar novos endereços em disco.
        intervalo = 1.1 - (time.monotonic() - _ultima_geocodificacao)
        if intervalo > 0:
            time.sleep(intervalo)
        ox.settings.requests_timeout = 10
        ox.settings.http_user_agent = os.getenv("PORONDE_GEOCODE_USER_AGENT", "PorOnde-MVP/1.0 (academic pilot)")
        # O próprio OSMnx pode persistir as respostas: desativa durante esta consulta.
        cache_original = ox.settings.use_cache
        ox.settings.use_cache = False
        try:
            _ultima_geocodificacao = time.monotonic()
            latitude, longitude = ox.geocode(f"{chave}, São Paulo, SP, Brasil")
        finally:
            ox.settings.use_cache = cache_original
    except Exception as erro:
        raise ValueError("Não foi possível localizar esse endereço. Confira a rua, o número e o bairro.") from erro
    _validar_coordenada(latitude, longitude)
    return latitude, longitude


def localizar_endereco(endereco):
    chave = _normalizar_endereco(endereco)
    if not chave:
        raise ValueError("Informe um endereço.")
    with _geocodificacao_lock:
        return _geocodificar_memoria(chave)


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