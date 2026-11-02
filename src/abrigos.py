import pandas as pd
import osmnx as ox

from src.config import ARQUIVO_ABRIGOS, ARQUIVO_LOCAIS_MANUAIS
from src.grafo import carregar_limite


COLUNAS_ABRIGOS = [
    "nome",
    "tipo",
    "lat",
    "lon",
    "horario",
    "fonte",
    "grupo",
]


def _texto(valor):
    if pd.isna(valor):
        return ""

    return str(valor).strip()


def _classificar_local(local):
    amenity = _texto(local.get("amenity"))
    shop = _texto(local.get("shop"))
    railway = _texto(local.get("railway"))

    if amenity == "pharmacy":
        return "farmacia", "abrigo_amigo"

    if shop == "supermarket":
        return "mercado", "abrigo_amigo"

    if shop == "convenience":
        return "loja", "abrigo_amigo"

    if amenity == "police":
        return "delegacia", "seguranca"

    if amenity == "hospital":
        return "hospital", "saude"

    if amenity == "clinic":
        return "clinica", "saude"

    if amenity == "fuel":
        return "posto", "transporte_24h"

    if railway in ("station", "subway_entrance"):
        return "metro", "transporte_24h"

    return None, None


def _ler_locais_manuais():
    ARQUIVO_LOCAIS_MANUAIS.parent.mkdir(parents=True, exist_ok=True)

    if not ARQUIVO_LOCAIS_MANUAIS.exists():
        pd.DataFrame(columns=COLUNAS_ABRIGOS).to_csv(
            ARQUIVO_LOCAIS_MANUAIS,
            index=False,
        )

    locais = pd.read_csv(ARQUIVO_LOCAIS_MANUAIS)

    for coluna in COLUNAS_ABRIGOS:
        if coluna not in locais.columns:
            locais[coluna] = ""

    locais["fonte"] = locais["fonte"].fillna("Cadastro manual")
    locais["grupo"] = locais["grupo"].fillna("outro")

    return locais[COLUNAS_ABRIGOS]


def gerar_abrigos():
    limite = carregar_limite()
    poligono = limite.geometry.unary_union

    etiquetas = {
        "amenity": ["pharmacy", "police", "hospital", "clinic", "fuel"],
        "shop": ["supermarket", "convenience"],
        "railway": ["station", "subway_entrance"],
    }

    locais_osm = ox.features_from_polygon(poligono, etiquetas)
    abrigos = []

    for _, local in locais_osm.iterrows():
        tipo, grupo = _classificar_local(local)

        if tipo is None:
            continue

        geometria = local.geometry

        if geometria is None or geometria.is_empty:
            continue

        if geometria.geom_type == "Point":
            ponto = geometria
        else:
            ponto = geometria.representative_point()

        nome = _texto(local.get("name"))

        if not nome:
            nome = tipo.replace("_", " ").title()

        horario = _texto(local.get("opening_hours"))

        if not horario:
            horario = "Horário não informado no OpenStreetMap"

        abrigos.append(
            {
                "nome": nome,
                "tipo": tipo,
                "lat": ponto.y,
                "lon": ponto.x,
                "horario": horario,
                "fonte": "OpenStreetMap",
                "grupo": grupo,
            }
        )

    abrigos_osm = pd.DataFrame(abrigos, columns=COLUNAS_ABRIGOS)
    locais_manuais = _ler_locais_manuais()

    resultado = pd.concat(
        [abrigos_osm, locais_manuais],
        ignore_index=True,
    )

    resultado = resultado.drop_duplicates(
        subset=["nome", "lat", "lon"],
        keep="first",
    )

    resultado = resultado.sort_values(
        by=["grupo", "tipo", "nome"],
    ).reset_index(drop=True)

    ARQUIVO_ABRIGOS.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(ARQUIVO_ABRIGOS, index=False)

    return resultado


def listar_abrigos():
    if not ARQUIVO_ABRIGOS.exists():
        return pd.DataFrame(columns=COLUNAS_ABRIGOS)

    abrigos = pd.read_csv(ARQUIVO_ABRIGOS)

    return abrigos.reindex(columns=COLUNAS_ABRIGOS)