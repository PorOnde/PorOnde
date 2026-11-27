from pathlib import Path
from datetime import date
import streamlit as st

from src.ui_paginas import inicio, pesquisa, sobre



RAIZ = Path(__file__).resolve().parent

def aba_rotas():
    from src.ui_rotas import aba_rotas as mostrar_trajeto

    mostrar_trajeto()
PAGINAS = {"Início": inicio, "Trajeto": aba_rotas, "Nossa pesquisa": pesquisa, "Sobre nós": sobre}

st.set_page_config(page_title="PorOnde?", layout="wide")
st.html(f"<style>{(RAIZ / 'assets' / 'estilo.css').read_text(encoding='utf-8')}</style>")

with st.container(key="cabecalho"):
    marca, menu = st.columns([1, 3], vertical_alignment="center")
    with marca:
        st.image(str(RAIZ / "assets" / "logo.png"), width=146)
    with menu:
        with st.container(horizontal=True, horizontal_alignment="right"):
            pagina = st.radio(
                "Navegação",
                PAGINAS,
                horizontal=True,
                label_visibility="collapsed",
                key="pagina",
                width="content",
            )

PAGINAS[pagina]()

with st.container(
    key="rodape",
    horizontal=True,
    horizontal_alignment="distribute",
    vertical_alignment="center",
    gap="medium",
):
    st.image(str(RAIZ / "assets" / "logo.png"), width=106)
    st.caption(
        f"Protótipo · Vila Mariana, São Paulo · {date.today().year}",
        width="content",
    )
