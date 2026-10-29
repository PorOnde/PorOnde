import os
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ_PROJETO / "data"

MODO_DADOS = os.getenv("PORONDE_MODO", "real").lower()

if MODO_DADOS not in {"real", "demo"}:
    raise ValueError("PORONDE_MODO deve ser 'real' ou 'demo'.")

ARQUIVO_BANCO_REAL = PASTA_DADOS / "poronde.db"
ARQUIVO_BANCO_DEMO = PASTA_DADOS / "poronde_demo.db"