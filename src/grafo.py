"""Malha de ruas da Vila Mariana (contrato 1)."""

import os

import geopandas as gpd
import osmnx as ox

from src import config


def baixar_e_salvar_grafo():
    """Baixa o limite e a rede de pedestres do OpenStreetMap e salva em disco."""
    # 1. Contorno do bairro
    limite = ox.geocode_to_gdf(config.NOME_LUGAR)
    if limite.geom_type.iloc[0] not in ("Polygon", "MultiPolygon"):
        raise ValueError("O OSM não devolveu um polígono. Use o plano B (geojson.io).")

    # 2. Rede de ruas para pedestres dentro do polígono
    grafo = ox.graph_from_polygon(limite.geometry.iloc[0], network_type="walk")

    # 3. Mantém só a maior parte conectada (evita ruas ilhadas)
    grafo = ox.truncate.largest_component(grafo, strongly=True)

    # 4. Salva os dois arquivos
    os.makedirs(os.path.dirname(config.CAMINHO_GRAFO), exist_ok=True)
    ox.save_graphml(grafo, config.CAMINHO_GRAFO)
    limite.to_file(config.CAMINHO_LIMITE, driver="GeoJSON")

    # 5. Resumo para conferência
    arestas = ox.convert.graph_to_gdfs(grafo, nodes=False)
    print("Nós:", len(grafo.nodes))
    print("Trechos:", len(grafo.edges))
    print("Extensão total (km):", round(arestas["length"].sum() / 1000, 1))


def carregar_grafo():
    """Devolve o grafo de ruas lido do .graphml."""
    return ox.load_graphml(config.CAMINHO_GRAFO)


def carregar_limite():
    """Devolve o limite da Vila Mariana como GeoDataFrame."""
    return gpd.read_file(config.CAMINHO_LIMITE)
