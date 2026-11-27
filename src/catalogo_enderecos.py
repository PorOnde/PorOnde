"""Sugestões locais. A confirmação do endereço continua na geocodificação."""
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
import pandas as pd
from src import config

def normalizar(texto):
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", str(texto).casefold())
                           if not unicodedata.combining(c)).split())

@lru_cache(maxsize=4)
def _ler_catalogo(arquivos):
    nomes = {}
    for arquivo, _, coluna in arquivos:
        if not arquivo.is_file():
            continue
        for valor in pd.read_csv(arquivo, usecols=[coluna])[coluna].dropna():
            nome = str(valor).strip()
            if len(nome) < 4 or normalizar(nome) in {"nan", "sem nome", "via sem nome", "nao informado"}:
                continue
            if nome.startswith("[") or nome.startswith("{"):
                continue
            nomes.setdefault(normalizar(nome), nome)
    return tuple(sorted(nomes.items()))

def sugerir(q):
    consulta = normalizar(q)
    if len(consulta) < 2 or any(c.isdigit() for c in consulta):
        return []  # Não inventar número de imóvel.
    caminhos = [(Path(config.ARQUIVO_SCORE), "nome_rua"), (Path(config.ARQUIVO_ABRIGOS), "nome")]
    arquivos = tuple((p, p.stat().st_mtime_ns if p.is_file() else 0, coluna) for p,coluna in caminhos)
    catalogo = _ler_catalogo(arquivos)
    achados = [(not chave.startswith(consulta), len(chave), chave, nome)
               for chave,nome in catalogo if consulta in chave or all(t in chave for t in consulta.split())]
    if not achados and len(consulta) >= 5:
        # Tolera um pequeno erro de digitação, mas só retorna nomes presentes no CSV.
        alvo = consulta.removeprefix("rua ").removeprefix("avenida ")
        aproximados = []
        for chave, nome in catalogo:
            comparavel = chave.removeprefix("rua ").removeprefix("avenida ")
            similaridade = max([SequenceMatcher(None, alvo, comparavel).ratio()] +
                               [SequenceMatcher(None, alvo, parte).ratio() for parte in comparavel.split()])
            if similaridade >= 0.83:
                aproximados.append((-similaridade, len(chave), chave, nome))
        achados = aproximados
    return [nome for _,_,_,nome in sorted(achados)[:6]]
