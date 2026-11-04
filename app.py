import streamlit as st

from src.ui_relatos import aba_relatos
from src.ui_rotas import aba_rotas


st.set_page_config(
    page_title="PorOnde?",
    page_icon="🗺️",
    layout="wide",
)

aba_rotas_tab, aba_relatos_tab, aba_salvas_tab, aba_sobre_tab = st.tabs(
    [
        "Rotas",
        "Relatos",
        "Rotas salvas",
        "Sobre",
    ]
)

with aba_rotas_tab:
    aba_rotas()

with aba_relatos_tab:
    aba_relatos()

with aba_salvas_tab:
    st.header("Rotas salvas")
    st.info("Esta funcionalidade será implementada na próxima etapa.")

with aba_sobre_tab:
    st.header("Sobre o PorOnde?")
    st.write(
        "O PorOnde? ajuda a comparar trajetos a pé na Vila Mariana "
        "com informações de distância, tempo, relatos da região "
        "e locais úteis próximos ao caminho."
    )
    st.caption(
        "As informações apresentadas não representam garantia de segurança."
    )