import math
from html import escape

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src import config
from src.mapa import (
    ESTILOS_ROTAS,
    GRUPOS_APOIO,
    agrupar_alertas,
    classificar_contexto,
    criar_mapa,
    nome_tipo_apoio,
)
from src.rotas import (
    calcular_alternativas,
    coordenadas_da_rota,
    localizar_endereco,
    locais_apoio_proximos,
)
from src.supabase_db import listar_alertas_ativos_supabase, registrar_evento
from src.ui_relatos import formulario_relato


CLASSIFICACOES = {
    "verde": "Contexto mais favorável",
    "amarelo": "Contexto intermediário",
    "vermelho": "Contexto menos favorável",
}


def _consultar_alertas():
    if config.MODO_DADOS == "demo":
        return pd.DataFrame(), False
    try:
        alertas = listar_alertas_ativos_supabase()
    except Exception:
        return pd.DataFrame(), False

    if alertas.empty:
        return alertas, True

    lat = pd.to_numeric(alertas["lat"], errors="coerce")
    lon = pd.to_numeric(alertas["lon"], errors="coerce")
    sul, norte, oeste, leste = config.BBOX_VM
    dentro = lat.between(sul, norte) & lon.between(oeste, leste)
    return alertas.loc[dentro & alertas["simulado"].eq(False)].copy(), True


@st.cache_data(show_spinner=False)
def _catalogo_local(arquivo, versao):
    locais = pd.read_csv(arquivo, usecols=["nome", "tipo", "lat", "lon"])
    sul, norte, oeste, leste = config.BBOX_VM
    locais = locais[
        locais["lat"].between(sul, norte) & locais["lon"].between(oeste, leste)
    ].dropna(subset=["nome"])
    catalogo = {}
    repetidos = set()
    for local in locais.itertuples(index=False):
        nome = str(local.nome).strip()
        if not nome or nome.casefold() in {"metro", "metrô"}:
            continue
        if local.tipo == "metro" and not nome.casefold().startswith("estação "):
            nome = f"Estação {nome}"
        if nome in catalogo:
            repetidos.add(nome)
        catalogo[nome] = (local.lat, local.lon)
    return {nome: catalogo[nome] for nome in sorted(catalogo) if nome not in repetidos}


def _resolver_endereco(endereco, catalogo):
    coordenadas = catalogo.get(endereco)
    return coordenadas if coordenadas is not None else localizar_endereco(endereco)


def _buscar(origem, destino, catalogo):
    for chave in ("alternativas_rotas", "rota", "rota_selecionada", "alertas_rota",
                  "alertas_disponiveis", "relatar", "ponto_relato", "relato_enviado"):
        st.session_state.pop(chave, None)
    if not origem or not destino or not origem.strip() or not destino.strip():
        st.warning("Preencha origem e destino.")
        return

    try:
        lat_origem, lon_origem = _resolver_endereco(origem, catalogo)
        lat_destino, lon_destino = _resolver_endereco(destino, catalogo)
        alertas, disponiveis = _consultar_alertas()
        alertas_score = alertas.loc[alertas["afeta_score"].eq(True)] if not alertas.empty else alertas
        alternativas = calcular_alternativas(
            lat_origem, lon_origem, lat_destino, lon_destino, alertas_ativos=alertas_score,
        )
        for alternativa in alternativas:
            nos = alternativa["nos"]
            alternativa.update(
                coordenadas=coordenadas_da_rota(nos),
                origem=[lon_origem, lat_origem],
                destino=[lon_destino, lat_destino],
                locais_apoio=locais_apoio_proximos(nos),
            )
    except ValueError as erro:
        st.error(str(erro))
        return

    st.session_state.update(
        alternativas_rotas=alternativas,
        alertas_rota=alertas,
        alertas_disponiveis=disponiveis,
        sequencia_mapa=st.session_state.get("sequencia_mapa", 0) + 1,
    )
    if disponiveis:
        try:
            registrar_evento("busca_trajeto")
        except Exception:
            pass  # Métricas de uso são auxiliares à busca.


@st.cache_data(show_spinner=False)
def _ler_categorias_ocorrencias(arquivo, versao):
    return pd.read_csv(arquivo, usecols=["trecho_id", "categoria", "total"])


def _categorias_da_rota(rota):
    arquivo = config.PASTA_TRATADOS / "ocorrencias_por_categoria.csv"
    if config.ARQUIVO_SCORE != config.ARQUIVO_SCORE_REAL or not arquivo.is_file():
        return None

    trechos = set()
    for edge_id in rota["edge_ids"]:
        origem, destino, chave = edge_id.split("_")
        primeiro, segundo = sorted((origem, destino))
        trechos.add(f"{primeiro}_{segundo}_{chave}")

    tabela = _ler_categorias_ocorrencias(arquivo, arquivo.stat().st_mtime_ns)
    return (
        tabela.loc[tabela["trecho_id"].isin(trechos)]
        .groupby("categoria")["total"]
        .sum()
        .sort_values(ascending=False)
    )


def _cartao_rota(numero, alternativa, selecionada):
    distancia = alternativa["distancia_metros"]
    medida = f"{distancia} m" if distancia < 1000 else f"{distancia / 1000:.2f} km"
    tempo = f"{alternativa['tempo_minutos']:g}".replace(".", ",")
    nota = alternativa["score_contexto"]
    nota_texto = f"{nota:.1f}".replace(".", ",")
    faixa = classificar_contexto(nota)
    avaliacao = alternativa["avaliacao"]
    categorias = _categorias_da_rota(alternativa)
    total = int(categorias.sum()) if categorias is not None else avaliacao["n_ocorrencias"]
    apoio = len(alternativa["locais_apoio"])
    titulo = f"Opção {numero} · {alternativa['nome']}"
    estado = " selecionado" if selecionada else ""
    texto_botao = f"{titulo} · selecionada" if selecionada else f"Selecionar {titulo}"

    with st.container(key=f"cartao_rota_{numero}"):
        st.html(
            f'<article class="poronde-rota{estado}">'
            f'<div class="poronde-rota-topo"><strong>{escape(titulo)}</strong>'
            f'<span class="poronde-nota {faixa}" title="{CLASSIFICACOES[faixa]}">'
            f'{nota_texto}/100</span></div>'
            '<div class="poronde-rota-metricas">'
            f'<span>{tempo} min · {medida.replace(".", ",")}</span>'
            f'<span>{avaliacao["n_trechos_com_luz"]} trechos com luz</span>'
            f'<span>Ocorrências: {total}</span>'
            f'<span>Locais de apoio: {apoio}</span>'
            '</div></article>'
        )
        st.button(
            texto_botao, key=f"escolher_rota_{numero}",
            on_click=_selecionar_rota, args=(numero - 1,), width="stretch",
        )


def _selecionar_rota(indice):
    st.session_state["rota_selecionada"] = indice
    _alterar_rota()


def _legenda(alternativas, selecionada):
    with st.expander("Legenda do mapa"):
        if alternativas:
            for i in range(len(alternativas)):
                cor, tracejado = ESTILOS_ROTAS[i]
                estilo = ("solid", "dashed", "dotted")[i] if tracejado else "solid"
                estado = " · selecionada" if i == selecionada else ""
                st.html(
                    '<div style="display:flex;align-items:center;gap:10px;margin:4px 0">'
                    f'<span aria-hidden="true" style="width:28px;border-top:4px {estilo} {cor}"></span>'
                    f'<span>Opção {i + 1}{estado}</span></div>'
                )
            st.caption("A linha mais forte indica a rota selecionada. O pontilhado escuro marca o trecho que merece atenção.")
        for _, cor, nome in GRUPOS_APOIO.values():
            st.html(
                '<div style="display:flex;align-items:center;gap:10px;margin:4px 0">'
                f'<span aria-hidden="true" style="width:10px;height:10px;border-radius:50%;background:{cor}"></span>'
                f'<span>{nome}</span></div>'
            )
        st.caption("Marcadores com ! em roxo-escuro indicam alertas comunitários públicos. Os ícones de início e fim marcam origem e destino.")


def _explicar(rota, alertas, alertas_disponiveis):
    avaliacao = rota["avaliacao"]
    classe = CLASSIFICACOES[classificar_contexto(rota["score_contexto"])]
    with st.expander("Por que esta pontuação?"):
        nota = f"{rota['score_contexto']:.1f}".replace(".", ",")
        st.write(f"**{nota}/100 · {classe}**")
        st.caption(
            f"Faixas do piloto: verde a partir de {config.LIMITE_VERDE}, "
            f"amarela de {config.LIMITE_AMARELO} até abaixo de {config.LIMITE_VERDE}, "
            f"e vermelha abaixo de {config.LIMITE_AMARELO}. "
            "A nota resume as condições registradas para a rota e as penalidades "
            "por alertas ativos considerados no cálculo."
        )
        st.write(rota["justificativa"])
        st.write(f"Trechos com iluminação cadastrada: {avaliacao['n_trechos_com_luz']}")
        st.write(f"Trechos em áreas de concentração de ocorrências: {avaliacao['n_trechos_em_hotspot']}")
        if avaliacao["n_trechos_com_abrigos"] is not None:
            st.write(f"Trechos com locais de apoio próximos: {avaliacao['n_trechos_com_abrigos']}")
        if alertas_disponiveis:
            st.write(f"Alertas ativos considerados no cálculo: {avaliacao['n_alertas_na_rota']}")
        else:
            st.caption("Pontuação calculada sem alertas da comunidade.")

    categorias = _categorias_da_rota(rota)
    total = int(categorias.sum()) if categorias is not None else avaliacao["n_ocorrencias"]
    with st.expander(f"Ocorrências registradas · {total}"):
        st.write(f"{total} registros associados aos trechos desta rota.")
        if config.ARQUIVO_SCORE == config.ARQUIVO_SCORE_REAL:
            st.caption("Fonte: SSP-SP · Recorte do piloto: 02/07 a 30/09/2026.")
        else:
            st.caption("Dados de exemplo.")
        if categorias is None:
            st.caption("A categoria de cada ocorrência não está disponível.")
        else:
            for categoria, quantidade in categorias.items():
                st.write(f"{categoria} · {quantidade}")
            st.caption(
                "O detalhamento conta os dois sentidos como um trecho de rua. "
                "Um boletim com mais de uma categoria aparece uma vez, com as categorias juntas."
            )

    locais = rota["locais_apoio"]
    with st.expander(f"Locais de apoio no mapa · {len(locais)}"):
        for local in locais:
            st.text(
                f"{local['nome']} · {nome_tipo_apoio(local['tipo'])} · "
                f"aprox. {local['distancia_metros']} m da rota"
            )
        if not locais:
            st.caption("Nenhum local de apoio cadastrado encontrado próximo à rota.")

    with st.expander("Alertas da comunidade no mapa"):
        if not alertas_disponiveis:
            st.caption("A consulta de alertas está indisponível.")
        else:
            grupos_publicos = [
                grupo for grupo in agrupar_alertas(alertas) if grupo["quantidade"] >= 2
            ]
            for grupo in grupos_publicos:
                st.text(f"{grupo['categoria']} · {grupo['quantidade']} relatos agrupados")
            if not grupos_publicos:
                st.caption("Nenhum alerta público agrupado para exibir no mapa.")


def _alterar_rota():
    st.session_state["relatar"] = False
    st.session_state.pop("ponto_relato", None)


def _abrir_relato():
    st.session_state["relatar"] = True
    st.session_state.pop("ponto_relato", None)
    st.session_state["sequencia_mapa"] += 1


def _ler_ponto_clique(mapa):
    clique = mapa.get("last_clicked")
    if not clique:
        return st.session_state.get("ponto_relato")
    lat, lon = clique["lat"], clique["lng"]
    sul, norte, oeste, leste = config.BBOX_VM
    if not (math.isfinite(lat) and math.isfinite(lon) and sul <= lat <= norte and oeste <= lon <= leste):
        st.session_state.pop("ponto_relato", None)
        st.warning("Marque um ponto dentro da área atendida.")
        return None
    if clique != st.session_state.get("ponto_relato"):
        st.session_state["ponto_relato"] = clique
        st.rerun()
    return clique


@st.fragment
def aba_rotas():
    st.html(
        """
        <style>
          .st-key-busca_trajeto [data-testid="stForm"] {
            border: 0;
            padding: 0;
          }
          .st-key-opcoes_trajeto [class*="st-key-cartao_rota_"] {
            position: relative;
          }
          .poronde-rota {
            padding: .85rem 1rem;
            border: 1px solid #d8d7d4;
            border-radius: .75rem;
          }
          .poronde-rota.selecionado {
            border-color: #242b26;
            background: #eff0ed;
          }
          .poronde-rota-topo {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: .5rem;
          }
          .poronde-rota-topo strong { font-size: .95rem; font-weight: 600; }
          .poronde-nota {
            white-space: nowrap;
            font-size: .75rem;
            border: 1px solid currentColor;
            border-radius: 99px;
            padding: 0 .45rem;
          }
          .poronde-nota.verde { color: #17643b; background: #e7f3eb; }
          .poronde-nota.amarelo { color: #705000; background: #fff2cb; }
          .poronde-nota.vermelho { color: #932920; background: #fbeae7; }
          .poronde-rota-metricas {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .3rem .65rem;
            margin-top: .65rem;
            color: #515953;
            font-size: .8rem;
          }
          .st-key-opcoes_trajeto [class*="st-key-cartao_rota_"] [data-testid="stElementContainer"]:has([data-testid="stButton"]) {
            position: absolute;
            inset: 0;
            z-index: 1;
          }
          .st-key-opcoes_trajeto [class*="st-key-cartao_rota_"] [data-testid="stButton"],
          .st-key-opcoes_trajeto [class*="st-key-cartao_rota_"] button { height: 100%; }
          .st-key-opcoes_trajeto [class*="st-key-cartao_rota_"] button {
            opacity: 0;
            border-radius: .75rem;
          }
          .st-key-opcoes_trajeto [class*="st-key-cartao_rota_"]:has(button:hover) article {
            border-color: #242b26;
          }
          .st-key-opcoes_trajeto [class*="st-key-cartao_rota_"]:has(button:focus-visible) article {
            outline: 2px solid #197144;
            outline-offset: 2px;
          }
          .st-key-mapa_trajeto iframe {
            border: 1px solid #d8d7d4;
            border-radius: .75rem;
          }
          .st-key-acao_relato button {
            background: #fbd530;
            color: #17191e;
            border: 1px solid #17191e;
          }
        </style>
        """
    )
    st.title("Trajeto", anchor=False)
    if config.ARQUIVO_SCORE == config.ARQUIVO_SCORE_EXEMPLO:
        st.warning("A pontuação está usando dados de exemplo.")

    arquivo_apoio = config.ARQUIVO_ABRIGOS
    catalogo = (
        _catalogo_local(arquivo_apoio, arquivo_apoio.stat().st_mtime_ns)
        if arquivo_apoio.is_file() else {}
    )
    with st.container(key="busca_trajeto"):
        with st.form("form_rota"):
            campo_origem, campo_destino, acao = st.columns(
                [3, 3, 1.1], vertical_alignment="bottom"
            )
            origem = campo_origem.selectbox(
                "Origem", list(catalogo), index=None, accept_new_options=True,
                placeholder="Ex.: Estação Vila Mariana", key="origem_trajeto",
            )
            destino = campo_destino.selectbox(
                "Destino", list(catalogo), index=None, accept_new_options=True,
                placeholder="Ex.: Rua Gandavo, 550", key="destino_trajeto",
            )
            calcular = acao.form_submit_button("Comparar", type="primary", width="stretch")
        st.caption("Escolha uma sugestão ou digite o endereço completo e confirme com Enter.")
        if calcular:
            with st.spinner("Calculando trajetos…"):
                _buscar(origem, destino, catalogo)

    alternativas = st.session_state.get("alternativas_rotas", [])
    alertas = st.session_state.get("alertas_rota", pd.DataFrame())
    alertas_disponiveis = st.session_state.get("alertas_disponiveis", False)

    mapa_coluna, painel = st.columns([1.3, 1], gap="medium")
    rota = None
    selecionada = None
    with painel:
        if alternativas:
            selecionada = min(st.session_state.get("rota_selecionada", 0), len(alternativas) - 1)
            with st.container(key="opcoes_trajeto"):
                for indice, alternativa in enumerate(alternativas):
                    _cartao_rota(indice + 1, alternativa, indice == selecionada)
            if len(alternativas) < 3:
                st.caption(
                    f"A malha de ruas retornou {len(alternativas)} "
                    f"{'caminho distinto' if len(alternativas) == 1 else 'caminhos distintos'} "
                    "para este par de endereços."
                )
            rota = alternativas[selecionada]
            st.session_state["rota"] = rota
            _explicar(rota, alertas, alertas_disponiveis)
            if st.session_state.pop("relato_enviado", False):
                st.success("Relato enviado para avaliação.")
            if config.MODO_DADOS == "demo":
                st.caption("Envio de relatos indisponível no modo demonstração.")
            elif not st.session_state.get("relatar"):
                with st.container(key="acao_relato"):
                    st.caption("Encontrou algum problema no caminho?")
                    st.button("Deixar um relato", on_click=_abrir_relato)
        else:
            st.caption("Informe origem e destino para comparar os trajetos.")
        formulario = st.container()

    modo_relato = rota is not None and st.session_state.get("relatar", False)
    with mapa_coluna:
        retorno = None
        with st.container(key="mapa_trajeto"):
            if rota:
                mapa = criar_mapa(
                    rota, alternativas, alertas=alertas,
                    ponto_relato=st.session_state.get("ponto_relato") if modo_relato else None,
                )
                if modo_relato:
                    st.caption("Clique no mapa para marcar o local.")
                retorno = st_folium(
                    mapa, height=510, use_container_width=True,
                    key=f"trajeto-{st.session_state.get('sequencia_mapa', 0)}-{selecionada}",
                    returned_objects=["last_clicked"] if modo_relato else [],
                )
            else:
                st.info("O mapa aparece após a comparação dos trajetos.")
        ponto = _ler_ponto_clique(retorno or {}) if modo_relato else None
        legenda, atalho = st.columns([2, 1])
        with legenda:
            _legenda(alternativas, selecionada)
        with atalho.popover("Emergência", use_container_width=True):
            st.markdown(
                "[Polícia Militar · 190](tel:190)  \n"
                "[SAMU · 192](tel:192)  \n"
                "[Bombeiros · 193](tel:193)"
            )

    if modo_relato:
        with formulario:
            st.button("Cancelar relato", on_click=_alterar_rota)
            formulario_relato(ponto)
