import sqlite3
from pathlib import Path

from src.config import ARQUIVO_BANCO_DEMO, ARQUIVO_BANCO_REAL, MODO_DADOS


def conectar(caminho=None):
    """Abre uma conexão com o banco de dados do modo atual."""

    if caminho is None:
        if MODO_DADOS == "demo":
            caminho_banco = ARQUIVO_BANCO_DEMO
        else:
            caminho_banco = ARQUIVO_BANCO_REAL
    else:
        caminho_banco = caminho

    if str(caminho_banco) != ":memory:":
        Path(caminho_banco).parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(caminho_banco)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


def criar_tabelas(caminho=None):
    """Cria as tabelas de relatos e votos, caso ainda não existam."""

    with conectar(caminho) as conexao:
        conexao.executescript(
            """
            CREATE TABLE IF NOT EXISTS relatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                descricao TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                criado_em TEXT NOT NULL,
                expira_em TEXT NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN ('pendente', 'ativo', 'rejeitado', 'expirado')
                ),
                confirmacoes INTEGER NOT NULL DEFAULT 0,
                rejeicoes INTEGER NOT NULL DEFAULT 0,
                id_sessao TEXT NOT NULL,
                simulado INTEGER NOT NULL DEFAULT 0 CHECK (
                    simulado IN (0, 1)
                )
            );

            CREATE TABLE IF NOT EXISTS votos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_relato INTEGER NOT NULL,
                id_sessao TEXT NOT NULL,
                voto INTEGER NOT NULL CHECK (voto IN (1, -1)),
                criado_em TEXT NOT NULL,
                FOREIGN KEY (id_relato) REFERENCES relatos(id),
                UNIQUE (id_relato, id_sessao)
            );
            """
        )


if __name__ == "__main__":
    criar_tabelas()
    print("Banco e tabelas criados com sucesso.")