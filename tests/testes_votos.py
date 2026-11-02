import os

os.environ["PORONDE_MODO"] = "demo"

from src import relatos


def executar_teste():
    try:
        relatos.gerar_relatos_simulados()

        alertas = relatos.listar_alertas_ativos()

        id_confirmar = int(alertas.iloc[0]["id"])
        id_rejeitar = int(alertas.iloc[1]["id"])

        resposta = relatos.votar_relato(
            id_confirmar,
            "sessao_confirmacao",
            1,
        )
        assert resposta == "Voto registrado."

        resposta_repetida = relatos.votar_relato(
            id_confirmar,
            "sessao_confirmacao",
            1,
        )
        assert resposta_repetida == "Esta sessão já votou nesse relato."

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

        resposta = relatos.votar_relato(
            id_rejeitar,
            "sessao_rejeicao",
            -1,
        )
        assert resposta == "Voto registrado."

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