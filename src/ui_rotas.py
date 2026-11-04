import sys
from pathlib import Path
from src import config

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

import pydeck as pdk
import streamlit as st

from src.rotas import (
    calcular_rota,
    coordenadas_da_rota,
    localizar_endereco,
    locais_apoio_proximos,
)


def aba_rotas():
    """Exibe a aba de cálculo e visualização de rotas."""

    st.title("PorOnde?")
    st.caption(
        "Compare o trajeto a pé dentro da Vila Mariana. "
        "Tempo e distância não representam garantia de segurança."
    )
    if config.ARQUIVO_SCORE == config.ARQUIVO_SCORE_EXEMPLO:
     st.warning(
            "Usando dados de exemplo para o Score de Contexto. "
            "Os dados reais serão integrados quando a Parte A for concluída."
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
                latitude_origem, longitude_origem = localizar_endereco(
                    endereco_origem
                )
                latitude_destino, longitude_destino = localizar_endereco(
                    endereco_destino
                )

                rota = calcular_rota(
                    latitude_origem,
                    longitude_origem,
                    latitude_destino,
                    longitude_destino,
                )

                rota["coordenadas"] = coordenadas_da_rota(rota["nos"])
                rota["origem"] = [longitude_origem, latitude_origem]
                rota["destino"] = [longitude_destino, latitude_destino]
                rota["locais_apoio"] = locais_apoio_proximos(rota["nos"])

                st.session_state["rota"] = rota

            except ValueError as erro:
                st.error(str(erro))

    if "rota" in st.session_state:
        rota = st.session_state["rota"]

        coluna_distancia, coluna_tempo = st.columns(2)
        coluna_distancia.metric(
            "Distância",
            f"{rota['distancia_metros']} m",
        )
        coluna_tempo.metric(
            "Tempo estimado",
            f"{rota['tempo_minutos']} min",
        )

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

        cores_grupos = {
            "abrigo_amigo": [52, 109, 173],
            "saude": [181, 49, 49],
            "seguranca": [126, 84, 32],
            "transporte_24h": [119, 70, 181],
            "outro": [90, 90, 90],
        }

        for local in rota["locais_apoio"]:
            dados_pontos.append(
                {
                    "nome": f"{local['nome']} ({local['tipo']})",
                    "coordenada": [local["lon"], local["lat"]],
                    "cor": cores_grupos.get(
                        local["grupo"],
                        [90, 90, 90],
                    ),
                }
            )

        camada_rota = pdk.Layer(
            "PathLayer",
            data=dados_rota,
            get_path="caminho",
            get_color=[198, 68, 17],
            width_scale=6,
            width_min_pixels=4,
            pickable=False,
        )

        camada_pontos = pdk.Layer(
            "ScatterplotLayer",
            data=dados_pontos,
            get_position="coordenada",
            get_color="cor",
            get_radius=45,
            pickable=True,
        )

        centro_latitude = (
            rota["origem"][1] + rota["destino"][1]
        ) / 2
        centro_longitude = (
            rota["origem"][0] + rota["destino"][0]
        ) / 2

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

        st.subheader("Locais úteis próximos ao trajeto")

        if rota["locais_apoio"]:
            for local in rota["locais_apoio"]:
                st.write(
                    f"**{local['nome']}** — {local['tipo']} "
                    f"({local['distancia_metros']} m da rota)"
                )
        else:
            st.info(
                "Não foram encontrados locais úteis a até 200 m da rota."
            )


if __name__ == "__main__":
    st.set_page_config(
        page_title="PorOnde? | Rotas",
        page_icon="🗺️",
        layout="wide",
    )
    aba_rotas()