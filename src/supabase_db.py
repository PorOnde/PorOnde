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


def registrar_relato_supabase(
    categoria,
    descricao,
    lat,
    lon,
    id_sessao,
    rua=None,
    data_ocorrencia=None,
    horario_ocorrencia=None,
):
    """Valida e registra um relato no Supabase."""
    from datetime import date, time
    import math

    descricao = str(descricao or "").strip()
    rua = str(rua or "").strip() or None

    if categoria not in CATEGORIAS_VALIDADE_HORAS:
        return "Categoria inválida."

    if not descricao or len(descricao) > MAX_CARACTERES_DESCRICAO:
        return "A descrição deve ter entre 1 e 200 caracteres."

    if not id_sessao:
        return "Sessão inválida."

    try:
        lat = float(lat)
        lon = float(lon)
        if not math.isfinite(lat) or not math.isfinite(lon):
            return "Coordenadas inválidas."
    except (TypeError, ValueError):
        return "Coordenadas inválidas."

    sul, norte, oeste, leste = BBOX_VM

    if not (sul <= lat <= norte and oeste <= lon <= leste):
        return "O relato precisa estar dentro da Vila Mariana."

    agora = datetime.now(timezone.utc)
    ocorrido_em = None

    if categoria == "Roubo ou furto relatado":
        if data_ocorrencia is None or str(data_ocorrencia).strip() == "":
            return "Informe a data em que a ocorrência aconteceu."

        try:
            if isinstance(data_ocorrencia, datetime):
                data = data_ocorrencia.date()
            elif isinstance(data_ocorrencia, date):
                data = data_ocorrencia
            else:
                data = date.fromisoformat(str(data_ocorrencia))

            if data > agora.astimezone(
                timezone(timedelta(hours=-3))
            ).date():
                return "A data não pode estar no futuro."

            if horario_ocorrencia is None or str(horario_ocorrencia).strip() == "":
                # Meio-dia apenas como referência técnica.
                # Não representa um horário confirmado.
                hora = time(12, 0)
                horario_foi_informado = False
            elif isinstance(horario_ocorrencia, time):
                hora = horario_ocorrencia
                horario_foi_informado = True
            else:
                hora = time.fromisoformat(str(horario_ocorrencia))
                horario_foi_informado = True

            fuso_sp = timezone(timedelta(hours=-3))
            ocorrido_em = datetime.combine(
                data, hora, tzinfo=fuso_sp
            ).astimezone(timezone.utc)

            if ocorrido_em < agora - timedelta(days=20):
                return "Só é possível registrar ocorrências dos últimos 20 dias."

        except (ValueError, TypeError):
            return "Data ou horário da ocorrência inválido."

    cliente = conectar_supabase()
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

    dados = {
        "categoria": categoria,
        "descricao": descricao,
        "lat": lat,
        "lon": lon,
        "rua": rua,
        "horario_informado": (
        horario_foi_informado
        if categoria == "Roubo ou furto relatado"
    else False
),
        "ocorrido_em": (
            ocorrido_em.isoformat() if ocorrido_em else None
        ),
        "criado_em": agora.isoformat(),
        "expira_em": expira_em.isoformat(),
        "status": "pendente",
        "id_sessao": id_sessao,
        "simulado": False,
        "afeta_score": False,
    }

    resultado = (
        cliente.table("relatos")
        .insert(dados)
        .execute()
    )

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

def registrar_verificacao_supabase(id_relato, id_sessao, continua):
    """Registra se um alerta ainda continua acontecendo."""
    if not id_sessao or not isinstance(continua, bool):
        return False

    resposta = conectar_supabase().rpc(
        "registrar_verificacao_alerta",
        {
            "p_id_relato": int(id_relato),
            "p_id_sessao": id_sessao,
            "p_continua": continua,
        },
    ).execute()

    return resposta.data is True


def atualizar_alertas_supabase():
    """Atualiza os alertas expirados e ativa os relatos elegíveis."""
    cliente = conectar_supabase()

    expirados = cliente.rpc("expirar_alertas").execute().data
    ativados = cliente.rpc("ativar_alertas").execute().data
    renovados = cliente.rpc("renovar_alertas").execute().data
    recorrencias = cliente.rpc(
    "identificar_recorrencias_roubo_furto"
    ).execute().data

    return {
        "expirados": expirados,
        "ativados": ativados,
        "recorrencias": recorrencias,
        "renovados": renovados,
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

def listar_recorrencias_ativas_supabase():
    """Consulta somente recorrências de roubo ou furto ainda válidas."""
    agora = datetime.now(timezone.utc).isoformat()

    resposta = (
        conectar_supabase()
        .table("recorrencias_roubo_furto")
        .select("*")
        .gt("expira_em", agora)
        .order("ativado_em", desc=True)
        .limit(100)
        .execute()
    )

    return resposta.data