import logging
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

app = FastAPI(title="PorOnde? API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


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
    "confirmacoes,rejeicoes,afeta_score"
)


def _consultar_relatos_validos(limite_mapa=False):
    from datetime import datetime, timezone
    from src.supabase_db import conectar_supabase, atualizar_alertas_supabase

    atualizar_alertas_supabase()
    cliente = conectar_supabase()
    instante = datetime.now(timezone.utc).isoformat()
    tamanho = 100 if limite_mapa else 200
    relatos = []
    while True:
        consulta = (cliente.table("relatos").select(COLUNAS_COMUNIDADE)
                    .in_("status", ["pendente", "ativo"])
                    .eq("simulado", False).gt("expira_em", instante))
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


@app.get("/api/rotas")
def buscar_rotas(origem_lat: float, origem_lon: float,
                 destino_lat: float, destino_lon: float):
    import pandas as pd
    from src.abrigos import listar_abrigos
    from src.rotas import calcular_alternativas, coordenadas_da_rota

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

    try:
        alternativas = calcular_alternativas(
            origem_lat, origem_lon, destino_lat, destino_lon,
            alertas_ativos=alertas,
        )
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro

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
        })

    return {
        "quantidade": len(resultados),
        "alertas_disponiveis": comunidade_disponivel,
        "rotas": resultados,
    }


@app.get("/api/geocodificar")
def geocodificar_endereco(endereco: str):
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

    try:
        resultado = registrar_relato_supabase(
            categoria=relato.categoria,
            descricao=relato.descricao,
            lat=relato.lat,
            lon=relato.lon,
            id_sessao=sessao,
            rua=relato.rua,
            data_ocorrencia=relato.data_ocorrencia,
            horario_ocorrencia=relato.horario_ocorrencia,
        )
    except Exception as erro:
        logger.warning("Falha ao registrar relato: %s", type(erro).__name__)
        raise HTTPException(status_code=503, detail="Não foi possível concluir o envio do relato.") from None

    # A função original retorna uma mensagem de validação ou o ID numérico.
    if isinstance(resultado, str):
        raise HTTPException(status_code=400, detail=resultado)
    if type(resultado) is not int:
        raise HTTPException(status_code=500, detail="Resposta inesperada no registro do relato.")

    return {"id": resultado, "status": "pendente", "afeta_score": False}


@app.get("/api/comunidade/relatos")
def consultar_comunidade():
    try:
        relatos = _consultar_relatos_validos(limite_mapa=True)
    except Exception as erro:
        logger.warning("Falha na consulta comunitária: %s", type(erro).__name__)
        raise HTTPException(status_code=503, detail="Não foi possível consultar os relatos e alertas.") from None
    return {"relatos": relatos, "limite": 100}


class VotoEntrada(BaseModel):
    id_sessao: str = Field(min_length=1, max_length=128)
    voto: int


@app.post("/api/comunidade/relatos/{id_relato}/voto")
def votar_relato(id_relato: int, entrada: VotoEntrada):
    from src.supabase_db import conectar_supabase, votar_supabase

    if id_relato <= 0 or entrada.voto not in (1, -1) or not entrada.id_sessao.strip():
        raise HTTPException(status_code=400, detail="Voto ou sessão inválida.")
    try:
        # Defesa no endpoint: não expõe a sessão do autor na consulta pública.
        registros = (conectar_supabase().table("relatos")
                     .select("id_sessao").eq("id", id_relato).limit(1).execute().data or [])
        if not registros:
            raise HTTPException(status_code=404, detail="Relato não encontrado.")
        if registros[0].get("id_sessao") == entrada.id_sessao.strip():
            raise HTTPException(status_code=409, detail="Você não pode votar no próprio relato.")
        aceito = votar_supabase(id_relato, entrada.voto, entrada.id_sessao.strip())
    except HTTPException:
        raise
    except Exception as erro:
        logger.warning("Falha ao registrar voto: %s", type(erro).__name__)
        raise HTTPException(status_code=503, detail="Não foi possível confirmar o voto. Atualize os relatos antes de tentar novamente.") from None
    if not aceito:
        raise HTTPException(status_code=409, detail="Voto não aceito. A sessão pode já ter votado ou o relato pode estar indisponível.")
    return {"status": "registrado"}
