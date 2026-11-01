
from pathlib import Path
from collections import Counter
import json
import re
from openpyxl import load_workbook

PASTA_DADOS = Path("data/brutos/ssp")
PASTA_SAIDA = Path("data/tratados")
ARQUIVOS = [
    "SPDadosCriminais_2026.xlsx",
    "CelularesSubtraidos_2026.xlsx",
    "ObjetosSubtraidos_2026.xlsx",
]

def normalizar(texto):
    return re.sub(r"[^A-Z0-9]", "", str(texto).upper())

def inspecionar_arquivo(caminho):
    resultado = {
        "arquivo": caminho.name,
        "abas": [],
    }

    workbook = load_workbook(caminho, read_only=True, data_only=True)

    try:
        for aba in workbook.worksheets:
            primeiras_linhas = list(
                aba.iter_rows(min_row=1, max_row=8, values_only=True)
            )

            resultado_aba = {
                "nome": aba.title,
                "linhas_estimadas": aba.max_row,
                "colunas_estimadas": aba.max_column,
                "primeiras_linhas": [
                    [str(valor)[:120] if valor is not None else None for valor in linha]
                    for linha in primeiras_linhas
                ],
            }

            resultado["abas"].append(resultado_aba)
    finally:
        workbook.close()

    return resultado

def main():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    resultados = []

    for nome in ARQUIVOS:
        caminho = PASTA_DADOS / nome

        if not caminho.exists():
            print(f"ARQUIVO NÃO ENCONTRADO: {caminho}")
            continue

        print(f"Inspecionando: {nome}")
        resultado = inspecionar_arquivo(caminho)
        resultados.append(resultado)

        for aba in resultado["abas"]:
            print(f"  Aba: {aba['nome']}")
            print(f"  Linhas estimadas: {aba['linhas_estimadas']}")
            print(f"  Colunas estimadas: {aba['colunas_estimadas']}")

    destino = PASTA_SAIDA / "inspecao_estrutura_ssp.json"

    with open(destino, "w", encoding="utf-8") as arquivo:
        json.dump(resultados, arquivo, ensure_ascii=False, indent=2)

    print(f"\nRelatório salvo em: {destino}")

if __name__ == "__main__":
    main()
