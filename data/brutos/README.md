PorOnde — Dados e Score de Contexto da Pessoa A
Objetivo
Documentar as fontes, o tratamento dos dados e os resultados do Score de Contexto. As seções 1 a 13 registram as fontes, a inspeção inicial da A2 e as responsabilidades da equipe. A seção 14 descreve as entregas e validações da A3 à A12.

O MVP está limitado a deslocamentos a pé na Vila Mariana, em São Paulo.
1. Ocorrências — SSP-SP
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
2. Iluminação pública — GeoSampa
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
3. Preservação dos dados e versionamento
Os dados brutos devem ser preservados sem alterações.

O notebook e as funções de tratamento geram os arquivos derivados em data/tratados/.

Os arquivos originais da SSP-SP e do GeoSampa não devem ser enviados ao GitHub.

O relatório local data/tratados/inspecao_estrutura_ssp.json contém primeiras linhas das planilhas e não deve ser incluído no commit de compartilhamento.

Antes de versionar o notebook, limpar suas saídas para evitar publicar registros individuais de boletins e arquivos excessivamente grandes.

A configuração do .gitignore e os arquivos selecionados devem ser conferidos antes do commit.
4. Andamento da Pessoa A — A2
Registro inicial: 31/10/2026.

Branch de trabalho da Pessoa A: tarefa-01-dados-brutos. A documentação da A2 foi registrada no commit 3e2fa06.

Status: inspeção exploratória realizada nas seis abas SSP-SP, com amostras das primeiras 10.000 linhas por aba, e na base completa de iluminação. Funções de leitura implementadas e testadas com amostras.

As contagens abaixo descrevem a inspeção inicial. A A3 processou as seis abas completas e registrou as perdas por filtro na seção 14.
5. Ferramentas e arquivos de trabalho
Ferramentas utilizadas:
- Python.
- Jupyter Notebook no VS Code.
- pandas.
- openpyxl.
- GeoPandas 1.2.0.
- OSMnx, Folium, Shapely, NumPy e scikit-learn nas etapas de processamento e validação espacial.
- Ambiente virtual .venv.
Notebook de exploração:
- notebooks/01_inspecao_ssp.ipynb
Script auxiliar:
- src/inspecionar_ssp.py
Funções reutilizáveis de leitura:
- src/dados.py
O notebook é utilizado para exploração e conferência. O código reutilizável de leitura e tratamento fica em arquivos Python dentro de src/.
6. Estrutura das bases SSP-SP
Foram identificadas seis abas contendo dados:
Arquivo	Aba	Linhas estimadas sem cabeçalho	Colunas estimadas
SPDadosCriminais_2026.xlsx	JAN-JUN_2026	555.404	30
SPDadosCriminais_2026.xlsx	JUL-DEZ_2026	259.496	30
CelularesSubtraidos_2026.xlsx	CELULAR_2026	256.076	55
ObjetosSubtraidos_2026.xlsx	OBJETOS_01_TRIM_2026	431.089	55
ObjetosSubtraidos_2026.xlsx	OBJETOS_02_TRIM_2026	421.364	55
ObjetosSubtraidos_2026.xlsx	OBJETOS_03_TRIM_2026	394.639	56


Total estimado: 2.318.068 linhas.

As estimativas utilizam as dimensões das planilhas, descontando uma linha de cabeçalho. Podem incluir linhas vazias ou apenas formatadas.

Esse total não representa a quantidade de crimes ou boletins distintos.

Também foram identificadas abas informativas:
- Campos da Tabela_SPDADOS, na base geral.
- METODOLOGIA e DICIONARIO DE DADOS, nas bases de celulares e objetos.
Coluna adicional no terceiro trimestre de objetos
O relatório de inspeção mostra uma 56ª posição com cabeçalho vazio na aba OBJETOS_03_TRIM_2026.

Os 55 cabeçalhos anteriores coincidem, em nome e ordem, com os do segundo trimestre.

Não foi verificado se a coluna adicional está inteiramente vazia. Não excluir colunas com dados sem conferência.
7. Metodologia SSP-SP e interpretação dos registros
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
8. Dicionário mínimo dos campos SSP-SP
Os significados abaixo foram conferidos nas abas de dicionário dos arquivos.
Campo	Significado	Uso e cuidado
NOME_DELEGACIA	Delegacia responsável pelo registro	Compõe a chave do BO; não representa necessariamente o local do fato.
ANO_BO	Ano do boletim de ocorrência	Compõe a chave do BO.
NUM_BO	Número do boletim de ocorrência	Não identifica sozinho um boletim.
VERSAO	Versionamento do registro	Presente nas bases de celulares e objetos; regra de consolidação ainda não definida.
DATA_OCORRENCIA_BO	Data da ocorrência	Campo temporal do fato; precisa de validação no conjunto completo.
DATA_REGISTRO	Data do registro da ocorrência	Campo da base geral; não confundir com data do fato.
DATAHORA_REGISTRO_BO	Data do registro da ocorrência	Campo das bases de celulares e objetos; não confundir com data do fato.
RUBRICA	Natureza jurídica da ocorrência	Exemplo observado: Furto (art. 155).
NATUREZA_APURADA	Classificação criminal analisada e validada pela equipe SPDados	Presente na base geral; exemplo observado: FURTO - OUTROS.
DESCR_TIPOLOCAL	Grupo de tipos de locais onde ocorreu o fato	Pode ajudar a avaliar a pertinência do registro para deslocamentos a pé.
DESCR_SUBTIPOLOCAL	Subgrupo vinculado ao tipo de local	Complementa a descrição do local.
BAIRRO	Bairro da ocorrência	Exemplo observado: VILA MARIANA; não define sozinho o recorte espacial.
LOGRADOURO	Endereço dos fatos	Informação auxiliar; pode apresentar limitações ou proteção de dados.
LATITUDE	Latitude da ocorrência	Deve ser convertida e validada antes do uso espacial.
LONGITUDE	Longitude da ocorrência	Deve ser convertida e validada antes do uso espacial.
NOME_MUNICIPIO	Município de registro	Exemplo observado: S.PAULO; não usar sozinho para localizar o fato.
NOME_MUNICIPIO_CIRCUNSCRICAO	Município da delegacia de circunscrição associado ao local do fato	Nome utilizado na base geral.
NOME_MUNICIPIO_CIRC	Município da delegacia de circunscrição associado ao local do fato	Nome utilizado nas bases de celulares e objetos.
CIDADE	Cidade dos fatos	Significado confirmado no dicionário de celulares; não presumir o mesmo significado em outra base sem conferir.


Não incluir exemplos de registros individuais de boletins nesta documentação.

Os exemplos acima ilustram valores observados ou a finalidade dos campos; não constituem um esquema final de saída da A3.
9. Resultados da inspeção amostral SSP-SP
Foram examinadas as primeiras 10.000 linhas de cada uma das seis abas de dados.

Essas amostras não são aleatórias e seus resultados não devem ser generalizados para as bases completas.
Tipos e valores ausentes
Aba	Bairro nulo	Bairro em branco	Latitude nula	Longitude nula
Geral JAN-JUN	0	0	0	0
Geral JUL-DEZ	0	7	0	0
Celulares	10	0	1.494	1.494
Objetos 1º trimestre	10	0	1.504	1.504
Objetos 2º trimestre	2	0	702	702
Objetos 3º trimestre	10	0	227	227


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

O recorte espacial da A4 usa coordenadas válidas e o limite entregue pela Pessoa C. O campo textual de bairro serve de referência para a inspeção.
Datas
As amostras contêm datas de ocorrência anteriores a 2026.

A diferença entre data de registro e data de ocorrência é uma hipótese a investigar para explicar parte desses registros; não é uma causa comprovada.

As datas mínimas e máximas obtidas nas amostras não representam necessariamente os extremos dos arquivos completos.
Coordenadas e área geográfica
Foram realizados testes exploratórios de limites numéricos, valores diferentes de zero e localização em um retângulo aproximado da capital.

Esses testes não comprovam precisão das coordenadas nem pertencimento à Vila Mariana.

A área de uma delegacia e o nome textual de um bairro não substituem o recorte pelo polígono utilizado pelo projeto.
Município de registro
Uma comparação com o texto literal SÃO PAULO retornou zero nas amostras.

A inspeção posterior encontrou a grafia S.PAULO em NOME_MUNICIPIO.

Esse campo descreve o município de registro do BO. Não deve ser utilizado sozinho para determinar o município do fato.
Categorias criminais
Foram examinadas frequências de RUBRICA e NATUREZA_APURADA na amostra da base geral.

A seleção usada no score atual está descrita na A5, na seção 14.

Não incluir automaticamente crimes de veículos, trânsito ou outras categorias no indicador de caminhada sem justificativa.
10. Análise inicial de repetição — Celulares
Foi analisada uma amostra das primeiras 10.000 linhas da aba CELULAR_2026.

A identificação foi examinada pela combinação NOME_DELEGACIA, ANO_BO e NUM_BO.
Indicador	Resultado
Linhas analisadas	10.000
Boletins distintos pela chave indicada	8.859
Linhas com identificação incompleta	0
Linhas adicionais com identificação repetida	1.141


Na amostra, 8.328 boletins apareceram apenas uma vez. Houve identificadores associados a até 28 linhas.

As 1.141 linhas adicionais correspondem a 11,41% das linhas da amostra. Isso não significa que 11,41% dos boletins sejam duplicados.

Várias linhas do mesmo BO podem ser legítimas. A análise não define uma regra final de deduplicação.

A A5 mediu a sobreposição entre arquivos na janela analisada na seção 14.
11. Inspeção da iluminação pública
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
Campos apresentados na leitura
Campo	Tipo observado	Observação
il_numero	float64	Totalmente nulo; significado oficial detalhado ainda não conferido.
il_placa	texto	Exemplo observado: IP0487798; significado oficial detalhado ainda não conferido.
il_tipilum	texto	Valor LED em todos os registros; não comprova funcionamento da luminária.
il_enderec	texto	Contém nomes de logradouros; exemplo observado: RUA CARDOSO DE OLIVEIRA.
il_unidade	texto	Predominantemente em branco; significado oficial detalhado ainda não conferido.
geometry	geometry	Localização do ponto em EPSG:31983, por exemplo POINT (356933.148 7394684.957).


As descrições observacionais não substituem um dicionário oficial da fonte. Não atribuir significado adicional aos campos apenas pelo nome.

Na A6, a contagem de pontos próximos aos trechos usou as geometrias. A leitura e a inspeção da A2 preservaram os registros originais.

A presença de um ponto cadastrado não comprova que a luminária esteja funcionando nem informa a iluminação efetiva da rua.

A validade geométrica dos pontos não comprova a precisão de sua localização.
12. Validação das funções de leitura
Implementadas em src/dados.py:
- ler_ssp(caminho, aba, colunas=None, n_linhas=None): leitura de uma aba Excel, com seleção de colunas e limite opcional de linhas.
- ler_iluminacao(caminho, n_linhas=None): leitura da camada de iluminação do GeoPackage, com limite opcional de linhas.
Teste básico executado pelo notebook:
Verificação	Resultado
SSP-SP	5 linhas e 3 colunas selecionadas
Iluminação	5 linhas e 6 colunas
CRS da iluminação	EPSG:31983
Geometrias da amostra de iluminação	Cinco pontos


A função ler_ssp também foi utilizada nas inspeções das amostras das seis abas.

Essas duas funções cuidam da leitura. A limpeza e as conferências posteriores estão descritas na seção 14.

O teste básico não comprova desempenho ou qualidade dos arquivos completos. Casos de erro não foram registrados como testados.
13. Responsabilidades e integração
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
Entradas da Pessoa C usadas nesta execução:
- data/tratados/grafo_vila_mariana.graphml
- data/tratados/limite_vila_mariana.geojson
A A4 usou o limite da Pessoa C. Os cálculos por trecho usaram o grafo correspondente e a contagem de locais de apoio usou o abrigos.csv da Pessoa B.

A deve consumir as entregas de B e C sem modificar unilateralmente seus contratos.

A chave de integração dos trechos continua sendo edge_id, no formato u_v_key.
14. Tratamento dos dados e Score de Contexto
O commit 354bc5f, na branch tarefa-01-dados-brutos, reúne o notebook, o código de leitura, limpeza e avaliação de rotas e o CSV de scores. O cálculo cobre 12.134 trechos da Vila Mariana e inclui os locais de apoio da Pessoa B. A Pessoa C pode usar o CSV para ler os indicadores por trecho e a função de avaliação para calcular o score de uma rota.
A3 — Limpeza das ocorrências da SSP-SP
Foram processadas seis abas de três planilhas, uma por vez. Padronizamos os nomes das colunas, convertemos datas e coordenadas e tratamos o traço nas coordenadas como valor ausente. A cada filtro, registramos quantas linhas foram removidas. O retângulo preliminar cobre latitude de −24,1 a −23,3 e longitude de −47,0 a −46,3.
Etapa do funil	Linhas
Lidas	2.318.068
Removidas por data ausente ou inválida	0
Removidas por falta de coordenadas utilizáveis	139.782
Removidas por coordenada igual a zero	304.454
Removidas por ficar fora do retângulo	567.327
Cópias idênticas removidas dentro de cada aba	826
Restantes	1.305.679


A exportação de ssp_limpo.csv foi conferida por releitura. O CSV preserva o arquivo e a aba de origem. O ssp_funil_a3.csv guarda as contagens agregadas por aba. Uma mesma chave de boletim pode aparecer em várias linhas ou fontes.
A4 — Recorte da Vila Mariana
Usamos o polígono de limite_vila_mariana.geojson, fornecido pela Pessoa C. Mantivemos os pontos no interior do contorno e geramos ssp_vila_mariana.csv com 19.259 linhas. A conferência visual mostrou uma amostra de 500 linhas dentro da área esperada.

A comparação com o registro no 27º ou no 36º DP encontrou 452 linhas em comum. Outras 18.807 linhas estavam dentro do polígono, mas foram registradas em outras delegacias, e 3.030 linhas registradas nas duas delegacias tinham coordenadas fora do polígono. Por isso, o recorte segue as coordenadas do fato.
A5 — Ocorrências recentes por trecho
Usamos a janela de 02/07/2026 a 30/09/2026. Entre as 3.301 chaves de boletim distintas identificadas no diagnóstico dessa janela, 1.676 apareciam em mais de um arquivo. O cálculo atual usa a base geral da SSP-SP, com os rótulos FURTO - OUTROS, ROUBO - OUTROS e LESÃO CORPORAL DOLOSA. Cada combinação de delegacia, ano e número conta uma vez, mesmo quando tem mais de uma categoria selecionada.

O filtro gerou 1.854 boletins. O OSMnx associou 1.839 ao trecho mais próximo em até 50 m e deixou 15 fora desse limite. 711 trechos receberam pelo menos um boletim. A equipe ainda precisa registrar a confirmação da seleção de categorias.
A6 a A9 — Iluminação, locais de apoio e hotspots
Indicador	Como foi calculado
Iluminação	Contamos os pontos do GeoSampa a até 30 m de cada trecho. Encontramos 5.960 pontos distintos associados à rede e 12.090 trechos com pelo menos um ponto próximo.
Locais de apoio	Usamos abrigos.csv, da Pessoa B, para contar os locais a até 100 m de cada trecho.
Integração	Juntamos os indicadores pelo edge_id no formato u_v_key. A tabela integrada tem uma linha para cada um dos 12.134 trechos do grafo da Pessoa C.
Hotspots	Comparamos 12 combinações do DBSCAN. Escolhemos raio de 100 m e mínimo de cinco boletins. Os 50 polígonos, com margem de 15 m, tocam ou cruzam 6.046 trechos (49,8%).


Ocorrências e iluminação foram expressas por 100 m, usando 20 m como comprimento mínimo no denominador. As distâncias espaciais foram calculadas em metros no sistema EPSG:31983. O mapa mapa_conferencia_a6.html foi gerado localmente. Falta registrar a conferência visual da iluminação.
A10 — Score de Contexto por trecho
O score combina 35% de iluminação, 35% de ocorrências, 15% de locais de apoio e 15% de hotspot. Iluminação e ocorrências usam percentis das taxas por 100 m, com a nota de ocorrências invertida. Locais de apoio recebem nota 0, 50 ou 100 para zero, um ou dois ou mais locais. O componente de hotspot recebe zero quando o trecho está em um polígono e 100 nos demais.
Cor	Faixa de score	Trechos	Parcela da rede
Verde	70 ou mais	494	4,1%
Amarelo	De 40 até abaixo de 70	8.109	66,8%
Vermelho	Abaixo de 40	3.531	29,1%


O menor score foi 0,88 e o maior foi 83,48. O trechos_score.csv foi conferido contra as chaves e as contagens de locais de apoio da tabela integrada.
A11 e A12 — Testes de rota e conferência das ruas
A função avaliar_rota(edge_ids, alertas), em src/score.py, calcula a média dos scores ponderada pelo comprimento dos trechos. Cada alerta ativo a até 50 m da rota desconta 10 pontos, até o máximo de 30. O retorno inclui score, cor, pior trecho e fatores que ajudam a explicar o resultado.

Os testes com zero, um e cinco alertas retornaram 83,48, 73,48 e 53,48. Na rota de dois trechos, a média ponderada esperada e a retornada coincidiram em 35,8061.
Rua	Trechos	Faixa de score	Verdes	Amarelos	Vermelhos
Domingos de Morais	118	6,30 a 64,36	0	77	41
Vergueiro	164	8,63 a 75,16	20	104	40
Joaquim Távora	22	4,27 a 37,21	0	0	22
Sena Madureira	98	13,49 a 75,73	4	74	20
Humberto I	24	16,26 a 54,20	0	9	15


A conferência numérica está registrada. A observação qualitativa de quem conhece os trechos ainda precisa ser anotada, especialmente nos casos em que a cor diverge da experiência no local.
Arquivos para a integração
Arquivo	Uso
[`data/tratados/trechos_score.csv`](../tratados/trechos_score.csv)	Entrega da Pessoa A. Contém uma linha por trecho do grafo.
[`src/score.py`](../../src/score.py) e [`src/config.py`](../../src/config.py)	Avaliação da rota e parâmetros do score.
[`src/dados.py`](../../src/dados.py) e [`notebooks/01_inspecao_ssp.ipynb`](../../notebooks/01_inspecao_ssp.ipynb)	Leitura, limpeza, cálculo e conferências das etapas.
data/tratados/grafo_vila_mariana.graphml e data/tratados/limite_vila_mariana.geojson	Entradas da Pessoa C. O grafo deve ser da mesma versão usada para gerar o CSV de scores.
data/tratados/abrigos.csv	Entrada da Pessoa B para recalcular o indicador de locais de apoio.


Para testar a integração, a Pessoa C deve usar o grafo correspondente ao CSV de scores. A avaliação com alertas recebe a tabela de alertas ativos da Pessoa B. A documentação detalhada do método foi mantida em um arquivo separado.
15. Pendências para revisão e integração
- Registrar a confirmação da equipe sobre a base e as categorias selecionadas na A5.
- Registrar a conferência visual da iluminação da A6 e a avaliação qualitativa dos trechos das cinco ruas da A12.
- Testar uma rota na interface integrada, usando o mesmo grafo, o CSV de scores e os alertas ativos da Pessoa B.
- Confirmar o push da branch e a revisão do Pull Request conforme o fluxo combinado pela equipe.
- Completar a documentação de origem quando disponíveis as datas de download, o endereço exato usado para a SSP-SP e o dicionário oficial dos atributos auxiliares do GeoSampa.
A cobertura temporal completa dos arquivos SSP-SP, a sobreposição fora da janela analisada e o conteúdo integral da coluna sem cabeçalho da aba de objetos seguem como limites da investigação. Se a equipe mudar a seleção de ocorrências, é preciso refazer a associação aos trechos e os hotspots antes de recalcular o score.
16. Limites de interpretação do produto
O PorOnde apresenta indicadores contextuais relativos, combinados com outros fatores.

Os registros SSP-SP podem apresentar atraso, subnotificação e imprecisões. A iluminação cadastrada não informa necessariamente o funcionamento atual das luminárias.

Não há garantia de segurança individual, e ausência de registros não significa ausência de risco.

O aplicativo não deve afirmar que uma rua ou rota é segura ou livre de riscos.