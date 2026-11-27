from html import escape

import folium
from folium.plugins import PolyLineOffset

from src.config import (
    LIMITE_AMARELO,
    LIMITE_VERDE,
    MODO_DADOS,
    RAIO_ATIVACAO_METROS,
)
from src.relatos import _distancia_em_metros
from src.rotas import coordenadas_do_pior_trecho
from src.supabase_db import listar_alertas_ativos_supabase


ESTILOS_ROTAS = (
    ("#008746", None),
    ("#a87500", "11 7"),
    ("#cf3026", "2 7"),
)

GRUPOS_APOIO = {
    "abrigo_amigo": ("blue", "#2b81cb", "Comércios e farmácias"),
    "saude": ("red", "#cb2b3e", "Serviços de saúde"),
    "seguranca": ("orange", "#cb8427", "Segurança pública"),
    "transporte_24h": ("purple", "#682acb", "Transporte e postos"),
    "outro": ("gray", "#575757", "Outros locais de apoio"),
}

TIPOS_APOIO = {
    "farmacia": "Farmácia",
    "mercado": "Mercado",
    "loja": "Loja de conveniência",
    "delegacia": "Delegacia",
    "hospital": "Hospital",
    "clinica": "Clínica",
    "posto": "Posto de combustível",
    "metro": "Metrô",
}


def nome_tipo_apoio(tipo):
    return TIPOS_APOIO.get(tipo, str(tipo).replace("_", " ").capitalize())


def classificar_contexto(score):
    """Classifica a pontuação de contexto de uma rota."""
    if score >= LIMITE_VERDE:
        return "verde"

    if score >= LIMITE_AMARELO:
        return "amarelo"

    return "vermelho"


def agrupar_alertas(alertas):
    """Agrupa visualmente alertas próximos da mesma categoria."""
    grupos = []

    for _, alerta in alertas.iterrows():
        latitude = float(alerta["lat"])
        longitude = float(alerta["lon"])
        categoria = alerta["categoria"]

        grupo_encontrado = None

        for grupo in grupos:
            if grupo["categoria"] != categoria:
                continue

            distancias = [
                _distancia_em_metros(
                    latitude,
                    longitude,
                    ponto["lat"],
                    ponto["lon"],
                )
                for ponto in grupo["pontos"]
            ]

            if all(
                distancia <= RAIO_ATIVACAO_METROS
                for distancia in distancias
            ):
                grupo_encontrado = grupo
                break

        ponto = {
            "lat": latitude,
            "lon": longitude,
            "simulado": bool(alerta["simulado"]),
        }

        if grupo_encontrado is None:
            grupos.append({
                "categoria": categoria,
                "pontos": [ponto],
            })
        else:
            grupo_encontrado["pontos"].append(ponto)

    for grupo in grupos:
        pontos = grupo["pontos"]

        grupo["lat"] = sum(ponto["lat"] for ponto in pontos) / len(pontos)
        grupo["lon"] = sum(ponto["lon"] for ponto in pontos) / len(pontos)
        grupo["quantidade"] = len(pontos)
        grupo["simulado"] = all(
            ponto["simulado"] for ponto in pontos
        )

    return grupos


def criar_mapa_base(latitude, longitude):
    mapa = folium.Map(
        location=[latitude, longitude], zoom_start=14, tiles="OpenStreetMap"
    )
    mapa.get_root().header.add_child(folium.Element(
        "<style>.leaflet-tile-pane { filter: saturate(.35) brightness(1.035); }</style>"
    ))
    return mapa


def criar_mapa(rota, alternativas=None, *, alertas=None, ponto_relato=None):
    """Desenha as alternativas e destaca a rota selecionada."""
    origem = rota["origem"]
    destino = rota["destino"]
    mapa = criar_mapa_base(
        (origem[1] + destino[1]) / 2, (origem[0] + destino[0]) / 2
    )

    rotas = alternativas if alternativas is not None else [rota]

    rotas_numeradas = list(enumerate(rotas, start=1))
    # A rota selecionada fica por cima dos caminhos com trechos em comum.
    rotas_numeradas.sort(key=lambda item: item[1] is rota)

    for numero, alternativa in rotas_numeradas:
        selecionada = alternativa is rota
        cor, tracejado = ESTILOS_ROTAS[(numero - 1) % len(ESTILOS_ROTAS)]
        PolyLineOffset(
            locations=[[lat, lon] for lon, lat in alternativa["coordenadas"]],
            offset=(numero - (len(rotas) + 1) / 2) * 7,
            color=cor,
            dash_array=tracejado,
            weight=7 if selecionada else 4,
            opacity=1 if selecionada else 0.55,
            tooltip=f"Opção {numero} · {escape(alternativa['nome'])}",
        ).add_to(mapa)

    pior_trecho = rota.get("pior_trecho")

    if pior_trecho is not None:
        coordenadas_pior_trecho = coordenadas_do_pior_trecho(
            pior_trecho
        )

        popup_pior_trecho = (
            "<b>Trecho que merece atenção</b><br>"
            f"Score: {pior_trecho['score']:.1f}/100<br><br>"
            f"Iluminação cadastrada: {pior_trecho['n_luz']} pontos<br>"
            "Fonte: GeoSampa<br><br>"
            f"Ocorrências associadas: {pior_trecho['n_ocorrencias']}<br>"
            "Fonte: SSP-SP<br><br>"
            f"Locais de apoio próximos: {pior_trecho['n_abrigos']}<br>"
            "Fonte: cadastro de locais úteis do PorOnde?<br><br>"
            "Em área de concentração de registros: "
            f"{'Sim' if pior_trecho['em_hotspot'] else 'Não'}<br><br>"
            "Período das ocorrências: 02/07 a 30/09/2026, na base do piloto."
        )

        folium.PolyLine(
            locations=coordenadas_pior_trecho,
            color="#242b26",
            dash_array="2 6",
            weight=4,
            opacity=1,
            tooltip="Clique para ver os indicadores deste trecho",
            popup=folium.Popup(
                popup_pior_trecho,
                max_width=350,
            ),
        ).add_to(mapa)

    folium.Marker(
        location=[origem[1], origem[0]],
        tooltip="Origem",
        icon=folium.Icon(color="darkgreen", icon="play"),
    ).add_to(mapa)

    folium.Marker(
        location=[destino[1], destino[0]],
        tooltip="Destino",
        icon=folium.Icon(color="black", icon="stop"),
    ).add_to(mapa)

    camada_apoio = folium.FeatureGroup(name="Locais de apoio da rota selecionada")
    for local in rota["locais_apoio"]:
        nome = escape(str(local["nome"]))
        tipo = escape(nome_tipo_apoio(local["tipo"]))
        cor, _, categoria = GRUPOS_APOIO.get(local["grupo"], GRUPOS_APOIO["outro"])
        distancia = local["distancia_metros"]
        folium.Marker(
            location=[local["lat"], local["lon"]],
            tooltip=f"{nome} · {tipo}",
            popup=folium.Popup(
                f"<strong>{nome}</strong><br>{tipo} · {categoria}"
                f"<br>Aproximadamente {distancia} m da rota",
                max_width=300,
            ),
            icon=folium.Icon(color=cor, icon="info-sign"),
        ).add_to(camada_apoio)

    camada_apoio.add_to(mapa)

    nome_camada = (
        "Alertas da comunidade (demonstração)"
        if MODO_DADOS == "demo"
        else "Alertas da comunidade"
    )

    camada_alertas = folium.FeatureGroup(
        name=nome_camada,
        show=True,
    )

    if alertas is None:
        alertas = listar_alertas_ativos_supabase()
    grupos_alertas = agrupar_alertas(alertas)

    for grupo in grupos_alertas:
        if grupo["quantidade"] < 2:
            continue
        identificacao = (
            " — DEMONSTRAÇÃO"
            if grupo["simulado"]
            else ""
        )

        quantidade = grupo["quantidade"]

        folium.Marker(
            location=[grupo["lat"], grupo["lon"]],
            tooltip=(
                f"{escape(str(grupo['categoria']))}"
                f" — {quantidade} relato(s)"
                f"{identificacao}"
            ),
            popup=folium.Popup(
                f"Categoria: {escape(str(grupo['categoria']))}"
                f"<br>Relatos agrupados: {quantidade}"
                f"<br>{'Dados simulados' if grupo['simulado'] else 'Dados registrados'}",
                max_width=300,
            ),
            icon=folium.Icon(
                color="darkpurple",
                icon="exclamation-sign",
            ),
        ).add_to(camada_alertas)

    camada_alertas.add_to(mapa)
    if ponto_relato:
        folium.CircleMarker(
            location=[ponto_relato["lat"], ponto_relato["lng"]],
            radius=8, color="#173724", fill=True, fill_color="#fff",
            fill_opacity=1, tooltip="Local do relato",
        ).add_to(mapa)

    mapa.fit_bounds([
        [lat, lon]
        for alternativa in rotas
        for lon, lat in alternativa["coordenadas"]
    ] + [[origem[1], origem[0]], [destino[1], destino[0]]])
    folium.LayerControl(collapsed=True).add_to(mapa)

    return mapa
