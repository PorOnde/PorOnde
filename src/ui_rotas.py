
import streamlit as st
from streamlit_folium import st_folium

from src import config
from src.mapa import criar_mapa
from src.rotas import (
    calcular_alternativas,
    coordenadas_da_rota,
    localizar_endereco,
    locais_apoio_proximos,
)


def aba_rotas():
    """Exibe a comparação de rotas a pé na Vila Mariana."""

    st.title("PorOnde?")
    st.caption(
        "Compare trajetos a pé dentro da Vila Mariana. "
        "Tempo, distância e scores não garantem segurança."
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
            endereco_origem = st.text_input(
                "Endereço de origem",
                placeholder="Ex.: Estação Vila Mariana",
            )

        with coluna_destino:
            endereco_destino = st.text_input(
                "Endereço de destino",
                placeholder="Ex.: Rua Gandavo, 550",
            )

        calcular = st.form_submit_button("Calcular rota")

    if calcular:
        # Remove resultados antigos antes de uma nova tentativa.
        st.session_state.pop("alternativas_rotas", None)
        st.session_state.pop("rota", None)
        st.session_state.pop("rota_selecionada", None)

        if not endereco_origem.strip() or not endereco_destino.strip():
            st.warning("Preencha origem e destino antes de calcular.")
        else:
            try:
                latitude_origem, longitude_origem = localizar_endereco(
                    endereco_origem
                )
                latitude_destino, longitude_destino = localizar_endereco(
                    endereco_destino
                )

                alternativas = calcular_alternativas(
                    latitude_origem,
                    longitude_origem,
                    latitude_destino,
                    longitude_destino,
                )

                for alternativa in alternativas:
                    alternativa["coordenadas"] = coordenadas_da_rota(
                        alternativa["nos"]
                    )
                    alternativa["origem"] = [
                        longitude_origem,
                        latitude_origem,
                    ]
                    alternativa["destino"] = [
                        longitude_destino,
                        latitude_destino,
                    ]
                    alternativa["locais_apoio"] = locais_apoio_proximos(
                        alternativa["nos"]
                    )

                st.session_state["alternativas_rotas"] = alternativas

            except ValueError as erro:
                st.error(str(erro))

    if "alternativas_rotas" not in st.session_state:
        return

    alternativas = st.session_state["alternativas_rotas"]

    st.subheader("Compare as alternativas")

    nomes = [alternativa["nome"] for alternativa in alternativas]

    nome_selecionado = st.radio(
        "Escolha uma rota para destacar no mapa",
        options=nomes,
        horizontal=True,
        key="rota_selecionada",
    )

    rota = next(
        alternativa
        for alternativa in alternativas
        if alternativa["nome"] == nome_selecionado
    )

    # Mantém compatibilidade com outras partes do aplicativo
    # que possam utilizar a rota selecionada.
    st.session_state["rota"] = rota

    for alternativa in alternativas:
        with st.container(border=True):
            st.markdown(f"**{alternativa['nome']}**")

            coluna_distancia, coluna_tempo, coluna_score = st.columns(3)

            coluna_distancia.metric(
                "Distância",
                f"{alternativa['distancia_metros']} m",
            )
            coluna_tempo.metric(
                "Tempo estimado",
                f"{alternativa['tempo_minutos']} min",
            )
            coluna_score.metric(
                "Score de contexto",
                f"{alternativa['score_contexto']:.1f}/100",
            )

            st.caption(
                "Score de iluminação: "
                f"{alternativa['score_iluminacao']:.1f}/100"
            )

    st.subheader(f"Mapa — {rota['nome']}")

    mapa = criar_mapa(rota, alternativas)

    st_folium(
        mapa,
        width=None,
        height=500,
        use_container_width=True,
        returned_objects=[],
    )

    st.subheader("Locais úteis próximos à rota selecionada")

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