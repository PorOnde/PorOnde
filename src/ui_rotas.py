import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

import pydeck as pdk
import streamlit as st

from src.rotas import (
    calcular_rota,
    coordenadas_da_rota,
    localizar_endereco,
)

st.set_page_config(
    page_title="PorOnde? | Rotas",
    page_icon="🧭",
    layout="wide",
)

st.title("PorOnde?")
st.caption(
    "Compare o trajeto a pé dentro da Vila Mariana. "
    "Tempo e distância não representam garantia de segurança."
)

st.subheader("Calcular rota")

with st.form("form_rota"):
    coluna_origem, coluna_destino = st.columns(2)

    with coluna_origem:
        st.markdown("**Origem**")
        endereco_origem = st.text_input(
            "Endereço de origem",
            placeholder="Ex.: Estação Vila Mariana",
        )

    with coluna_destino:
        st.markdown("**Destino**")
        endereco_destino = st.text_input(
            "Endereço de destino",
            placeholder="Ex.: Rua Domingos de Morais, 2564",
        )

    calcular = st.form_submit_button("Calcular rota")

if calcular:
    if not endereco_origem or not endereco_destino:
        st.warning("Preencha origem e destino antes de calcular.")
    else:
        try:
            latitude_origem, longitude_origem = localizar_endereco(endereco_origem)
            latitude_destino, longitude_destino = localizar_endereco(endereco_destino)

            rota = calcular_rota(
                latitude_origem,
                longitude_origem,
                latitude_destino,
                longitude_destino,
            )

            rota["coordenadas"] = coordenadas_da_rota(rota["nos"])
            rota["origem"] = [longitude_origem, latitude_origem]
            rota["destino"] = [longitude_destino, latitude_destino]

            st.session_state["rota"] = rota

        except ValueError as erro:
            st.error(str(erro))

if "rota" in st.session_state:
    rota = st.session_state["rota"]

    coluna_distancia, coluna_tempo = st.columns(2)
    coluna_distancia.metric("Distância", f"{rota['distancia_metros']} m")
    coluna_tempo.metric("Tempo estimado", f"{rota['tempo_minutos']} min")

    dados_rota = [{"caminho": rota["coordenadas"]}]

    dados_pontos = [
        {
            "nome": "Origem",
            "coordenada": rota["origem"],
            "cor": [34, 139, 34],
        },
        {
            "nome": "Destino",
            "coordenada": rota["destino"],
            "cor": [198, 68, 17],
        },
    ]

    camada_rota = pdk.Layer(
        "PathLayer",
        data=dados_rota,
        get_path="caminho",
        get_color=[198, 68, 17],
        width_scale=8,
        width_min_pixels=4,
        pickable=False,
    )

    camada_pontos = pdk.Layer(
        "ScatterplotLayer",
        data=dados_pontos,
        get_position="coordenada",
        get_color="cor",
        get_radius=35,
        radius_min_pixels=6,
        pickable=True,
    )

    centro_latitude = (rota["origem"][1] + rota["destino"][1]) / 2
    centro_longitude = (rota["origem"][0] + rota["destino"][0]) / 2

    mapa = pdk.Deck(
        layers=[camada_rota, camada_pontos],
        initial_view_state=pdk.ViewState(
            latitude=centro_latitude,
            longitude=centro_longitude,
            zoom=14,
            pitch=0,
        ),
        map_style=None,
        tooltip={"text": "{nome}"},
    )

    st.subheader("Trajeto calculado")
    st.pydeck_chart(
        mapa,
        width="stretch",
        height=500,
        alt="Mapa com origem, destino e trajeto calculado.",
    )