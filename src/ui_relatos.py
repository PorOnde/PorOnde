import sys
import uuid
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

import streamlit as st

from src.config import BBOX_VM, CATEGORIAS_VALIDADE_HORAS
from src.relatos import (
    atualizar_status,
    listar_alertas_ativos,
    registrar_relato,
    votar,
)


st.set_page_config(
    page_title="PorOnde? | Relatos",
    page_icon="📍",
    layout="centered",
)


if "id_sessao" not in st.session_state:
    st.session_state.id_sessao = str(uuid.uuid4())


sul, norte, oeste, leste = BBOX_VM
lat_centro = (sul + norte) / 2
lon_centro = (oeste + leste) / 2


st.title("Relatos da região")
st.caption(
    "Os relatos precisam de confirmação e têm prazo de validade. "
    "Eles não representam garantia de segurança."
)


contagens = atualizar_status()

coluna_1, coluna_2, coluna_3, coluna_4 = st.columns(4)
coluna_1.metric("Pendentes", contagens["pendente"])
coluna_2.metric("Ativos", contagens["ativo"])
coluna_3.metric("Rejeitados", contagens["rejeitado"])
coluna_4.metric("Expirados", contagens["expirado"])


st.divider()
st.subheader("Registrar um relato")

with st.form("formulario_relato"):
    categoria = st.selectbox(
        "Categoria",
        list(CATEGORIAS_VALIDADE_HORAS),
    )

    descricao = st.text_area(
        "Descrição",
        max_chars=200,
        placeholder="Descreva o que você observou.",
    )

    coluna_lat, coluna_lon = st.columns(2)

    with coluna_lat:
        lat = st.number_input(
            "Latitude",
            min_value=float(sul),
            max_value=float(norte),
            value=float(lat_centro),
            format="%.6f",
        )

    with coluna_lon:
        lon = st.number_input(
            "Longitude",
            min_value=float(oeste),
            max_value=float(leste),
            value=float(lon_centro),
            format="%.6f",
        )

    enviar = st.form_submit_button("Enviar relato")


if enviar:
    if not descricao.strip():
        st.error("Escreva uma descrição antes de enviar.")

    else:
        resultado = registrar_relato(
            categoria,
            descricao.strip(),
            lat,
            lon,
            st.session_state.id_sessao,
        )

        if isinstance(resultado, int):
            st.success("Relato enviado para validação.")
            st.rerun()

        else:
            st.error(resultado)


st.divider()
st.subheader("Alertas ativos")

alertas = listar_alertas_ativos()

if alertas.empty:
    st.info("Ainda não há alertas ativos.")

else:
    for _, alerta in alertas.iterrows():
        with st.container(border=True):
            st.markdown(f"**{alerta['categoria']}**")
            st.write(alerta["descricao"])

            st.caption(
                f"Confirmações: {alerta['confirmacoes']} | "
                f"Rejeições: {alerta['rejeicoes']} | "
                f"Expira em: {alerta['expira_em']}"
            )

            confirmar, rejeitar = st.columns(2)

            with confirmar:
                if st.button(
                    "Confirmar",
                    key=f"confirmar_{alerta['id']}",
                ):
                    resultado = votar(
                        int(alerta["id"]),
                        1,
                        st.session_state.id_sessao,
                    )

                    if resultado:
                        st.rerun()

                    st.warning(
                        "Você já votou neste relato ou ele não está disponível."
                    )

            with rejeitar:
                if st.button(
                    "Não confirma",
                    key=f"rejeitar_{alerta['id']}",
                ):
                    resultado = votar(
                        int(alerta["id"]),
                        -1,
                        st.session_state.id_sessao,
                    )

                    if resultado:
                        st.rerun()

                    st.warning(
                        "Você já votou neste relato ou ele não está disponível."
                    )