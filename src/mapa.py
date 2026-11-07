
import folium
from src.rotas import coordenadas_do_pior_trecho


CORES_ROTAS = {
    "Mais curta": "#C64411",
    "Melhor iluminação": "#27834A",
    "Melhor contexto": "#2563A6",
}


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
         coordenadas = coordenadas_do_pior_trecho(pior_trecho)

        folium.PolyLine(
            locations=coordenadas,
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

    folium.LayerControl().add_to(mapa)

    return mapa
