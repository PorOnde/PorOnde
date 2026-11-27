import logging
import os
import time
from collections import defaultdict, deque
from threading import BoundedSemaphore, Lock
from src.ambiente_comunidade import AMBIENTE, SIMULADO
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="PorOnde? API", version="1.0.0")





# Proteção básica por processo, não equivale a autenticação nem rate limit distribuído.
_limite_lock = Lock()
_requisicoes = defaultdict(deque)

@app.middleware("http")
async def proteger_e_medir(request: Request, call_next):
    inicio = time.monotonic()
    caminho = request.url.path
    if caminho.startswith("/api/") and request.method in {"GET", "POST"}:
        grupo = ("escrita" if request.method == "POST" else
                 "calculo" if caminho == "/api/rotas" else "consulta")
        limite = {"escrita": 24, "calculo": 15, "consulta": 180}[grupo]
        chave = (request.client.host if request.client else "desconhecido", grupo)
        with _limite_lock:
            # Limpa chaves ociosas e limita a memória ocupada.
            for k in list(_requisicoes):
                if not _requisicoes[k] or inicio - _requisicoes[k][-1] >= 60:
                    del _requisicoes[k]
            if chave not in _requisicoes and len(_requisicoes) >= 4096:
                return JSONResponse(status_code=429, content={"detail": "Servidor ocupado. Tente novamente em instantes."})
            fila = _requisicoes[chave]
            while fila and inicio - fila[0] >= 60:
                fila.popleft()
            if len(fila) >= limite:
                return JSONResponse(status_code=429, content={"detail": "Muitas solicitações. Aguarde um minuto."}, headers={"Retry-After": "60"})
            fila.append(inicio)
    try:
        resposta = await call_next(request)
    except Exception as erro:
        logger.error("Falha na API: %s", type(erro).__name__)
        resposta = JSONResponse(status_code=500, content={"detail": "Não foi possível concluir a consulta."})
    if caminho == "/api/rotas":
        logger.info("Busca de rotas: %.2fs", time.monotonic() - inicio)
    resposta.headers["Cache-Control"] = "no-store"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    return resposta

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"] + [
        origem.strip().rstrip("/") for origem in os.getenv("PORONDE_ORIGENS", "").split(",")
        if origem.strip() and origem.strip() != "*"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.get("/api/ambiente")
def consultar_ambiente():
    return {"ambiente": AMBIENTE, "simulado": SIMULADO}

# Evita repetir quatro RPCs em cada carregamento consecutivo. A consulta das
# linhas é sempre nova, com filtro de validade; não serve registros vencidos do cache.
_atualizacao_lock = Lock()
_ultima_atualizacao = None

@lru_cache(maxsize=1)
def _confirmar_isolamento_sql():
    from src.supabase_db import conectar_supabase
    r = conectar_supabase().rpc("poronde_isolamento_v1").execute()
    if r.data is not True:
        raise RuntimeError("Instale sql/atualizar_comunidade.sql antes de usar a comunidade.")
    return True

def _atualizar_comunidade(force=False):
    global _ultima_atualizacao
    from src.supabase_db import atualizar_alertas_supabase
    _confirmar_isolamento_sql()
    with _atualizacao_lock:
        if force or _ultima_atualizacao is None or time.monotonic() - _ultima_atualizacao >= 8:
            atualizar_alertas_supabase()
            _ultima_atualizacao = time.monotonic()

def _invalidar_atualizacao():
    global _ultima_atualizacao
    with _atualizacao_lock:
        _ultima_atualizacao = None


@app.get("/")
def inicio():
    return {"projeto": "PorOnde?", "status": "API funcionando"}


@app.get("/api/saude")
def verificar_servidor():
    return {"status": "online"}


@lru_cache(maxsize=2)
def _ler_categorias_ocorrencias(arquivo, versao):
    import pandas as pd

    tabela = pd.read_csv(arquivo, usecols=["trecho_id", "categoria", "total"],
                         dtype={"trecho_id": str, "categoria": str})
    totais = pd.to_numeric(tabela["total"], errors="raise")
    if (tabela[["trecho_id", "categoria"]].isna().any().any()
            or totais.isna().any() or (totais < 0).any()
            or (totais % 1 != 0).any()):
        raise ValueError("Arquivo de categorias com registros inválidos.")
    return tabela.assign(total=totais.astype(int))


def _ocorrencias_da_rota(rota):
    from src import config

    avaliacao = rota["avaliacao"]
    dados_reais = (not avaliacao["dados_piloto"]
                   and Path(config.ARQUIVO_SCORE).name == "trechos_score.csv")
    arquivo = Path(config.PASTA_TRATADOS) / "ocorrencias_por_categoria.csv"
    resposta = {
        "categorias_disponiveis": False,
        "total_categorias": None,
        "categorias": [],
        "registros_associados_ao_score": int(avaliacao["n_ocorrencias"]),
        "dados_piloto": not dados_reais,
        "fonte": "SSP-SP" if dados_reais else None,
        "periodo": "02/07 a 30/09/2026" if dados_reais else None,
    }
    if not dados_reais or not arquivo.is_file():
        return resposta

    # Mesma normalização de sentidos utilizada no Streamlit original.
    trechos = set()
    for edge_id in rota["edge_ids"]:
        origem, destino, chave = edge_id.split("_")
        primeiro, segundo = sorted((origem, destino))
        trechos.add(f"{primeiro}_{segundo}_{chave}")

    try:
        tabela = _ler_categorias_ocorrencias(arquivo, arquivo.stat().st_mtime_ns)
        categorias = (tabela.loc[tabela["trecho_id"].isin(trechos)]
                      .groupby("categoria")["total"].sum()
                      .sort_values(ascending=False))
    except (OSError, ValueError):
        # O score permanece disponível mesmo se o detalhamento falhar.
        return resposta

    resposta.update(
        categorias_disponiveis=True,
        total_categorias=int(categorias.sum()),
        categorias=[{"categoria": str(nome), "total": int(total)}
                    for nome, total in categorias.items()],
    )
    return resposta


def _apoio_da_rota(rota, cadastro):
    import math
    import pandas as pd
    from src.rotas import locais_apoio_proximos

    if cadastro is None or cadastro.empty:
        return None

    # Reutiliza a seleção original de até cinco locais, com diversidade de grupos.
    locais = locais_apoio_proximos(rota["nos"], raio_metros=200)
    metadados = {
        (str(linha.nome), float(linha.lat), float(linha.lon)): linha
        for linha in cadastro.itertuples(index=False)
        if pd.notna(linha.lat) and pd.notna(linha.lon)
    }
    resultado = []
    for local in locais:
        lat, lon = float(local["lat"]), float(local["lon"])
        if not (math.isfinite(lat) and math.isfinite(lon)
                and -90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        dados = metadados.get((str(local["nome"]), lat, lon))
        fonte = getattr(dados, "fonte", None)
        horario = getattr(dados, "horario", None)
        resultado.append({
            "nome": str(local["nome"]),
            "tipo": str(local["tipo"]),
            "grupo": str(local["grupo"]),
            "lat": lat,
            "lon": lon,
            "distancia_metros": int(local["distancia_metros"]),
            "fonte": str(fonte) if pd.notna(fonte) else None,
            "horario": str(horario) if pd.notna(horario) else None,
        })
    return resultado


# Consulta única por busca, compartilhada por todas as alternativas.
# O mapa geral mantém seu limite de 100; o cálculo não descarta alertas
# antigos ainda válidos apenas por causa desse limite de apresentação.
COLUNAS_COMUNIDADE = (
    "id,categoria,descricao,lat,lon,rua,status,criado_em,expira_em,"
    "confirmacoes,rejeicoes,afeta_score,simulado"
)


def _consultar_relatos_validos(limite_mapa=False):
    from datetime import datetime, timezone
    from src.supabase_db import conectar_supabase

    _atualizar_comunidade()
    cliente = conectar_supabase()
    instante = datetime.now(timezone.utc).isoformat()
    tamanho = 100 if limite_mapa else 200
    relatos = []
    while True:
        consulta = (cliente.table("relatos").select(COLUNAS_COMUNIDADE)
                    .in_("status", ["pendente", "ativo"])
                    .eq("simulado", SIMULADO).gt("expira_em", instante))
        if limite_mapa:
            consulta = consulta.order("criado_em", desc=True).order("id", desc=True).limit(tamanho)
        else:
            # Paginação por ID: evita saltar registros ao mudar de página.
            if relatos:
                consulta = consulta.gt("id", relatos[-1]["id"])
            consulta = consulta.order("id").limit(tamanho)
        lote = consulta.execute().data or []
        relatos.extend(lote)
        if limite_mapa or len(lote) < tamanho:
            return relatos
        # Proteção contra consultas ilimitadas. Não calcula um score parcial
        # silenciosamente se o volume superar a capacidade prevista do MVP.
        if len(relatos) >= 2000:
            raise RuntimeError("Limite de consulta comunitária atingido.")


def _consultar_recorrencias():
    """Consulta as recorrências já calculadas pelo banco, sem alterar o Score."""
    from src.supabase_db import conectar_supabase, listar_recorrencias_ativas_supabase

    registros = listar_recorrencias_ativas_supabase() or []
    if not registros:
        return []
    ids = sorted({r[c] for r in registros for c in ("id_relato_1", "id_relato_2")})
    # Defesa adicional: não publicar pares mistos ou rejeitados.
    fontes = {}
    cliente = conectar_supabase()
    for i in range(0, len(ids), 100):
        lote = (cliente.table("relatos").select("id,status,simulado")
                .in_("id", ids[i:i + 100]).execute().data or [])
        fontes.update({r["id"]: r for r in lote})
    resultado = []
    for r in registros:
        a, b = r["id_relato_1"], r["id_relato_2"]
        if not all(i in fontes and fontes[i]["simulado"] is SIMULADO
                   and fontes[i]["status"] != "rejeitado" for i in (a, b)):
            continue
        resultado.append({"id": f"{a}-{b}", "rua": r["rua"],
                          "lat": r["lat"], "lon": r["lon"],
                          "expira_em": r["expira_em"], "simulado": SIMULADO})
    return resultado


def _recorrencias_ou_indisponivel():
    try:
        return _consultar_recorrencias()
    except Exception as erro:
        logger.warning("Falha na consulta de recorrências: %s", type(erro).__name__)
        return None


def _relatos_para_score(relatos):
    import pandas as pd
    return pd.DataFrame([
        r for r in relatos
        if r["status"] == "ativo" and r.get("afeta_score") is True
    ])


def _relatos_proximos(edge_ids, relatos):
    """Mesmo raio e mesma geometria projetada usados por src.score."""
    import geopandas as gpd
    import pandas as pd
    from src.config import RAIO_ALERTA_ROTA_M
    from src.score import TRATADOS, _linhas_projetadas

    if not relatos:
        return []
    tabela = pd.DataFrame(relatos)
    lat = pd.to_numeric(tabela["lat"], errors="raise")
    lon = pd.to_numeric(tabela["lon"], errors="raise")
    if not (lat.between(-90, 90) & lon.between(-180, 180)).all():
        raise ValueError("Relato com coordenadas inválidas.")
    arquivo = TRATADOS / "grafo_vila_mariana.graphml"
    linhas = _linhas_projetadas(arquivo, arquivo.stat().st_mtime_ns)
    linha_rota = linhas.loc[edge_ids].union_all()
    pontos = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs="EPSG:4326").to_crs(linhas.crs)
    distancias = pontos.distance(linha_rota)
    proximos = [dict(relato, distancia_metros=round(float(distancia)))
                for relato, distancia in zip(relatos, distancias)
                if distancia <= RAIO_ALERTA_ROTA_M]
    return sorted(proximos, key=lambda r: (r["distancia_metros"], r["id"]))


_limite_calculos = BoundedSemaphore(2)

@app.get("/api/rotas")
def buscar_rotas(origem_lat: float, origem_lon: float,
                 destino_lat: float, destino_lon: float):
    if not _limite_calculos.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="Há outras rotas em cálculo. Tente novamente em instantes.")
    try:
        return _buscar_rotas(origem_lat, origem_lon, destino_lat, destino_lon)
    finally:
        _limite_calculos.release()


def _buscar_rotas(origem_lat, origem_lon, destino_lat, destino_lon):
    import pandas as pd
    from src.abrigos import listar_abrigos
    from src.rotas import calcular_alternativas, coordenadas_da_rota, _validar_coordenada

    try:
        _validar_coordenada(origem_lat, origem_lon)
        _validar_coordenada(destino_lat, destino_lon)
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro

    # Em caso de indisponibilidade, ainda permite comparar o contexto histórico,
    # mas sinaliza explicitamente que a comunidade não participou do cálculo.
    try:
        relatos = _consultar_relatos_validos()
        alertas = _relatos_para_score(relatos)
        comunidade_disponivel = True
    except Exception as erro:
        logger.warning("Comunidade indisponível no cálculo: %s", type(erro).__name__)
        relatos = []
        alertas = pd.DataFrame()
        comunidade_disponivel = False

    recorrencias = _recorrencias_ou_indisponivel() if comunidade_disponivel else None

    inicio_calculo = time.monotonic()
    try:
        alternativas = calcular_alternativas(
            origem_lat, origem_lon, destino_lat, destino_lon,
            alertas_ativos=alertas,
        )
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro

    logger.info("Algoritmo de rotas: %.2fs", time.monotonic() - inicio_calculo)
    try:
        cadastro = listar_abrigos()
    except (OSError, ValueError):
        cadastro = None

    resultados = []
    for rota in alternativas:
        coordenadas = coordenadas_da_rota(rota["nos"])
        avaliacao = rota["avaliacao"]
        try:
            locais = _apoio_da_rota(rota, cadastro)
        except (OSError, ValueError, TypeError, KeyError):
            locais = None

        proximos = None
        if comunidade_disponivel:
            try:
                proximos = _relatos_proximos(rota["edge_ids"], relatos)
            except Exception as erro:
                logger.warning("Falha no detalhamento comunitário: %s", type(erro).__name__)
        recorrencias_proximas = None
        if recorrencias is not None:
            try:
                recorrencias_proximas = _relatos_proximos(rota["edge_ids"], recorrencias)
            except Exception as erro:
                logger.warning("Falha no recorte de recorrências: %s", type(erro).__name__)
        resultados.append({
            "nome": rota["nome"],
            "distancia_metros": rota["distancia_metros"],
            "tempo_minutos": rota["tempo_minutos"],
            "score_iluminacao": rota["score_iluminacao"],
            "score_contexto": rota["score_contexto"],
            "justificativa": rota["justificativa"],
            "coordenadas": [[float(lat), float(lon)] for lon, lat in coordenadas],
            "avaliacao": avaliacao,
            "ocorrencias": _ocorrencias_da_rota(rota),
            "locais_apoio": locais,
            "relatos_proximos": proximos,
            "recorrencias_proximas": recorrencias_proximas,
        })

    return {
        "quantidade": len(resultados),
        "alertas_disponiveis": comunidade_disponivel,
        "ambiente": AMBIENTE,
        "rotas": resultados,
    }


@app.get("/api/geocodificar")
def geocodificar_endereco(endereco: str = Query(min_length=1, max_length=250)):
    from src.rotas import localizar_endereco

    endereco = endereco.strip()
    if not endereco:
        raise HTTPException(status_code=400, detail="Informe um endereço.")
    try:
        latitude, longitude = localizar_endereco(endereco)
        return {"endereco": endereco, "latitude": float(latitude),
                "longitude": float(longitude)}
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro


# Comunidade: primeira etapa da integração com o Supabase.
@app.get("/api/comunidade/saude")
def verificar_supabase():
    from src.supabase_db import conectar_supabase

    try:
        _confirmar_isolamento_sql()
        conectar_supabase().table("relatos").select("id").limit(1).execute()
    except Exception as erro:
        # Não devolve chaves, URL privada ou detalhes internos ao navegador.
        logger.warning("Falha na consulta de saúde do Supabase: %s", type(erro).__name__)
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.") from None
    return {"status": "online", "banco": "supabase"}


class RelatoEntrada(BaseModel):
    categoria: str = Field(min_length=1, max_length=100)
    descricao: str = Field(min_length=1, max_length=200)
    lat: float
    lon: float
    id_sessao: str = Field(min_length=1, max_length=128)
    rua: str | None = Field(default=None, max_length=200)
    data_ocorrencia: str | None = Field(default=None, max_length=10)
    horario_ocorrencia: str | None = Field(default=None, max_length=15)


@app.post("/api/relatos", status_code=201)
def cadastrar_relato(relato: RelatoEntrada):
    from src.supabase_db import registrar_relato_supabase

    sessao = relato.id_sessao.strip()
    if not sessao:
        raise HTTPException(status_code=400, detail="Sessão inválida.")
    if relato.categoria == "Roubo ou furto relatado" and not (relato.rua or "").strip():
        raise HTTPException(status_code=400, detail="Informe o nome da rua da ocorrência.")

    try:
        _confirmar_isolamento_sql()
        resultado = registrar_relato_supabase(
            categoria=relato.categoria,
            descricao=relato.descricao,
            lat=relato.lat,
            lon=relato.lon,
            id_sessao=sessao,
            rua=relato.rua,
            data_ocorrencia=relato.data_ocorrencia,
            horario_ocorrencia=relato.horario_ocorrencia,
            simulado=SIMULADO,
        )
    except Exception as erro:
        logger.warning("Falha ao registrar relato: %s", type(erro).__name__)
        raise HTTPException(status_code=503, detail="Não foi possível concluir o envio do relato.") from None

    # A função original retorna uma mensagem de validação ou o ID numérico.
    if isinstance(resultado, str):
        raise HTTPException(status_code=400, detail=resultado)
    if type(resultado) is not int:
        raise HTTPException(status_code=500, detail="Resposta inesperada no registro do relato.")

    _invalidar_atualizacao()
    return {"id": resultado, "status": "pendente", "afeta_score": False, "simulado": SIMULADO}


@app.get("/api/comunidade/relatos")
def consultar_comunidade():
    try:
        relatos = _consultar_relatos_validos(limite_mapa=True)
    except Exception as erro:
        logger.warning("Falha na consulta comunitária: %s", type(erro).__name__)
        raise HTTPException(status_code=503, detail="Não foi possível consultar os relatos e alertas.") from None
    return {"relatos": relatos, "limite": 100,
            "recorrencias": _recorrencias_ou_indisponivel(), "ambiente": AMBIENTE}


class VotoEntrada(BaseModel):
    id_sessao: str = Field(min_length=1, max_length=128)
    voto: int = Field(strict=True)


@app.post("/api/comunidade/relatos/{id_relato}/voto")
def votar_relato(id_relato: int, entrada: VotoEntrada):
    from src.supabase_db import conectar_supabase, votar_supabase

    if id_relato <= 0 or entrada.voto not in (1, -1) or not entrada.id_sessao.strip():
        raise HTTPException(status_code=400, detail="Voto ou sessão inválida.")
    try:
        _confirmar_isolamento_sql()
        # Defesa no endpoint: não expõe a sessão do autor na consulta pública.
        registros = (conectar_supabase().table("relatos")
                     .select("id_sessao,simulado").eq("id", id_relato).limit(1).execute().data or [])
        if not registros or registros[0]["simulado"] is not SIMULADO:
            raise HTTPException(status_code=404, detail="Relato não encontrado.")
        if registros[0].get("id_sessao") == entrada.id_sessao.strip():
            raise HTTPException(status_code=409, detail="Você não pode votar no próprio relato.")
        aceito = votar_supabase(id_relato, entrada.voto, entrada.id_sessao.strip(), simulado=SIMULADO)
    except HTTPException:
        raise
    except Exception as erro:
        logger.warning("Falha ao registrar voto: %s", type(erro).__name__)
        raise HTTPException(status_code=503, detail="Não foi possível confirmar o voto. Atualize os relatos antes de tentar novamente.") from None
    if not aceito:
        raise HTTPException(status_code=409, detail="Voto não aceito. A sessão pode já ter votado ou o relato pode estar indisponível.")
    _invalidar_atualizacao()
    return {"status": "registrado"}


class VerificacaoEntrada(BaseModel):
    id_sessao: str = Field(min_length=1, max_length=128)
    continua: bool = Field(strict=True)


@app.post("/api/comunidade/relatos/{id_relato}/verificacao")
def verificar_continuidade(id_relato: int, entrada: VerificacaoEntrada):
    from src.supabase_db import conectar_supabase, registrar_verificacao_supabase

    sessao = entrada.id_sessao.strip()
    if id_relato <= 0 or not sessao:
        raise HTTPException(status_code=400, detail="Relato ou sessão inválida.")
    try:
        _confirmar_isolamento_sql()
        registros = (conectar_supabase().table("relatos")
                     .select("status,categoria,simulado").eq("id", id_relato)
                     .limit(1).execute().data or [])
        if not registros or registros[0]["simulado"] is not SIMULADO:
            raise HTTPException(status_code=404, detail="Relato não encontrado.")
        if registros[0]["status"] != "ativo" or registros[0]["categoria"] not in {
            "Iluminação insuficiente", "Problema na calçada", "Obras ou bloqueios", "Tumulto ou confusão"
        }:
            raise HTTPException(status_code=409, detail="Verificação indisponível para este relato.")
        aceito = registrar_verificacao_supabase(id_relato, sessao, entrada.continua)
    except HTTPException:
        raise
    except Exception as erro:
        logger.warning("Falha ao verificar continuidade: %s", type(erro).__name__)
        raise HTTPException(status_code=503, detail="Não foi possível confirmar a verificação. Atualize os relatos antes de tentar novamente.") from None
    if not aceito:
        raise HTTPException(status_code=409, detail="Verificação não aceita. Você pode já ter respondido nas últimas duas horas ou o alerta pode ter expirado.")
    _invalidar_atualizacao()
    return {"status": "registrado"}


@app.get("/api/enderecos/sugestoes")
def sugerir_enderecos(q: str = Query(min_length=2, max_length=120)):
    from src.catalogo_enderecos import sugerir
    return {"sugestoes": sugerir(q)}
