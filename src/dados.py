from pathlib import Path

import geopandas as gpd
import pandas as pd


def ler_ssp(caminho, aba, colunas=None, n_linhas=None):
    caminho = Path(caminho)

    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    return pd.read_excel(
        caminho,
        sheet_name=aba,
        usecols=colunas,
        nrows=n_linhas,
        engine="openpyxl"
    )


def ler_iluminacao(caminho, n_linhas=None):
    caminho = Path(caminho)

    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    return gpd.read_file(
        caminho,
        layer="SIRGAS_GPKG_iluminacaopublica",
        rows=n_linhas
    )