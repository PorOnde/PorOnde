# PorOnde — Fontes de dados brutos

## Objetivo

Documentar os dados originais utilizados pela Pessoa A no processamento dos indicadores de contexto do PorOnde, as inspeções realizadas e as limitações identificadas.

O MVP está limitado a deslocamentos a pé na Vila Mariana, em São Paulo.

## 1. Ocorrências — SSP-SP

- Fonte: Secretaria da Segurança Pública do Estado de São Paulo.
- Endereço exato utilizado no download: não registrado.
- Arquivos selecionados:
  - SPDadosCriminais_2026.xlsx
  - CelularesSubtraidos_2026.xlsx
  - ObjetosSubtraidos_2026.xlsx
- Período: arquivos identificados como 2026; as amostras contêm ocorrências anteriores. A cobertura temporal completa ainda não foi validada.
- Data do download: não registrada.
- Formato: Excel (.xlsx).
- Pasta local: data/brutos/ssp/

Os nomes das abas e dos arquivos não comprovam, sozinhos, o intervalo efetivo das datas de ocorrência.

## 2. Iluminação pública — GeoSampa

- Fonte: GeoSampa — Prefeitura de São Paulo.
- Endereço: https://novogeosampa.prefeitura.sp.gov.br/
- Camada: Pontos de Iluminação Pública.
- Caminho observado no portal: Ambiente Construído → Vias Públicas.
- Responsável informado: Prefeitura de São Paulo / SP Regula — Coordenadoria de Gestão da Rede Municipal de Iluminação Pública.
- Frequência de atualização declarada: mensal.
- Data do download: não registrada.
- Arquivo: SIRGAS_GPKG_iluminacaopublica.gpkg
- Formato: GeoPackage (.gpkg).
- Pasta local: data/brutos/geosampa/

A frequência mensal declarada não comprova a data de atualização efetiva de cada registro.

## 3. Preservação dos dados e versionamento

Os dados brutos devem ser preservados sem alterações.

O tratamento, a padronização e os recortes geográficos serão realizados pelo código em etapas posteriores.

Os arquivos originais da SSP-SP e do GeoSampa não devem ser enviados ao GitHub.

O relatório local data/tratados/inspecao_estrutura_ssp.json contém primeiras linhas das planilhas e não deve ser incluído no commit de compartilhamento.

Antes de versionar o notebook, limpar suas saídas para evitar publicar registros individuais de boletins e arquivos excessivamente grandes.

A configuração do .gitignore e os arquivos selecionados devem ser conferidos antes do commit.

## 4. Andamento da Pessoa A — A2

Registro inicial: 31/10/2026.

Branch utilizada anteriormente: tarefa-01-dados-brutos.
A branch atual deve ser confirmada no Git antes do commit.

Status: inspeção exploratória realizada nas seis abas SSP-SP, com amostras das primeiras 10.000 linhas por aba, e na base completa de iluminação. Funções de leitura implementadas e testadas com amostras.

A inspeção amostral da SSP-SP não equivale a uma validação completa dos arquivos. As contagens completas de qualidade e as perdas por filtro serão apuradas na A3.

O fechamento documental e o compartilhamento pelo Git devem ser conferidos antes de iniciar a A3.

Nenhum score foi calculado e nenhum conjunto de ocorrências foi tratado definitivamente.

## 5. Ferramentas e arquivos de trabalho

Ferramentas utilizadas:

- Python.
- Jupyter Notebook no VS Code.
- pandas.
- openpyxl.
- GeoPandas 1.2.0.
- Ambiente virtual .venv.

Notebook de exploração:

- notebooks/01_inspecao_ssp.ipynb

Script auxiliar:

- src/inspecionar_ssp.py

Funções reutilizáveis de leitura:

- src/dados.py

O notebook é utilizado para exploração e conferência. O código reutilizável de leitura e tratamento fica em arquivos Python dentro de src/.

## 6. Estrutura das bases SSP-SP

Foram identificadas seis abas contendo dados:

| Arquivo | Aba | Linhas estimadas sem cabeçalho | Colunas estimadas |
|---|---|---:|---:|
| SPDadosCriminais_2026.xlsx | JAN-JUN_2026 | 555.404 | 30 |
| SPDadosCriminais_2026.xlsx | JUL-DEZ_2026 | 259.496 | 30 |
| CelularesSubtraidos_2026.xlsx | CELULAR_2026 | 256.076 | 55 |
| ObjetosSubtraidos_2026.xlsx | OBJETOS_01_TRIM_2026 | 431.089 | 55 |
| ObjetosSubtraidos_2026.xlsx | OBJETOS_02_TRIM_2026 | 421.364 | 55 |
| ObjetosSubtraidos_2026.xlsx | OBJETOS_03_TRIM_2026 | 394.639 | 56 |

Total estimado: 2.318.068 linhas.

As estimativas utilizam as dimensões das planilhas, descontando uma linha de cabeçalho. Podem incluir linhas vazias ou apenas formatadas.

Esse total não representa a quantidade de crimes ou boletins distintos.

Também foram identificadas abas informativas:

- Campos da Tabela_SPDADOS, na base geral.
- METODOLOGIA e DICIONARIO DE DADOS, nas bases de celulares e objetos.

### Coluna adicional no terceiro trimestre de objetos

O relatório de inspeção mostra uma 56ª posição com cabeçalho vazio na aba OBJETOS_03_TRIM_2026.

Os 55 cabeçalhos anteriores coincidem, em nome e ordem, com os do segundo trimestre.

Não foi verificado se a coluna adicional está inteiramente vazia. Não excluir colunas com dados sem conferência.

## 7. Metodologia SSP-SP e interpretação dos registros

As metodologias das bases de celulares e objetos informam que:

- Um mesmo boletim pode gerar várias linhas, associadas a pessoas, naturezas criminais ou objetos.
- As bases são disponibilizadas em formato bruto, sem tratamento prévio de consistência.
- Para identificar um boletim, deve ser considerada a combinação NOME_DELEGACIA, ANO_BO e NUM_BO.
- O local de registro do BO pode ser diferente do local em que ocorreu o fato.
- Alguns dados de endereço são ocultados para proteção de informações pessoais.
- As bases de celulares e objetos possuem finalidade exploratória e não constituem as estatísticas criminais oficiais do Estado.

Consequências para o projeto:

- Não contar automaticamente cada linha como um crime distinto.
- Não somar diretamente os registros das três bases.
- Não remover registros apenas por NUM_BO.
- Examinar versões, naturezas e sobreposição entre bases antes de consolidar boletins.
- Não tentar reconstruir informações ocultadas.
- Não interpretar ausência de registros como garantia de segurança.

## 8. Dicionário mínimo dos campos SSP-SP

Os significados abaixo foram conferidos nas abas de dicionário dos arquivos.

| Campo | Significado | Uso e cuidado |
|---|---|---|
| NOME_DELEGACIA | Delegacia responsável pelo registro | Compõe a chave do BO; não representa necessariamente o local do fato. |
| ANO_BO | Ano do boletim de ocorrência | Compõe a chave do BO. |
| NUM_BO | Número do boletim de ocorrência | Não identifica sozinho um boletim. |
| VERSAO | Versionamento do registro | Presente nas bases de celulares e objetos; regra de consolidação ainda não definida. |
| DATA_OCORRENCIA_BO | Data da ocorrência | Campo temporal do fato; precisa de validação no conjunto completo. |
| DATA_REGISTRO | Data do registro da ocorrência | Campo da base geral; não confundir com data do fato. |
| DATAHORA_REGISTRO_BO | Data do registro da ocorrência | Campo das bases de celulares e objetos; não confundir com data do fato. |
| RUBRICA | Natureza jurídica da ocorrência | Exemplo observado: Furto (art. 155). |
| NATUREZA_APURADA | Classificação criminal analisada e validada pela equipe SPDados | Presente na base geral; exemplo observado: FURTO - OUTROS. |
| DESCR_TIPOLOCAL | Grupo de tipos de locais onde ocorreu o fato | Pode ajudar a avaliar a pertinência do registro para deslocamentos a pé. |
| DESCR_SUBTIPOLOCAL | Subgrupo vinculado ao tipo de local | Complementa a descrição do local. |
| BAIRRO | Bairro da ocorrência | Exemplo observado: VILA MARIANA; não define sozinho o recorte espacial. |
| LOGRADOURO | Endereço dos fatos | Informação auxiliar; pode apresentar limitações ou proteção de dados. |
| LATITUDE | Latitude da ocorrência | Deve ser convertida e validada antes do uso espacial. |
| LONGITUDE | Longitude da ocorrência | Deve ser convertida e validada antes do uso espacial. |
| NOME_MUNICIPIO | Município de registro | Exemplo observado: S.PAULO; não usar sozinho para localizar o fato. |
| NOME_MUNICIPIO_CIRCUNSCRICAO | Município da delegacia de circunscrição associado ao local do fato | Nome utilizado na base geral. |
| NOME_MUNICIPIO_CIRC | Município da delegacia de circunscrição associado ao local do fato | Nome utilizado nas bases de celulares e objetos. |
| CIDADE | Cidade dos fatos | Significado confirmado no dicionário de celulares; não presumir o mesmo significado em outra base sem conferir. |

Não incluir exemplos de registros individuais de boletins nesta documentação.

Os exemplos acima ilustram valores observados ou a finalidade dos campos; não constituem um esquema final de saída da A3.

## 9. Resultados da inspeção amostral SSP-SP

Foram examinadas as primeiras 10.000 linhas de cada uma das seis abas de dados.

Essas amostras não são aleatórias e seus resultados não devem ser generalizados para as bases completas.

### Tipos e valores ausentes

| Aba | Bairro nulo | Bairro em branco | Latitude nula | Longitude nula |
|---|---:|---:|---:|---:|
| Geral JAN-JUN | 0 | 0 | 0 | 0 |
| Geral JUL-DEZ | 0 | 7 | 0 | 0 |
| Celulares | 10 | 0 | 1.494 | 1.494 |
| Objetos 1º trimestre | 10 | 0 | 1.504 | 1.504 |
| Objetos 2º trimestre | 2 | 0 | 702 | 702 |
| Objetos 3º trimestre | 10 | 0 | 227 | 227 |

Os demais campos selecionados não apresentaram nulos ou textos em branco nas amostras.

Isso não comprova que todos os valores estejam corretos. Valores como zero, textos de preenchimento ou coordenadas fora da área exigem validações próprias.

Contagens iguais de latitude e longitude ausentes não comprovam que os valores faltam nas mesmas linhas.

Tipos observados:

- Datas selecionadas: datetime64[us].
- ANO_BO e VERSAO, quando selecionados: int64.
- Latitude e longitude na amostra Geral JAN-JUN: object.
- Latitude e longitude nas demais amostras: float64.
- Demais campos selecionados: texto.

Esses tipos foram inferidos nas amostras e podem variar no conjunto completo.

Bairro ausente não será motivo automático para excluir uma ocorrência. O recorte espacial definitivo dependerá de coordenadas válidas e do limite entregue por C.

### Datas

As amostras contêm datas de ocorrência anteriores a 2026.

A diferença entre data de registro e data de ocorrência é uma hipótese a investigar para explicar parte desses registros; não é uma causa comprovada.

As datas mínimas e máximas obtidas nas amostras não representam necessariamente os extremos dos arquivos completos.

### Coordenadas e área geográfica

Foram realizados testes exploratórios de limites numéricos, valores diferentes de zero e localização em um retângulo aproximado da capital.

Esses testes não comprovam precisão das coordenadas nem pertencimento à Vila Mariana.

A área de uma delegacia e o nome textual de um bairro não substituem o recorte pelo polígono utilizado pelo projeto.

### Município de registro

Uma comparação com o texto literal SÃO PAULO retornou zero nas amostras.

A inspeção posterior encontrou a grafia S.PAULO em NOME_MUNICIPIO.

Esse campo descreve o município de registro do BO. Não deve ser utilizado sozinho para determinar o município do fato.

### Categorias criminais

Foram examinadas frequências de RUBRICA e NATUREZA_APURADA na amostra da base geral.

A seleção definitiva das categorias pertinentes a pedestres ainda não foi realizada.

Não incluir automaticamente crimes de veículos, trânsito ou outras categorias no indicador de caminhada sem justificativa.

## 10. Análise inicial de repetição — Celulares

Foi analisada uma amostra das primeiras 10.000 linhas da aba CELULAR_2026.

A identificação foi examinada pela combinação NOME_DELEGACIA, ANO_BO e NUM_BO.

| Indicador | Resultado |
|---|---:|
| Linhas analisadas | 10.000 |
| Boletins distintos pela chave indicada | 8.859 |
| Linhas com identificação incompleta | 0 |
| Linhas adicionais com identificação repetida | 1.141 |

Na amostra, 8.328 boletins apareceram apenas uma vez. Houve identificadores associados a até 28 linhas.

As 1.141 linhas adicionais correspondem a 11,41% das linhas da amostra. Isso não significa que 11,41% dos boletins sejam duplicados.

Várias linhas do mesmo BO podem ser legítimas. A análise não define uma regra final de deduplicação.

A sobreposição entre arquivos e entre abas ainda não foi medida.

## 11. Inspeção da iluminação pública

Arquivo: SIRGAS_GPKG_iluminacaopublica.gpkg

Camada interna: SIRGAS_GPKG_iluminacaopublica

A leitura completa foi executada no notebook com GeoPandas 1.2.0, utilizando a .venv do projeto.

Resultados validados:

- 662.945 registros.
- 6 colunas apresentadas pelo GeoPandas.
- Sistema de coordenadas: EPSG:31983, em metros.
- Todas as geometrias são Point.
- Nenhuma geometria nula, vazia ou inválida.
- il_numero: 662.945 valores nulos.
- il_unidade: 658.654 textos vazios ou contendo apenas espaços.
- il_placa, il_tipilum e il_enderec: sem nulos ou textos em branco.
- Todos os registros apresentam il_tipilum igual a LED.

### Campos apresentados na leitura

| Campo | Tipo observado | Observação |
|---|---|---|
| il_numero | float64 | Totalmente nulo; significado oficial detalhado ainda não conferido. |
| il_placa | texto | Exemplo observado: IP0487798; significado oficial detalhado ainda não conferido. |
| il_tipilum | texto | Valor LED em todos os registros; não comprova funcionamento da luminária. |
| il_enderec | texto | Contém nomes de logradouros; exemplo observado: RUA CARDOSO DE OLIVEIRA. |
| il_unidade | texto | Predominantemente em branco; significado oficial detalhado ainda não conferido. |
| geometry | geometry | Localização do ponto em EPSG:31983, por exemplo POINT (356933.148 7394684.957). |

As descrições observacionais não substituem um dicionário oficial da fonte. Não atribuir significado adicional aos campos apenas pelo nome.

A futura contagem de pontos próximos aos trechos utilizará as geometrias. Não excluir pontos apenas pela ausência de il_numero ou il_unidade.

Nenhum registro foi removido ou alterado. O recorte para a Vila Mariana ainda não foi realizado.

A presença de um ponto cadastrado não comprova que a luminária esteja funcionando nem informa a iluminação efetiva da rua.

A validade geométrica dos pontos não comprova a precisão de sua localização.

## 12. Validação das funções de leitura

Implementadas em src/dados.py:

- ler_ssp(caminho, aba, colunas=None, n_linhas=None): leitura de uma aba Excel, com seleção de colunas e limite opcional de linhas.
- ler_iluminacao(caminho, n_linhas=None): leitura da camada de iluminação do GeoPackage, com limite opcional de linhas.

Teste básico executado pelo notebook:

| Verificação | Resultado |
|---|---|
| SSP-SP | 5 linhas e 3 colunas selecionadas |
| Iluminação | 5 linhas e 6 colunas |
| CRS da iluminação | EPSG:31983 |
| Geometrias da amostra de iluminação | Cinco pontos |

A função ler_ssp também foi utilizada nas inspeções das amostras das seis abas.

As funções apenas leem os arquivos. Não fazem limpeza, exclusão, recorte geográfico ou gravação de resultados.

O teste básico não comprova desempenho ou qualidade dos arquivos completos. Casos de erro não foram registrados como testados.

## 13. Responsabilidades e integração

Pessoa A:

- Leitura e tratamento dos dados SSP-SP e GeoSampa.
- Associação dos indicadores aos trechos.
- Hotspots e Score de Contexto.
- Função de avaliação de rotas conforme o contrato.

Pessoa B:

- Locais de apoio e arquivo data/tratados/abrigos.csv.
- Banco de dados e regras dos relatos comunitários.

Pessoa C:

- Grafo de pedestres.
- Limite geográfico utilizado pelo projeto.
- Rotas, mapa e interface.

Entradas esperadas de C:

- data/tratados/grafo_vila_mariana.graphml
- data/tratados/limite_vila_mariana.geojson

A existência e a validação dessas entregas ainda precisam ser confirmadas com a equipe.

A deve consumir as entregas de B e C sem modificar unilateralmente seus contratos.

A chave de integração dos trechos continua sendo edge_id, no formato u_v_key.

## 14. Próximas etapas e pendências

### A3 — Limpeza SSP-SP

- Ler uma aba por vez e somente as colunas necessárias.
- Padronizar nomes de colunas.
- Converter e validar datas e coordenadas.
- Contar nulos, textos em branco e valores inválidos no conjunto completo.
- Registrar quantas linhas cada filtro remove.
- Examinar linhas integralmente repetidas.
- Não remover registros apenas pelo número do BO.
- Planejar consolidação entre bases e versões antes de somar ocorrências.
- Gerar data/tratados/ssp_limpo.csv com os critérios documentados.

### Etapas posteriores

- A4: recorte pela área geográfica entregue e validada por C.
- A5: escolha justificada de categorias e janela temporal, seguida da associação às arestas.
- A6 em diante: iluminação, locais de apoio, integração, hotspots, score e avaliação de rotas.

### Limitações e informações ainda pendentes

- Endereço exato e data dos downloads SSP-SP.
- Data registrada do download GeoSampa.
- Cobertura temporal completa dos arquivos SSP-SP.
- Qualidade das coordenadas no conjunto completo.
- Sobreposição entre bases e abas.
- Regra de consolidação de versões e naturezas do mesmo BO.
- Conteúdo integral da coluna sem cabeçalho em objetos.
- Dicionário oficial detalhado dos atributos auxiliares GeoSampa.
- Confirmação das entregas atuais de B e C.
- Conferência da branch, do commit, do push e da revisão por B.

O guia prevê dados do ano anterior para evitar corte da janela na virada do ano. Esses arquivos não aparecem no conjunto atualmente inspecionado. Sua necessidade deve ser verificada diante da data de referência e da janela escolhida, antes de aplicar o filtro temporal.

## 15. Limites de interpretação do produto

O PorOnde apresenta indicadores contextuais relativos, combinados com outros fatores.

Os registros SSP-SP podem apresentar atraso, subnotificação e imprecisões. A iluminação cadastrada não informa necessariamente o funcionamento atual das luminárias.

Não há garantia de segurança individual, e ausência de registros não significa ausência de risco.

O aplicativo não deve afirmar que uma rua ou rota é segura ou livre de riscos.