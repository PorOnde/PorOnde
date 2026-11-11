from pathlib import Path

import geopandas as gpd
import pandas as pd
import re
import unicodedata


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

def padronizar_colunas(tabela):
    nomes = []

    for coluna in tabela.columns:
        nome = unicodedata.normalize("NFKD", str(coluna))
        nome = nome.encode("ascii", "ignore").decode("ascii")
        nome = re.sub(r"[^a-z0-9]+", "_", nome.lower()).strip("_")
        nomes.append(nome)

    if any(not nome for nome in nomes):
        raise ValueError("Há coluna sem nome após a padronização.")

    if len(nomes) != len(set(nomes)):
        raise ValueError("Há nomes de colunas repetidos após a padronização.")

    resultado = tabela.copy()
    resultado.columns = nomes
    return resultado


def limpar_amostra_ssp(tabela, retangulo):
    sul, norte, oeste, leste = retangulo
    dados = padronizar_colunas(tabela)

    dados["data_ocorrencia_bo"] = pd.to_datetime(
        dados["data_ocorrencia_bo"], dayfirst=True, errors="coerce"
    )

    for coluna in ["latitude", "longitude"]:
        texto = dados[coluna].astype("string").str.strip()
        texto = texto.str.replace(",", ".", regex=False)
        dados[coluna] = pd.to_numeric(texto, errors="coerce")

    funil = {"Linhas lidas": len(dados)}

    # Cada filtro conta apenas as linhas que chegaram até ele.
    filtros = [
        ("Sem data válida", dados["data_ocorrencia_bo"].notna()),
        ("Sem coordenadas", dados[["latitude", "longitude"]].notna().all(axis=1)),
        ("Coordenada igual a zero", dados["latitude"].ne(0) & dados["longitude"].ne(0)),
        ("Fora do retângulo", dados["latitude"].between(sul, norte)
         & dados["longitude"].between(oeste, leste)),
    ]

    for etapa, manter in filtros:
        quantidade_antes = len(dados)
        dados = dados.loc[manter.reindex(dados.index).fillna(False)]
        funil[etapa] = quantidade_antes - len(dados)

    # Compara todas as colunas originais antes de remover cópias idênticas.
    repetidas = tabela.loc[dados.index].duplicated(keep="first")
    funil["Linhas integralmente repetidas"] = int(repetidas.sum())
    dados = dados.loc[~repetidas]

    funil["Linhas finais"] = len(dados)
    return dados, funil