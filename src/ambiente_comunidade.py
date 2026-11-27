"""Isolamento dos relatos comunitários, independente do modo SQLite legado."""
import os

AMBIENTE = os.getenv("PORONDE_AMBIENTE", "demonstracao").strip().lower()
if AMBIENTE not in {"real", "demonstracao"}:
    raise RuntimeError("PORONDE_AMBIENTE deve ser real ou demonstracao.")
SIMULADO = AMBIENTE == "demonstracao"
