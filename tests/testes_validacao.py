import os
from datetime import datetime, timedelta

os.environ["PORONDE_MODO"] = "demo"

from src import relatos
from src.banco import conectar
from src.config import BBOX_VM


def limpar_dados_de_teste():
    with conectar() as conexao:
        conexao.execute(
            """
            DELETE FROM votos
            WHERE id_relato IN (
                SELECT id
                FROM relatos
                WHERE id_sessao LIKE 'teste_%'
            )
            """
        )

        conexao.execute(
            """
            DELETE FROM relatos
            WHERE id_sessao LIKE 'teste_%'
            """
        )


def executar_teste():
    sul, norte, oeste, leste = BBOX_VM
    lat = (sul + norte) / 2
    lon = (oeste + leste) / 2

    limpar_dados_de_teste()

    try:
        resultado = relatos.registrar_relato(
            "Categoria inexistente",
            "Teste",
            lat,
            lon,
            "teste_categoria",
        )
        assert resultado == "Categoria inválida."

        resultado = relatos.registrar_relato(
            "Outro",
            "x" * 201,
            lat,
            lon,
            "teste_descricao",
        )
        assert "200 caracteres" in resultado

        resultado = relatos.registrar_relato(
            "Outro",
            "Teste",
            "abc",
            lon,
            "teste_coordenada",
        )
        assert "precisam ser números" in resultado

        resultado = relatos.registrar_relato(
            "Outro",
            "Teste",
            0,
            0,
            "teste_fora_bbox",
        )
        assert "Vila Mariana" in resultado

        for numero in range(3):
            resultado = relatos.registrar_relato(
                "Outro",
                f"Teste de limite {numero}",
                lat,
                lon,
                "teste_limite",
            )
            assert isinstance(resultado, int)

        resultado = relatos.registrar_relato(
            "Outro",
            "Quarto relato na mesma hora",
            lat,
            lon,
            "teste_limite",
        )
        assert "3 relatos por hora" in resultado

        id_primeiro = relatos.registrar_relato(
            "Via bloqueada ou obra",
            "Primeiro relato próximo",
            lat,
            lon,
            "teste_ativacao_1",
        )

        id_segundo = relatos.registrar_relato(
            "Via bloqueada ou obra",
            "Segundo relato próximo",
            lat + 0.0005,
            lon,
            "teste_ativacao_2",
        )

        with conectar() as conexao:
            primeiro = conexao.execute(
                "SELECT status FROM relatos WHERE id = ?",
                (id_primeiro,),
            ).fetchone()

            segundo = conexao.execute(
                "SELECT status FROM relatos WHERE id = ?",
                (id_segundo,),
            ).fetchone()

        assert primeiro["status"] == "ativo"
        assert segundo["status"] == "ativo"

        voto_aceito = relatos.votar(
            id_primeiro,
            1,
            "teste_voto_confirmacao",
        )
        assert voto_aceito is True

        voto_repetido = relatos.votar(
            id_primeiro,
            1,
            "teste_voto_confirmacao",
        )
        assert voto_repetido is False

        id_rejeitar = relatos.registrar_relato(
            "Outro",
            "Relato para rejeitar",
            lat - 0.002,
            lon,
            "teste_rejeicao",
        )

        voto_rejeicao = relatos.votar(
            id_rejeitar,
            -1,
            "teste_voto_rejeicao",
        )
        assert voto_rejeicao is True

        with conectar() as conexao:
            rejeitado = conexao.execute(
                "SELECT status FROM relatos WHERE id = ?",
                (id_rejeitar,),
            ).fetchone()

        assert rejeitado["status"] == "rejeitado"

        agora = datetime.now()

        with conectar() as conexao:
            resultado = conexao.execute(
                """
                INSERT INTO relatos (
                    categoria, descricao, lat, lon, criado_em, expira_em,
                    status, confirmacoes, rejeicoes, id_sessao, simulado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "Outro",
                    "Relato expirado para teste",
                    lat,
                    lon,
                    (agora - timedelta(hours=13)).isoformat(
                        timespec="seconds"
                    ),
                    (agora - timedelta(hours=1)).isoformat(
                        timespec="seconds"
                    ),
                    "pendente",
                    0,
                    0,
                    "teste_expiracao",
                    0,
                ),
            )

            id_expirado = resultado.lastrowid

        contagens = relatos.atualizar_status()

        with conectar() as conexao:
            expirado = conexao.execute(
                "SELECT status FROM relatos WHERE id = ?",
                (id_expirado,),
            ).fetchone()

        assert expirado["status"] == "expirado"
        assert set(contagens) == {
            "pendente",
            "ativo",
            "rejeitado",
            "expirado",
        }

        print("10 validações dos relatos concluídas.")

    finally:
        limpar_dados_de_teste()


if __name__ == "__main__":
    executar_teste()