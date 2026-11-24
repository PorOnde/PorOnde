
from datetime import date, datetime, time, timedelta, timezone
import math

import pandas as pd
import streamlit as st
from supabase import create_client

from src.config import (
    BBOX_VM,
    CATEGORIAS_VALIDADE_HORAS,
    LIMITE_RELATOS_POR_HORA,
    MAX_CARACTERES_DESCRICAO,
)


# Horário de Brasília.
# Para as datas de 2026, São Paulo utiliza UTC-3.
FUSO_SP = timezone(timedelta(hours=-3))


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

    descricao = str(descricao or "").strip()
    rua = str(rua or "").strip() or None

    # 1. Validação da categoria
    if categoria not in CATEGORIAS_VALIDADE_HORAS:
        return "Categoria inválida."

    # Obras e bloqueios precisam do nome da rua
    # para que a regra de ativação funcione.
    if categoria == "Obras ou bloqueios" and not rua:
        return "Informe o nome da rua onde existe a obra ou o bloqueio."

    # 2. Validação da descrição
    if not descricao or len(descricao) > MAX_CARACTERES_DESCRICAO:
        return (
            f"A descrição deve ter entre 1 e "
            f"{MAX_CARACTERES_DESCRICAO} caracteres."
        )

    # 3. Validação da sessão
    if not id_sessao:
        return "Sessão inválida."

    # 4. Validação das coordenadas
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

    # 5. Preparação das datas
    agora = datetime.now(timezone.utc)
    agora_sp = agora.astimezone(FUSO_SP)

    ocorrido_em = None
    horario_foi_informado = False

    # 6. Regras específicas para roubo ou furto
    if categoria == "Roubo ou furto relatado":

        if data_ocorrencia is None or str(data_ocorrencia).strip() == "":
            return "Informe a data em que a ocorrência aconteceu."

        try:
            # Converte a data informada.
            if isinstance(data_ocorrencia, datetime):
                data = data_ocorrencia.date()

            elif isinstance(data_ocorrencia, date):
                data = data_ocorrencia

            else:
                data = date.fromisoformat(str(data_ocorrencia))

            # Não permite uma data futura.
            if data > agora_sp.date():
                return "A data não pode estar no futuro."

            # Se o horário não for informado, usamos meio-dia
            # somente como referência para o banco.
            # Isso NÃO significa que a ocorrência aconteceu ao meio-dia.
            if (
                horario_ocorrencia is None
                or str(horario_ocorrencia).strip() == ""
            ):
                hora = time(12, 0)
                horario_foi_informado = False

            elif isinstance(horario_ocorrencia, time):
                hora = horario_ocorrencia
                horario_foi_informado = True

            else:
                hora = time.fromisoformat(str(horario_ocorrencia))
                horario_foi_informado = True

            # Converte a data e a hora para UTC.
            ocorrido_em = datetime.combine(
                data,
                hora,
                tzinfo=FUSO_SP,
            ).astimezone(timezone.utc)

            # Não permite horário conhecido no futuro.
            if horario_foi_informado and ocorrido_em > agora:
                return "A ocorrência não pode estar no futuro."

            # Limite de 20 dias.
            # Quando o horário é desconhecido, comparamos
            # apenas as datas para não rejeitar um dia válido
            # por causa do meio-dia utilizado como referência.
            if horario_foi_informado:
                if ocorrido_em < agora - timedelta(days=20):
                    return (
                        "Só é possível registrar ocorrências "
                        "dos últimos 20 dias."
                    )
            else:
                data_limite = agora_sp.date() - timedelta(days=20)

                if data < data_limite:
                    return (
                        "Só é possível registrar ocorrências "
                        "dos últimos 20 dias."
                    )

        except (ValueError, TypeError, OverflowError):
            return "Data ou horário da ocorrência inválido."

    # 7. Limite de relatos por sessão
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

    # 8. Prazo inicial do relato
    expira_em = agora + timedelta(
        hours=CATEGORIAS_VALIDADE_HORAS[categoria]
    )

    # 9. Dados enviados ao Supabase
    dados = {
        "categoria": categoria,
        "descricao": descricao,
        "lat": lat,
        "lon": lon,
        "rua": rua,
        "horario_informado": horario_foi_informado,
        "ocorrido_em": (
            ocorrido_em.isoformat()
            if ocorrido_em is not None
            else None
        ),
        "criado_em": agora.isoformat(),
        "expira_em": expira_em.isoformat(),
        "status": "pendente",
        "id_sessao": id_sessao,
        "simulado": False,
        "afeta_score": False,
    }

    # 10. Registro no banco
    resultado = (
        cliente.table("relatos")
        .insert(dados)
        .execute()
    )

    if not resultado.data:
        return "Não foi possível registrar o relato."

    return resultado.data[0]["id"]


def votar_supabase(id_relato, voto, id_sessao):
    """Registra um voto pela função existente no PostgreSQL."""

    if not id_sessao or voto not in (1, -1):
        return False

    resposta = (
        conectar_supabase()
        .rpc(
            "registrar_voto",
            {
                "p_id_relato": int(id_relato),
                "p_id_sessao": id_sessao,
                "p_voto": voto,
            },
        )
        .execute()
    )

    return resposta.data is True


def registrar_verificacao_supabase(id_relato, id_sessao, continua):
    """Registra se um alerta ainda continua acontecendo."""

    if not id_sessao or not isinstance(continua, bool):
        return False

    resposta = (
        conectar_supabase()
        .rpc(
            "registrar_verificacao_alerta",
            {
                "p_id_relato": int(id_relato),
                "p_id_sessao": id_sessao,
                "p_continua": continua,
            },
        )
        .execute()
    )

    return resposta.data is True


def atualizar_alertas_supabase():
    """Executa as regras de atualização dos alertas."""

    cliente = conectar_supabase()

    expirados = (
        cliente.rpc("expirar_alertas")
        .execute()
        .data
    )

    ativados = (
        cliente.rpc("ativar_alertas")
        .execute()
        .data
    )

    renovados = (
        cliente.rpc("renovar_alertas")
        .execute()
        .data
    )

    recorrencias = (
        cliente.rpc("identificar_recorrencias_roubo_furto")
        .execute()
        .data
    )

    return {
        "expirados": expirados,
        "ativados": ativados,
        "renovados": renovados,
        "recorrencias": recorrencias,
    }


def listar_alertas_ativos_supabase():
    """Consulta os alertas ativos armazenados no Supabase."""

    atualizar_alertas_supabase()

    colunas = [
        "id",
        "categoria",
        "descricao",
        "lat",
        "lon",
        "rua",
        "criado_em",
        "ativado_em",
        "expira_em",
        "confirmacoes",
        "rejeicoes",
        "saldo",
        "simulado",
        "afeta_score",
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
    """Conta quantos relatos existem em cada status."""

    atualizar_alertas_supabase()

    contagens = {
        "pendente": 0,
        "ativo": 0,
        "rejeitado": 0,
        "expirado": 0,
    }

    cliente = conectar_supabase()

    for status in contagens:
        resposta = (
            cliente.table("relatos")
            .select("id", count="exact", head=True)
            .eq("status", status)
            .execute()
        )

        contagens[status] = resposta.count or 0

    return contagens


def listar_recorrencias_ativas_supabase():
    """Consulta recorrências de roubo ou furto ainda válidas."""

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
