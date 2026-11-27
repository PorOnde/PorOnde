import math
import random
from datetime import datetime, timedelta

import pandas as pd

from src.banco import conectar, criar_tabelas
from src.config import (
    CATEGORIAS_VALIDADE_HORAS,
    JANELA_ATIVACAO_HORAS,
    LIMITE_RELATOS_POR_HORA,
    MAX_CARACTERES_DESCRICAO,
    MODO_DADOS,
    RAIO_ATIVACAO_METROS,
    SALDO_MINIMO_REJEICAO,
)


COLUNAS_ALERTAS = [
    "id",
    "categoria",
    "descricao",
    "lat",
    "lon",
    "criado_em",
    "expira_em",
    "confirmacoes",
    "rejeicoes",
    "saldo",
    "simulado",
]


def _exigir_modo_demo():
    if MODO_DADOS != "demo":
        raise RuntimeError(
            "Relatos simulados só podem ser usados no modo demonstração."
        )


def _obter_bbox_vm():
    try:
        from src.config import BBOX_VM
    except ImportError as erro:
        raise RuntimeError(
            "BBOX_VM ainda não foi definido pela parte do grafo."
        ) from erro

    return BBOX_VM


def _ponto_no_bbox(sul, norte, oeste, leste, percentual_lat, percentual_lon):
    lat = sul + (norte - sul) * percentual_lat
    lon = oeste + (leste - oeste) * percentual_lon
    return lat, lon


def _ponto_proximo(lat, lon, metros_lat, metros_lon):
    novo_lat = lat + metros_lat / 111_320
    novo_lon = lon + metros_lon / (111_320 * math.cos(math.radians(lat)))
    return novo_lat, novo_lon


def limpar_simulados():
    _exigir_modo_demo()
    criar_tabelas()

    with conectar() as conexao:
        conexao.execute(
            """
            DELETE FROM votos
            WHERE id_relato IN (
                SELECT id
                FROM relatos
                WHERE simulado = 1
            )
            """
        )

        resultado = conexao.execute(
            "DELETE FROM relatos WHERE simulado = 1"
        )

    return resultado.rowcount


def gerar_relatos_simulados(semente=42):
    _exigir_modo_demo()
    criar_tabelas()

    sul, norte, oeste, leste = _obter_bbox_vm()
    gerador = random.Random(semente)
    agora = datetime.now()

    limpar_simulados()

    relatos = []

    grupos_ativos = [
        ("Rua mal iluminada ou escura", 0.20, 0.25),
        ("Via bloqueada ou obra", 0.50, 0.55),
        ("Aglomeração ou tumulto", 0.75, 0.35),
    ]

    for numero_grupo, (categoria, percentual_lat, percentual_lon) in enumerate(
        grupos_ativos, start=1
    ):
        lat_centro, lon_centro = _ponto_no_bbox(
            sul,
            norte,
            oeste,
            leste,
            percentual_lat,
            percentual_lon,
        )

        for numero_relato in range(1, 3):
            deslocamento_lat = gerador.uniform(-30, 30)
            deslocamento_lon = gerador.uniform(-30, 30)
            lat, lon = _ponto_proximo(
                lat_centro,
                lon_centro,
                deslocamento_lat,
                deslocamento_lon,
            )

            relatos.append(
                (
                    categoria,
                    f"Relato simulado do grupo ativo {numero_grupo}.",
                    lat,
                    lon,
                    agora.isoformat(timespec="seconds"),
                    (agora + timedelta(hours=12)).isoformat(timespec="seconds"),
                    "ativo",
                    0,
                    0,
                    f"demo_ativo_{numero_grupo}_{numero_relato}",
                    1,
                )
            )

    categorias_pendentes = [
        "Outro",
        "Transporte com problema (ônibus ou metrô)",
        "Rua mal iluminada ou escura",
        "Via bloqueada ou obra",
        "Aglomeração ou tumulto",
    ]

    for numero, categoria in enumerate(categorias_pendentes, start=1):
        lat, lon = _ponto_no_bbox(
            sul,
            norte,
            oeste,
            leste,
            0.12 + numero * 0.13,
            0.82,
        )

        relatos.append(
            (
                categoria,
                f"Relato simulado isolado {numero}.",
                lat,
                lon,
                agora.isoformat(timespec="seconds"),
                (agora + timedelta(hours=12)).isoformat(timespec="seconds"),
                "pendente",
                0,
                0,
                f"demo_pendente_{numero}",
                1,
            )
        )

    for numero in range(1, 3):
        lat, lon = _ponto_no_bbox(
            sul,
            norte,
            oeste,
            leste,
            0.25 + numero * 0.20,
            0.12,
        )

        relatos.append(
            (
                "Outro",
                f"Relato simulado rejeitado {numero}.",
                lat,
                lon,
                agora.isoformat(timespec="seconds"),
                (agora + timedelta(hours=12)).isoformat(timespec="seconds"),
                "rejeitado",
                0,
                1,
                f"demo_rejeitado_{numero}",
                1,
            )
        )

    for numero in range(1, 3):
        lat, lon = _ponto_no_bbox(
            sul,
            norte,
            oeste,
            leste,
            0.30 + numero * 0.22,
            0.90,
        )

        criado_em = agora - timedelta(hours=26)
        expira_em = agora - timedelta(hours=2)

        relatos.append(
            (
                "Rua mal iluminada ou escura",
                f"Relato simulado expirado {numero}.",
                lat,
                lon,
                criado_em.isoformat(timespec="seconds"),
                expira_em.isoformat(timespec="seconds"),
                "expirado",
                0,
                0,
                f"demo_expirado_{numero}",
                1,
            )
        )

    with conectar() as conexao:
        conexao.executemany(
            """
            INSERT INTO relatos (
                categoria, descricao, lat, lon, criado_em, expira_em,
                status, confirmacoes, rejeicoes, id_sessao, simulado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            relatos,
        )

    return len(relatos)


def listar_alertas_ativos():
    """Retorna somente os alertas que continuam ativos."""
    atualizar_status()

    with conectar() as conexao:
        alertas = pd.read_sql_query(
            """
            SELECT
                id,
                categoria,
                descricao,
                lat,
                lon,
                criado_em,
                expira_em,
                confirmacoes,
                rejeicoes,
                confirmacoes - rejeicoes AS saldo,
                simulado
            FROM relatos
            WHERE status = 'ativo'
            ORDER BY criado_em DESC, id DESC
            """,
            conexao,
        )

    return alertas.reindex(columns=COLUNAS_ALERTAS)

def registrar_relato(categoria, descricao, lat, lon, id_sessao):
    if categoria not in CATEGORIAS_VALIDADE_HORAS:
        return "Categoria inválida."

    if len(descricao) > MAX_CARACTERES_DESCRICAO:
        return (
            f"A descrição pode ter no máximo "
            f"{MAX_CARACTERES_DESCRICAO} caracteres."
        )

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return "Latitude e longitude precisam ser números."

    try:
        sul, norte, oeste, leste = _obter_bbox_vm()
    except RuntimeError as erro:
        return str(erro)

    if not (sul <= lat <= norte and oeste <= lon <= leste):
        return "O relato precisa estar dentro da Vila Mariana."

    agora = datetime.now()
    inicio_ultima_hora = agora - timedelta(hours=1)

    criar_tabelas()

    with conectar() as conexao:
        quantidade_na_ultima_hora = conexao.execute(
            """
            SELECT COUNT(*)
            FROM relatos
            WHERE id_sessao = ? AND criado_em >= ?
            """,
            (
                id_sessao,
                inicio_ultima_hora.isoformat(timespec="seconds"),
            ),
        ).fetchone()[0]

        if quantidade_na_ultima_hora >= LIMITE_RELATOS_POR_HORA:
            return (
                f"Cada sessão pode enviar até "
                f"{LIMITE_RELATOS_POR_HORA} relatos por hora."
            )

        expira_em = agora + timedelta(
            hours=CATEGORIAS_VALIDADE_HORAS[categoria]
        )

        resultado = conexao.execute(
            """
            INSERT INTO relatos (
                categoria, descricao, lat, lon, criado_em, expira_em,
                status, confirmacoes, rejeicoes, id_sessao, simulado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                categoria,
                descricao,
                lat,
                lon,
                agora.isoformat(timespec="seconds"),
                expira_em.isoformat(timespec="seconds"),
                "pendente",
                0,
                0,
                id_sessao,
                0,
            ),
        )

        id_relato = resultado.lastrowid

    atualizar_status()

    return id_relato

def _distancia_em_metros(lat1, lon1, lat2, lon2):
    raio_terra = 6_371_000

    diferenca_lat = math.radians(lat2 - lat1)
    diferenca_lon = math.radians(lon2 - lon1)

    calculo = (
        math.sin(diferenca_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(diferenca_lon / 2) ** 2
    )

    angulo = 2 * math.atan2(math.sqrt(calculo), math.sqrt(1 - calculo))

    return raio_terra * angulo
    
def atualizar_status():
    criar_tabelas()

    agora = datetime.now()
    limite_ativacao = agora - timedelta(hours=JANELA_ATIVACAO_HORAS)

    with conectar() as conexao:
        conexao.execute(
            """
            UPDATE relatos
            SET status = 'expirado'
            WHERE status IN ('pendente', 'ativo')
              AND expira_em <= ?
            """,
            (agora.isoformat(timespec="seconds"),),
        )

        conexao.execute(
            """
            UPDATE relatos
            SET status = 'rejeitado'
            WHERE status IN ('pendente', 'ativo')
              AND confirmacoes - rejeicoes <= ?
            """,
            (SALDO_MINIMO_REJEICAO,),
        )

        pendentes = conexao.execute(
            """
            SELECT id, categoria, lat, lon, id_sessao
            FROM relatos
            WHERE status = 'pendente'
              AND criado_em >= ?
            """,
            (limite_ativacao.isoformat(timespec="seconds"),),
        ).fetchall()

        ids_ativar = set()

        for indice, relato in enumerate(pendentes):
            for comparado in pendentes[indice + 1:]:
                mesma_categoria = (
                    relato["categoria"] == comparado["categoria"]
                )
                sessoes_diferentes = (
                    relato["id_sessao"] != comparado["id_sessao"]
                )
                distancia = _distancia_em_metros(
                    relato["lat"],
                    relato["lon"],
                    comparado["lat"],
                    comparado["lon"],
                )

                if (
                    mesma_categoria
                    and sessoes_diferentes
                    and distancia <= RAIO_ATIVACAO_METROS
                ):
                    ids_ativar.add(relato["id"])
                    ids_ativar.add(comparado["id"])

        if ids_ativar:
            conexao.executemany(
                """
                UPDATE relatos
                SET status = 'ativo'
                WHERE id = ?
                """,
                [(id_relato,) for id_relato in ids_ativar],
            )

    with conectar() as conexao:
        linhas = conexao.execute(
            """
            SELECT status, COUNT(*) AS quantidade
            FROM relatos
            GROUP BY status
            """
        ).fetchall()

    contagens = {
        "pendente": 0,
        "ativo": 0,
        "rejeitado": 0,
        "expirado": 0,
    }

    for linha in linhas:
        contagens[linha["status"]] = linha["quantidade"]

    return contagens

def votar(id_relato, voto, id_sessao):
    try:
        id_relato = int(id_relato)
        voto = int(voto)
    except (TypeError, ValueError):
        return False

    if voto not in (1, -1):
        return False

    if not id_sessao:
        return False

    atualizar_status()

    with conectar() as conexao:
        relato = conexao.execute(
            """
            SELECT status
            FROM relatos
            WHERE id = ?
            """,
            (id_relato,),
        ).fetchone()

        if relato is None:
            return False

        if relato["status"] not in ("pendente", "ativo"):
            return False

        voto_existente = conexao.execute(
            """
            SELECT id
            FROM votos
            WHERE id_relato = ? AND id_sessao = ?
            """,
            (id_relato, id_sessao),
        ).fetchone()

        if voto_existente is not None:
            return False

        conexao.execute(
            """
            INSERT INTO votos (id_relato, id_sessao, voto, criado_em)
            VALUES (?, ?, ?, ?)
            """,
            (
                id_relato,
                id_sessao,
                voto,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

        if voto == 1:
            conexao.execute(
                """
                UPDATE relatos
                SET confirmacoes = confirmacoes + 1
                WHERE id = ?
                """,
                (id_relato,),
            )
        else:
            conexao.execute(
                """
                UPDATE relatos
                SET rejeicoes = rejeicoes + 1
                WHERE id = ?
                """,
                (id_relato,),
            )

    atualizar_status()

    return True