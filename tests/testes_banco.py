from src.banco import conectar, criar_tabelas

CAMINHO_TESTE = "data/banco_teste.db"

# Cria as tabelas duas vezes para confirmar que não dá erro
criar_tabelas(CAMINHO_TESTE)
criar_tabelas(CAMINHO_TESTE)

with conectar(CAMINHO_TESTE) as conexao:
    conexao.execute(
        """
        INSERT INTO relatos (
            categoria, descricao, lat, lon, criado_em, expira_em,
            status, confirmacoes, rejeicoes, id_sessao, simulado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Outro",
            "Teste de leitura do banco",
            -23.5800,
            -46.6300,
            "2026-10-28 10:00:00",
            "2026-10-28 22:00:00",
            "pendente",
            0,
            0,
            "sessao_teste",
            1,
        ),
    )

    relato = conexao.execute(
        """
        SELECT categoria, descricao, status
        FROM relatos
        WHERE id_sessao = ?
        """,
        ("sessao_teste",),
    ).fetchone()

    print(dict(relato))

    conexao.execute(
        "DELETE FROM relatos WHERE id_sessao = ?",
        ("sessao_teste",),
    )

print("Teste do banco concluído.")