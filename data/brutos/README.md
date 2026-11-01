# PorOnde — Fontes de dados brutos

## Objetivo

Documentar os dados originais utilizados pela Pessoa A no processamento dos indicadores de contexto do projeto PorOnde.

## 1. Ocorrências — SSP-SP

- Fonte: Secretaria da Segurança Pública do Estado de São Paulo
- Endereço da fonte: a confirmar
- Base selecionada: a confirmar
- Período dos dados: a confirmar
- Data do download: a confirmar
- Formato do arquivo: a confirmar
- Pasta local: data/brutos/ssp/

## 2. Iluminação pública — GeoSampa

- Fonte: GeoSampa — Prefeitura de São Paulo
- Endereço da fonte: a confirmar
- Camada selecionada: a confirmar
- Data do download: a confirmar
- Formato do arquivo: a confirmar
- Pasta local: data/brutos/geosampa/

## Observações

Os dados brutos devem ser preservados sem alterações.

O tratamento, a padronização e os recortes geográficos serão realizados em etapas posteriores.

Os arquivos originais não serão enviados ao GitHub.

## Andamento da Pessoa A — Etapa A2: Inspeção dos dados da SSP-SP

**Data do registro:** 31/10/2026  
**Branch:** `tarefa-01-dados-brutos`  
**Status:** A2 em andamento — pausada após a Célula 11.

### 1. Objetivo

Inspecionar os dados criminais públicos da Secretaria da Segurança Pública de São Paulo (SSP-SP), identificando a estrutura das planilhas, os campos disponíveis, a quantidade estimada de registros e possíveis problemas de qualidade.

Esta inspeção prepara a futura limpeza e integração dos dados utilizados nos indicadores de contexto do PorOnde, cujo MVP está limitado à Vila Mariana, em São Paulo.

### 2. Arquivos selecionados

Os arquivos originais estão armazenados localmente em `data/brutos/ssp/`:

- `SPDadosCriminais_2026.xlsx`
- `CelularesSubtraidos_2026.xlsx`
- `ObjetosSubtraidos_2026.xlsx`

Os arquivos brutos não devem ser modificados nem enviados ao GitHub.

### 3. Ferramentas utilizadas

- Python
- Jupyter Notebook
- pandas
- openpyxl
- Ambiente virtual `.venv`

Notebook de exploração: `notebooks/01_inspecao_ssp.ipynb`.

Também foi criado o script auxiliar `src/inspecionar_ssp.py`, que poderá ser revisado posteriormente.

### 4. Estrutura das bases

Foram identificadas seis abas contendo dados:

| Arquivo | Aba | Linhas estimadas |
|---|---|---:|
| Dados criminais gerais | JAN-JUN_2026 | 555.404 |
| Dados criminais gerais | JUL-DEZ_2026 | 259.496 |
| Celulares subtraídos | CELULAR_2026 | 256.076 |
| Objetos subtraídos | OBJETOS_01_TRIM_2026 | 431.089 |
| Objetos subtraídos | OBJETOS_02_TRIM_2026 | 421.364 |
| Objetos subtraídos | OBJETOS_03_TRIM_2026 | 394.639 |

**Total estimado: 2.318.068 linhas.**

Esse total não representa a quantidade de crimes ou boletins distintos.

As bases possuem campos de identificação do BO, data da ocorrência, natureza criminal, bairro, latitude e longitude.

Foi observada uma diferença estrutural: o terceiro trimestre da base de objetos apresenta 56 colunas, enquanto os dois primeiros apresentam 55. A diferença ainda precisa ser investigada.

### 5. Descobertas sobre a metodologia da SSP-SP

As abas de metodologia das bases de celulares e objetos informam que:

- Um mesmo boletim pode gerar várias linhas, associadas a pessoas, naturezas criminais ou objetos.
- As bases são disponibilizadas em formato bruto, sem tratamento prévio de consistência.
- Para identificar um boletim, a metodologia recomenda combinar `NOME_DELEGACIA`, `ANO_BO` e `NUM_BO`.
- O local de registro do BO pode ser diferente do local em que o crime aconteceu.
- Alguns dados de endereço são ocultados para proteção de informações pessoais.
- As bases de celulares e objetos possuem finalidade exploratória e não constituem estatísticas criminais oficiais.

**Consequência para o projeto:** não podemos contar cada linha como um crime distinto nem somar diretamente os registros das três bases.

### 6. Análise inicial de repetição — Base de celulares

Foi analisada uma amostra das primeiras 10.000 linhas da aba `CELULAR_2026`.

Resultados:

| Indicador | Resultado |
|---|---:|
| Linhas analisadas | 10.000 |
| Boletins distintos pela chave indicada | 8.859 |
| Linhas com identificação incompleta | 0 |
| Linhas adicionais com identificação repetida | 1.141 |

Na amostra, 8.328 boletins apareceram apenas uma vez. Outros apareceram repetidamente, chegando a 28 linhas associadas ao mesmo identificador.

As 1.141 linhas adicionais correspondem a 11,41% da amostra, mas isso não significa que 11,41% dos boletins sejam duplicados.

A análise confirma a necessidade de estudar a estrutura dos registros antes de realizar deduplicação.

### 7. Decisões técnicas até o momento

1. Utilizar Jupyter Notebook para exploração e visualização dos dados.
2. Manter o código definitivo de tratamento e cálculo de indicadores em arquivos Python reutilizáveis.
3. Preservar os arquivos originais da SSP-SP.
4. Não realizar limpeza ou exclusão de registros durante a A2.
5. Investigar a identificação de ocorrências antes de juntar as três bases.
6. Não interpretar as ocorrências registradas como uma medida direta ou garantia de segurança.

### 8. Pendências e próximos passos

**Retomar a partir da Célula 12 do notebook `01_inspecao_ssp.ipynb`.**

- **Célula 12:** investigar a coluna adicional da aba `OBJETOS_03_TRIM_2026`.
- **Célula 13:** verificar datas e coordenadas em amostras das seis abas.
- **Célula 14:** identificar as naturezas criminais mais frequentes na base geral.
- Posteriormente: aprofundar a análise de duplicidades, qualidade das coordenadas e relevância das categorias criminais para pedestres.

A etapa A2 ainda não foi concluída. Nenhum score foi calculado e nenhum conjunto de ocorrências foi tratado definitivamente.

### 9. Cuidados para a equipe

O MVP considera a Vila Mariana, mas os dados ainda não foram filtrados geograficamente pelo limite oficial da área.

O recorte espacial definitivo dependerá do arquivo geográfico do limite da Vila Mariana, previsto na integração com a Pessoa C.

As informações sobre crimes serão utilizadas como indicadores contextuais relativos, combinados com outros fatores. O PorOnde não deve afirmar que uma rota é segura ou livre de riscos.