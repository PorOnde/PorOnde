
import folium
from src.rotas import coordenadas_do_pior_trecho
from src.config import MODO_DADOS, RAIO_ATIVACAO_METROS
from src.relatos import (
    _distancia_em_metros,
    listar_alertas_ativos,
)


CORES_ROTAS = {
    "Mais curta": "#C64411",
    "Melhor iluminação": "#27834A",
    "Melhor contexto": "#2563A6",
}


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

        grupo["lat"] = sum(
            ponto["lat"] for ponto in pontos
        ) / len(pontos)

        grupo["lon"] = sum(
            ponto["lon"] for ponto in pontos
        ) / len(pontos)

        grupo["quantidade"] = len(pontos)
        grupo["simulado"] = all(
            ponto["simulado"] for ponto in pontos
        )

    return grupos



def criar_mapa(rota, alternativas=None):
    """Cria o mapa Folium com até três rotas alternativas."""

    origem = rota["origem"]
    destino = rota["destino"]

    mapa = folium.Map(
        location=[
            (origem[1] + destino[1]) / 2,
            (origem[0] + destino[0]) / 2,
        ],
        zoom_start=14,
        tiles="OpenStreetMap",
    )

    rotas = alternativas if alternativas is not None else [rota]

    for alternativa in rotas:
        coordenadas = [
            [latitude, longitude]
            for longitude, latitude in alternativa["coordenadas"]
        ]

        folium.PolyLine(
            locations=coordenadas,
            color=CORES_ROTAS.get(alternativa["nome"], "#C64411"),
            weight=6 if alternativa is rota else 4,
            opacity=1 if alternativa is rota else 0.6,
            tooltip=alternativa["nome"],
        ).add_to(mapa)
        
    pior_trecho = rota.get("pior_trecho")

    if pior_trecho is not None:
        coordenadas_pior_trecho = coordenadas_do_pior_trecho(
            pior_trecho
        )

        folium.PolyLine(
            locations=coordenadas_pior_trecho,
            color="#D00000",
            weight=10,
            opacity=1,
            tooltip=(
                "Trecho com menor score de contexto: "
                f"{pior_trecho['score']:.1f}/100 "
                "(dados de demonstração)"
            ),
        ).add_to(mapa)


    folium.Marker(
        location=[origem[1], origem[0]],
        tooltip="Origem",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(mapa)

    folium.Marker(
        location=[destino[1], destino[0]],
        tooltip="Destino",
        icon=folium.Icon(color="red", icon="stop"),
    ).add_to(mapa)

    cores_grupos = {
        "abrigo_amigo": "blue",
        "saude": "red",
        "seguranca": "orange",
        "transporte_24h": "purple",
        "outro": "gray",
    }

    for local in rota["locais_apoio"]:
        folium.Marker(
            location=[local["lat"], local["lon"]],
            tooltip=f"{local['nome']} ({local['tipo']})",
            icon=folium.Icon(
                color=cores_grupos.get(local["grupo"], "gray"),
                icon="info-sign",
            ),
        ).add_to(mapa)
    nome_camada = (
    "Alertas da comunidade (demonstração)"
    if MODO_DADOS == "demo"
    else "Alertas da comunidade"
)

    camada_alertas = folium.FeatureGroup(
    name=nome_camada,
    show=True,
)
    
    alertas = listar_alertas_ativos()
    grupos_alertas = agrupar_alertas(alertas)

    for grupo in grupos_alertas:
        identificacao = (
            " — DEMONSTRAÇÃO"
            if grupo["simulado"]
            else ""
        )

        quantidade = grupo["quantidade"]

        folium.Marker(
            location=[grupo["lat"], grupo["lon"]],
            tooltip=(
                f"{grupo['categoria']}"
                f" — {quantidade} relato(s)"
                f"{identificacao}"
            ),
            popup=folium.Popup(
                f"Categoria: {grupo['categoria']}"
                f"<br>Relatos agrupados: {quantidade}"
                f"<br>{'Dados simulados' if grupo['simulado'] else 'Dados registrados'}",
                max_width=300,
            ),
            icon=folium.Icon(
                color="orange",
                icon="exclamation-sign",
            ),
        ).add_to(camada_alertas)


    camada_alertas.add_to(mapa)
    folium.LayerControl().add_to(mapa)

    return mapa
