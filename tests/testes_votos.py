import os

os.environ["PORONDE_MODO"] = "demo"

from src import relatos


def executar_teste():
    try:
        relatos.gerar_relatos_simulados()

        alertas = relatos.listar_alertas_ativos()

        id_confirmar = int(alertas.iloc[0]["id"])
        id_rejeitar = int(alertas.iloc[1]["id"])

        voto_aceito = relatos.votar(
            id_confirmar,
            1,
            "sessao_confirmacao",
        )
        assert voto_aceito is True

        voto_repetido = relatos.votar(
            id_confirmar,
            1,
            "sessao_confirmacao",
        )
        assert voto_repetido is False

        with relatos.conectar() as conexao:
            relato_confirmado = conexao.execute(
                """
                SELECT confirmacoes
                FROM relatos
                WHERE id = ?
                """,
                (id_confirmar,),
            ).fetchone()

        assert relato_confirmado["confirmacoes"] == 1

        voto_aceito = relatos.votar(
            id_rejeitar,
            -1,
            "sessao_rejeicao",
        )
        assert voto_aceito is True

        with relatos.conectar() as conexao:
            relato_rejeitado = conexao.execute(
                """
                SELECT status, rejeicoes
                FROM relatos
                WHERE id = ?
                """,
                (id_rejeitar,),
            ).fetchone()

        assert relato_rejeitado["rejeicoes"] == 1
        assert relato_rejeitado["status"] == "rejeitado"

        print("Teste de votos concluído.")

    finally:
        relatos.limpar_simulados()


if __name__ == "__main__":
    executar_teste()