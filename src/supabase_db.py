from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st
from supabase import create_client

from src.config import (
    BBOX_VM,
    CATEGORIAS_VALIDADE_HORAS,
    LIMITE_RELATOS_POR_HORA,
    MAX_CARACTERES_DESCRICAO,
)


@st.cache_resource
def conectar_supabase():
    """Cria uma conexão privada com o Supabase."""
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["secret_key"],
    )

def listar_relatos_supabase():
    """Consulta os relatos armazenados no Supabase."""
    cliente = conectar_supabase()

    resposta = (
        cliente.table("relatos")
        .select("*")
        .limit(100)
        .execute()
    )

    return resposta.data

def registrar_relato_supabase(categoria, descricao, lat, lon, id_sessao):
    """Valida e registra um relato no Supabase."""
    descricao = descricao.strip()

    if categoria not in CATEGORIAS_VALIDADE_HORAS:
        return "Categoria inválida."

    if not descricao or len(descricao) > MAX_CARACTERES_DESCRICAO:
        return "A descrição deve ter entre 1 e 200 caracteres."

    if not id_sessao:
        return "Sessão inválida."

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return "Coordenadas inválidas."

    sul, norte, oeste, leste = BBOX_VM

    if not (sul <= lat <= norte and oeste <= lon <= leste):
        return "O relato precisa estar dentro da Vila Mariana."

    cliente = conectar_supabase()
    agora = datetime.now(timezone.utc)
    inicio = agora - timedelta(hours=1)

    resposta = (
        cliente.table("relatos")
        .select("id")
        .eq("id_sessao", id_sessao)
        .gte("criado_em", inicio.isoformat())
        .limit(LIMITE_RELATOS_POR_HORA)
        .execute()
    )

    if len(resposta.data) >= LIMITE_RELATOS_POR_HORA:
        return "Limite de relatos por hora atingido."

    expira_em = agora + timedelta(
        hours=CATEGORIAS_VALIDADE_HORAS[categoria]
    )

    resultado = cliente.table("relatos").insert({
        "categoria": categoria,
        "descricao": descricao,
        "lat": lat,
        "lon": lon,
        "criado_em": agora.isoformat(),
        "expira_em": expira_em.isoformat(),
        "status": "pendente",
        "id_sessao": id_sessao,
        "simulado": False,
    }).execute()

    return resultado.data[0]["id"]

def votar_supabase(id_relato, voto, id_sessao):
    """Registra um voto por meio da função segura do PostgreSQL."""
    if not id_sessao or voto not in (1, -1):
        return False

    resposta = conectar_supabase().rpc(
        "registrar_voto",
        {
            "p_id_relato": int(id_relato),
            "p_id_sessao": id_sessao,
            "p_voto": voto,
        },
    ).execute()

    return resposta.data is True


def atualizar_alertas_supabase():
    """Atualiza os alertas expirados e ativa os relatos elegíveis."""
    cliente = conectar_supabase()

    expirados = cliente.rpc("expirar_alertas").execute().data
    ativados = cliente.rpc("ativar_alertas").execute().data

    return {
        "expirados": expirados,
        "ativados": ativados,
    }

def listar_alertas_ativos_supabase():
    """Consulta os alertas ativos armazenados no Supabase."""
    atualizar_alertas_supabase()

    colunas = [
        "id", "categoria", "descricao", "lat", "lon",
        "criado_em", "expira_em", "confirmacoes",
        "rejeicoes", "saldo", "simulado",
    ]

    resposta = (
        conectar_supabase()
        .table("relatos")
        .select("*")
        .eq("status", "ativo")
        .order("criado_em", desc=True)
        .limit(100)
        .execute()
    )

    alertas = pd.DataFrame(resposta.data)

    if alertas.empty:
        return pd.DataFrame(columns=colunas)

    alertas["saldo"] = (
        alertas["confirmacoes"] - alertas["rejeicoes"]
    )

    return alertas.reindex(columns=colunas)


def contar_relatos_supabase():
    """Conta os relatos de cada status no Supabase."""
    atualizar_alertas_supabase()

    contagens = {
        "pendente": 0,
        "ativo": 0,
        "rejeitado": 0,
        "expirado": 0,
    }

    for status in contagens:
        resposta = (
            conectar_supabase()
            .table("relatos")
            .select("id", count="exact", head=True)
            .eq("status", status)
            .execute()
        )
        contagens[status] = resposta.count or 0

    return contagens