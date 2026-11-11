import os
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ_PROJETO / "data"

MODO_DADOS = os.getenv("PORONDE_MODO", "real").lower()

if MODO_DADOS not in {"real", "demo"}:
    raise ValueError("PORONDE_MODO deve ser 'real' ou 'demo'.")


ARQUIVO_BANCO_REAL = PASTA_DADOS / "poronde.db"
ARQUIVO_BANCO_DEMO = PASTA_DADOS / "poronde_demo.db"


BBOX_VM = (-23.59974, -23.56764, -46.65362, -46.61421)

CAMINHO_GRAFO = "data/tratados/grafo_vila_mariana.graphml"
CAMINHO_LIMITE = "data/tratados/limite_vila_mariana.geojson"
NOME_LUGAR = "Vila Mariana, São Paulo, Brazil"


CATEGORIAS_VALIDADE_HORAS = {
    "Rua mal iluminada ou escura": 24,
    "Via bloqueada ou obra": 24,
    "Aglomeração ou tumulto": 12,
    "Roubo ou furto ocorrido agora": 12,
    "Transporte com problema (ônibus ou metrô)": 12,
    "Outro": 12,
}

MAX_CARACTERES_DESCRICAO = 200
LIMITE_RELATOS_POR_HORA = 3

SALDO_MINIMO_REJEICAO = -1
RAIO_ATIVACAO_METROS = 200
JANELA_ATIVACAO_HORAS = 4
ARQUIVO_ABRIGOS = PASTA_DADOS / "tratados" / "abrigos.csv"
ARQUIVO_LOCAIS_MANUAIS = PASTA_DADOS / "brutos" / "locais_apoio_manuais.csv"
RAIO_ABRIGOS_METROS = 100
PASTA_TRATADOS = PASTA_DADOS / "tratados"

ARQUIVO_SCORE_REAL = PASTA_TRATADOS / "trechos_score.csv"
ARQUIVO_SCORE_EXEMPLO = PASTA_TRATADOS / "trechos_score_exemplo.csv"

ARQUIVO_SCORE = (
    ARQUIVO_SCORE_REAL
    if ARQUIVO_SCORE_REAL.exists()
    else ARQUIVO_SCORE_EXEMPLO
)
PASTA_CACHE = PASTA_DADOS / "cache"
ARQUIVO_CACHE_GEOCODIFICACAO = PASTA_CACHE / "geocodificacao.json"

# Parte A — Classificação do Score de Contexto
LIMITE_VERDE = 70
LIMITE_AMARELO = 40

# Parte A — Influência dos alertas comunitários na avaliação da rota
RAIO_ALERTA_ROTA_M = 50
PENALIDADE_ALERTA = 10
LIMITE_PENALIDADE_ALERTA = 30