"""Gera indicadores públicos agregados, sem modificar as bases originais."""
from pathlib import Path
import json
import pandas as pd

RAIZ = Path(__file__).resolve().parent
BASE = RAIZ / 'data' / 'tratados'
SAIDA = RAIZ / 'frontend' / 'src' / 'data' / 'observatorio.json'

NOMES = {
    'farmacia': 'Farmácias', 'mercado': 'Mercados', 'loja': 'Lojas',
    'delegacia': 'Delegacias', 'hospital': 'Hospitais', 'clinica': 'Clínicas',
    'posto': 'Postos de combustível', 'metro': 'Metrô (estações e acessos)',
    'outro': 'Outros',
}


def ler_csv(nome, colunas):
    df = pd.read_csv(BASE / nome, encoding='utf-8-sig')
    faltam = set(colunas) - set(df.columns)
    if faltam:
        raise ValueError(f'{nome}: faltam colunas {sorted(faltam)}')
    if df[colunas].isna().any().any():
        raise ValueError(f'{nome}: existem valores ausentes nas colunas necessárias')
    return df


def validar_total(df):
    numeros = pd.to_numeric(df['total'], errors='raise')
    if ((numeros < 0) | (numeros % 1 != 0)).any():
        raise ValueError('Os totais devem ser inteiros não negativos.')
    return df.assign(total=numeros.astype('int64'))


def lista(serie):
    return [{'nome': str(nome), 'total': int(total)}
            for nome, total in serie.sort_values(ascending=False).items()]


def serie_mensal():
    # Arquivo opcional, a gerar da base ORIGINAL datada e validada.
    # Colunas: mes (AAAA-MM), categoria, total. Não inferir datas dos trechos.
    if not (BASE / 'ocorrencias_mensais.csv').exists():
        return []
    df = validar_total(ler_csv('ocorrencias_mensais.csv', ['mes', 'categoria', 'total']))
    if df.empty:
        return []
    if not df['mes'].astype(str).str.fullmatch(r'\d{4}-(0[1-9]|1[0-2])').all():
        raise ValueError('Use AAAA-MM na coluna mes.')
    if df.duplicated(['mes', 'categoria']).any():
        raise ValueError('A base mensal deve ter uma linha por mês e categoria.')
    return [{'mes': str(r.mes), 'categoria': str(r.categoria), 'total': int(r.total)}
            for r in df.sort_values(['mes', 'categoria']).itertuples(index=False)]


def main():
    apoio = ler_csv('abrigos.csv', ['tipo', 'fonte'])
    ocorrencias = validar_total(ler_csv('ocorrencias_por_categoria.csv', ['trecho_id', 'categoria', 'total']))
    apoio = apoio.assign(categoria=apoio['tipo'].map(NOMES).fillna(apoio['tipo']))
    # Preserva categorias combinadas como grupo separado, sem duplicar totais.
    ocorrencias = ocorrencias.assign(categoria=ocorrencias['categoria'].where(
        ~ocorrencias['categoria'].str.contains(' + ', regex=False), 'Categorias combinadas'))
    dados = {
        'apoio': lista(apoio.groupby('categoria').size()),
        'fontes_apoio': lista(apoio.groupby('fonte').size()),
        'ocorrencias': lista(ocorrencias.groupby('categoria')['total'].sum()),
        'mensal': serie_mensal(),
    }
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Dados gerados: {SAIDA}')
    print(f'Locais cadastrados: {len(apoio)}; associações de ocorrências: {ocorrencias.total.sum()}')
    if not dados['mensal']:
        print('Série mensal indisponível: falta base agregada por mês.')


if __name__ == '__main__':
    main()
