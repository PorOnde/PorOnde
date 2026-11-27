import json
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

from src.config import PASTA_DADOS, RAIZ_PROJETO


ASSETS = RAIZ_PROJETO / "assets"


def abrir_trajeto():
    st.session_state["pagina"] = "Trajeto"


def inicio():
    with st.container(key="abertura"):
        intro, imagem = st.columns(2, vertical_alignment="center")

        with intro:
            st.html(
                '<h1 class="poronde-titulo"><span>Compare</span>'
                '<span class="palavra-verde">caminhos</span>'
                '<span>a pé</span></h1>'
            )
            st.write("Compare tempo, iluminação e locais de apoio em cada rota.")
            st.button("Buscar um trajeto", type="primary", on_click=abrir_trajeto)

        with imagem:
            st.image(str(ASSETS / "rua.svg"), width="stretch")

    st.divider()
    st.header("Como funciona", anchor=False)

    passos = (
        (
            "Defina seu trajeto",
            "Informe origem e destino.",
            '<path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"/>'
            '<circle cx="12" cy="10" r="2.5"/>',
        ),
        (
            "Compare as opções",
            "Veja as rotas lado a lado.",
            '<circle cx="6" cy="5" r="2.5"/><circle cx="18" cy="19" r="2.5"/>'
            '<path d="M6 7.5V16a3 3 0 0 0 3 3h2M18 16.5V8a3 3 0 0 0-3-3h-2"/>',
        ),
        (
            "Entenda a pontuação",
            "Veja o que entrou na nota.",
            '<path d="M4 19a10 10 0 1 1 16 0M12 14l4-5"/>',
        ),
    )

    for coluna, (titulo, texto, desenho) in zip(st.columns(3), passos):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            'fill="none" stroke="#17191e" stroke-width="1.7" '
            f'stroke-linecap="round" stroke-linejoin="round">{desenho}</svg>'
        )
        coluna.html(
            f'<img src="data:image/svg+xml,{quote(svg, safe="")}" '
            'width="24" height="24" alt="">'
        )
        coluna.subheader(titulo, anchor=False)
        coluna.write(texto)

    st.divider()

    mapa_svg = (ASSETS / "previa-mapa.svg").read_text(encoding="utf-8")
    mapa_svg = (
        mapa_svg.replace("#fcfbf8", "#ffffff")
        .replace("#e6e8e2", "#d8d7d4")
        .replace("#399e60", "#00b753")
        .replace("#c78d11", "#fbd530")
    )

    itens_mapa = (
        (
            "Tempo e distância",
            '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
        ),
        (
            "Iluminação cadastrada",
            '<path d="M9 18h6m-5 4h4m-5-8a6 6 0 1 1 6 0"/>',
        ),
        (
            "Ocorrências registradas",
            '<path d="M10 3.8 2.4 17a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 '
            '1.7-3L14 3.8a2.3 2.3 0 0 0-4 0ZM12 9v4m0 3h.01"/>',
        ),
        (
            "Locais de apoio",
            '<path d="M3 10l2-5h14l2 5M4 10v10h16V10M9 20v-6h6v6M2 10h20"/>',
        ),
    )

    linhas = []
    for texto, desenho in itens_mapa:
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            'fill="none" stroke="#17191e" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round">{desenho}</svg>'
        )
        linhas.append(
            f'<li><img src="data:image/svg+xml,{quote(svg, safe="")}" alt="">'
            f'{texto}</li>'
        )

    st.html(f"""
        <style>
          .poronde-mapa-inicio {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
            align-items: center;
            gap: 48px;
            font-family: Manrope, system-ui, sans-serif;
          }}
          .poronde-mapa-inicio figure {{
            margin: 0;
            padding: 16px;
            background: white;
            border: 1px solid #17191e;
            border-radius: 12px;
          }}
          .poronde-mapa-inicio figure img {{
            display: block;
            width: 100%;
            height: auto;
          }}
          .poronde-mapa-inicio figcaption {{
            margin-top: 8px;
            color: #515953;
            font-size: 12px;
            line-height: 16px;
          }}
          .stApp .poronde-mapa-inicio h2 {{
            font: 500 24px / 32px Manrope, system-ui, sans-serif;
            margin: 0;
            padding: 0;
          }}
          .poronde-mapa-inicio ul {{
            margin: 24px 0 0;
            padding: 0;
            border-top: 1px solid #d8d7d4;
            list-style: none;
          }}
          .poronde-mapa-inicio li {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px 0;
            border-bottom: 1px solid #d8d7d4;
            font-size: 16px;
            line-height: 24px;
          }}
          .poronde-mapa-inicio li img {{
            width: 20px;
            height: 20px;
            flex-shrink: 0;
          }}
          @media (max-width: 767px) {{
            .poronde-mapa-inicio {{
              grid-template-columns: 1fr;
              gap: 24px;
            }}
          }}
        </style>
        <section class="poronde-mapa-inicio">
          <figure>
            <img src="data:image/svg+xml,{quote(mapa_svg, safe='')}"
                 alt="Dois caminhos para o mesmo destino">
            <figcaption>Prévia ilustrativa</figcaption>
          </figure>
          <div>
            <h2>O que você vê no mapa</h2>
            <ul>{''.join(linhas)}</ul>
          </div>
        </section>
    """)
 
    with st.container(
        key="cobertura",
        horizontal=True,
        horizontal_alignment="distribute",
        vertical_alignment="center",
        gap="medium",
    ):
        st.html(
            "<h2>Onde funciona?</h2><p>Nesta primeira versão, o PorOnde? cobre a Vila Mariana, em São Paulo.</p>",            
            width="content",
        )
        st.button(
            "Buscar um trajeto",
            key="buscar_trajeto_rodape",
            on_click=abrir_trajeto,
        )


def pesquisa():
    st.title("Nossa pesquisa", anchor=False)
    st.write("Como as pessoas escolhem seus trajetos a pé.")
    arquivo = PASTA_DADOS / "pesquisa_agregada.csv"
    if not arquivo.is_file():
        st.info("Os resultados da pesquisa serão publicados aqui.")
        return

    colunas = ["tema", "resposta", "total", "base"]
    try:
        dados = pd.read_csv(arquivo, usecols=colunas)
        dados["total"] = pd.to_numeric(dados["total"])
        dados["base"] = pd.to_numeric(dados["base"])
        invalidos = (
            dados[colunas].isna().any().any()
            or not dados["total"].between(0, dados["base"]).all()
            or not dados["base"].between(1, float("inf"), inclusive="left").all()
            or not (dados[["total", "base"]] % 1 == 0).all().all()
            or dados.duplicated(["tema", "resposta"]).any()
            or (dados.groupby("tema")["base"].nunique() > 1).any()
        )
        if dados.empty or invalidos:
            raise ValueError("Totais ou bases inválidos.")
    except (OSError, ValueError):
        st.warning("Os resultados da pesquisa estão indisponíveis no momento.")
        return

    for titulo, respostas in dados.groupby("tema", sort=False):
        st.subheader(str(titulo), anchor=False)
        st.bar_chart(
            respostas,
            x="resposta",
            y="total",
            horizontal=True,
            x_label="Respostas",
            y_label="",
            color="#197144",
        )
        st.caption(f"Base: {int(respostas['base'].iloc[0])} respostas à pergunta.")


def sobre():
    st.title("Sobre nós", anchor=False)

    st.html("""
        <style>
          .stApp .st-key-perfis_equipe {
            max-width: 880px;
            margin-inline: auto;
          }

          .stApp .st-key-perfis_equipe .poronde-perfil-reservado {
            display: block;
            width: 96px;
            height: 96px;
            border: 1px solid #bfc9c0;
            border-radius: 50%;
            background: #f0f4ef;
          }
        </style>
    """)

    historia, foto = st.columns([1, 1.2], gap="large")
    with historia:
        st.write(
            "Tudo começou com um ônibus. Um de nós sempre esperava "
            "no mesmo ponto, escuro e vazio à noite."
        )
        st.html(
            '<p>Um dia descobrimos que dava para pegar o '
            '<span class="sobre-trecho-destaque">mesmo ônibus</span> em outro '
            'ponto, mais iluminado e movimentado, a poucos minutos de caminhada.</p>'
        )
        st.write(
            "Se essa informação mudou nosso trajeto, poderia mudar o de mais gente. "
            "Assim nasceu o PorOnde?, no Samsung Innovation Campus."
        )

    foto_equipe = ASSETS / "equipe.jpg"
    if foto_equipe.is_file():
        foto.image(str(foto_equipe), width="stretch")
    else:
        foto.html('<div class="poronde-foto-reservada">Foto da equipe</div>')

    perfis = PASTA_DADOS / "equipe.json"
    equipe = (
        json.loads(perfis.read_text(encoding="utf-8"))
        if perfis.is_file()
        else [
            {"nome": f"Integrante {numero}", "bio": "Perfil a definir."}
            for numero in range(1, 4)
        ]
    )

    st.divider()
    st.header("Equipe", anchor=False)

    with st.container(key="perfis_equipe"):
        colunas = st.columns(3, gap="medium")
        for coluna, pessoa in zip(colunas, equipe[:3]):
            with coluna:
                retrato = ASSETS / Path(pessoa.get("foto") or "").name
                with st.container(horizontal=True, horizontal_alignment="center"):
                    if retrato.is_file():
                        st.image(str(retrato), width=96)
                    else:
                        st.html(
                            '<span class="poronde-perfil-reservado" '
                            'aria-hidden="true"></span>',
                            width="content",
                        )

                st.subheader(
                    pessoa["nome"],
                    anchor=False,
                    text_alignment="center",
                )
                if pessoa.get("papel"):
                    st.markdown(pessoa["papel"], text_alignment="center")
                st.markdown(pessoa["bio"], text_alignment="center")