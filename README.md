# PorOnde?

Plataforma colaborativa para comparar trajetos a pé com informações sobre o contexto urbano. O MVP tem como área de cobertura a região da Vila Mariana, em São Paulo (SP).

**A rota mostra como chegar, mas não mostra o contexto.**

## Acesse o projeto

- [Aplicação web](https://poronde.vercel.app/)
- [Comparar trajetos](https://poronde.vercel.app/trajeto)
- [API — documentação interativa](https://poronde-backend.onrender.com/docs)
- [Repositório](https://github.com/PorOnde/PorOnde)

Projeto acadêmico em versão de demonstração. A pontuação representa os critérios e dados disponíveis no sistema, não uma garantia de segurança. A aplicação não realiza monitoramento em tempo real nem substitui serviços de emergência.

## Objetivo

Ajudar pessoas que se deslocam a pé a escolher um caminho com mais informações, além de distância e tempo estimado. A plataforma reúne indicadores de iluminação, ocorrências registradas, locais de apoio e relatos comunitários.

## Funcionalidades do MVP

- Busca de origem e destino dentro da área de cobertura, com sugestões de endereços.
- Comparação de uma a três alternativas de trajeto, conforme os caminhos distintos disponíveis na rede de ruas.
- Exibição de distância, tempo estimado, Score de Contexto e justificativas da pontuação.
- Mapa interativo com seleção de trajetos, indicadores urbanos, locais de apoio e relatos próximos ao percurso.
- Cadastro de relatos comunitários, votação, alertas, continuidade e identificação de recorrências.
- Observatório Urbano, na página Nossa pesquisa, com informações agregadas e fontes de dados.
- Página Sobre nós, com apresentação da equipe.
- Recursos de acessibilidade por meio do VLibras e do Legilo, incluindo ajustes de leitura e contraste.

## Tecnologias

| Camada | Tecnologia | Finalidade |
| --- | --- | --- |
| Frontend | React, Vite, JavaScript e Tailwind CSS | Interface web |
| Backend | Python 3.11, FastAPI e Uvicorn | API e regras de negócio |
| Processamento geográfico | OSMnx, NetworkX, Pandas, GeoPandas, Shapely e PyProj | Rede de ruas, cálculos e análise espacial |
| Banco de dados | Supabase (PostgreSQL) | Relatos, votos e informações comunitárias |
| Mapa | Leaflet, React Leaflet, CARTO e OpenStreetMap | Visualização geográfica |
| Geocodificação | Geoapify | Conversão de endereços em coordenadas |
| Acessibilidade | VLibras e Legilo | Tradução para Libras e recursos de leitura |
| Hospedagem | Vercel e Render | Frontend e backend, respectivamente |
| Versionamento | Git e GitHub | Controle de versões |

Streamlit e SQLite fazem parte da evolução inicial do projeto. A aplicação web publicada utiliza React, FastAPI e Supabase. O Nominatim público foi substituído pelo Geoapify na consulta de endereços; o OSMnx continua no processamento geográfico.

## Arquitetura

```text
Navegador
  |
  v
React / Vercel
  |
  v
FastAPI / Render
  |-- Geoapify: localização de endereços
  |-- OSMnx / NetworkX: cálculo de trajetos
  |-- Dados geográficos e indicadores: cálculo do contexto
  |-- Supabase: relatos, votos, alertas e recorrências

O frontend utiliza CARTO / OpenStreetMap na visualização do mapa.
```

## Como funciona

1. O usuário informa a origem e o destino na região atendida.
2. O backend localiza os endereços, valida a área de cobertura e associa os pontos à rede de ruas.
3. O algoritmo calcula alternativas distintas, respeitando o limite de distância definido no projeto.
4. Cada alternativa apresenta distância, tempo estimado de caminhada, indicadores e Score de Contexto.
5. O usuário seleciona um trajeto e consulta suas informações no mapa.
6. A comunidade pode registrar situações encontradas ao longo do caminho e avaliar relatos existentes.

### Score de Contexto

A pontuação de 0 a 100 combina indicadores disponíveis de iluminação, ocorrências e locais de apoio, com ajustes por alertas comunitários elegíveis. As faixas de cor representam maior, intermediária ou menor compatibilidade com os critérios adotados. Não correspondem a classificações oficiais de segurança.

Relatos pendentes não penalizam a pontuação. Alertas ativos elegíveis podem descontar 10 pontos por alerta, com teto de 30 pontos, conforme as regras de avaliação implementadas. Recorrências não penalizam diretamente o Score.

### Comunidade

Um relato novo entra como pendente. A ativação depende das regras de categoria, proximidade, período e sessões distintas. O sistema também prevê rejeição por saldo negativo, expiração, verificação de continuidade e identificação de recorrências.

No ambiente de demonstração, os novos registros recebem a identificação `simulado=true` pelo servidor. O objetivo é separar as informações comunitárias simuladas dos registros reais. Não cadastre ocorrências fictícias em ambiente real.

## Executar localmente

### Pré-requisitos

- Python 3.11 (versão utilizada no desenvolvimento: 3.11.9).
- Node.js e npm compatíveis com o frontend.
- Git.
- Acesso autorizado ao projeto Supabase, com esquema e funções SQL configurados.
- Chaves próprias do Geoapify e do CARTO.
- Conexão à internet para os serviços externos.

### 1. Clonar o repositório

```powershell
git clone https://github.com/PorOnde/PorOnde.git
cd PorOnde
```

### 2. Preparar o backend (Windows/PowerShell)

Na raiz do repositório:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-api.txt
```

Configure as variáveis de ambiente no terminal do backend, substituindo os valores ilustrativos por credenciais próprias. Não registre valores reais no GitHub.

```powershell
$env:PORONDE_MODO = 'real'
$env:PORONDE_AMBIENTE = 'demonstracao'
$env:PORONDE_ORIGENS = 'http://localhost:5173'
$env:PORONDE_SUPABASE_URL = 'URL_DO_SUPABASE'
$env:PORONDE_SUPABASE_SECRET_KEY = 'CHAVE_PRIVADA_DO_SUPABASE'
$env:GEOAPIFY_API_KEY = 'CHAVE_DO_GEOAPIFY'
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

`PORONDE_MODO=real` seleciona a integração com Supabase em vez do modo SQLite legado. `PORONDE_AMBIENTE=demonstracao` define o ambiente comunitário de testes. São configurações diferentes.

Para uma nova instância do banco, é necessário configurar o esquema e as funções SQL do projeto. O arquivo `sql/atualizar_comunidade.sql` é uma migração sobre o esquema existente, não uma instalação completa de um banco vazio. Não execute migrações novamente no banco da equipe sem necessidade e sem backup.

### 3. Preparar o frontend

Em outro terminal, a partir da raiz do repositório:

```powershell
cd frontend
npm install
```

Crie `frontend/.env.local` com os seguintes campos:

```dotenv
VITE_API_URL=http://127.0.0.1:8000
VITE_CARTO_API_KEY=CHAVE_DO_CARTO
```

Em seguida:

```powershell
npm run dev
```

Abra o endereço exibido pelo Vite (normalmente http://localhost:5173). Se utilizar outra porta, ajuste também `PORONDE_ORIGENS` no backend.

Para verificar a compilação de produção do frontend:

```powershell
npm run build
```

## Configuração da hospedagem

| Serviço | Configuração |
| --- | --- |
| Vercel | Diretório `frontend`; variáveis `VITE_API_URL` e `VITE_CARTO_API_KEY`; configuração de navegação SPA em `frontend/vercel.json`. |
| Render | Backend Python, instalação das dependências e comando `uvicorn api:app --host 0.0.0.0 --port $PORT`. |
| Supabase | Banco PostgreSQL e funções de negócio da comunidade. |

No Render, configure `PORONDE_ORIGENS=https://poronde.vercel.app`, `PORONDE_AMBIENTE=demonstracao`, `PORONDE_MODO=real`, as credenciais privadas do Supabase e `GEOAPIFY_API_KEY`. Na Vercel, `VITE_API_URL` aponta para `https://poronde-backend.onrender.com`.

A branch `main` contém a versão integrada do MVP. A branch `mvp-final` deve ser preservada enquanto for utilizada pelo Render. A publicação do frontend foi realizada via Vercel CLI (`vercel --prod` na pasta `frontend`). Alterações futuras devem ser verificadas antes de qualquer nova publicação.

## Estrutura principal

| Arquivo ou diretório | Responsabilidade |
| --- | --- |
| `frontend/` | Interface React |
| `frontend/src/pages/` | Páginas da aplicação |
| `frontend/src/components/trajeto/` | Componentes de rotas, mapa e relatos |
| `frontend/src/services/` | Comunicação com a API |
| `api.py` | Endpoints FastAPI |
| `src/rotas.py` | Geocodificação e cálculo de alternativas |
| `src/grafo.py` | Rede de ruas |
| `src/score.py` | Avaliação e pontuação dos trajetos |
| `src/abrigos.py` | Locais de apoio |
| `src/catalogo_enderecos.py` | Sugestões de endereços |
| `src/supabase_db.py` | Integração com o banco |
| `src/ambiente_comunidade.py` | Separação de ambientes comunitários |
| `data/` | Dados utilizados pelo projeto |
| `sql/` | Scripts de banco e migrações |
| `tests/` | Testes de regras e integração |

## Fontes de dados e créditos

- OpenStreetMap: rede de ruas e informações geográficas — [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright).
- CARTO: mapas de base — [carto.com/attribution](https://carto.com/attribution/).
- Geoapify: serviço de geocodificação — [geoapify.com](https://www.geoapify.com/).
- Prefeitura de São Paulo: dados urbanos de iluminação e apoio conforme a base processada do projeto.
- Secretaria da Segurança Pública de São Paulo (SSP-SP): registros históricos de ocorrências utilizados na análise.
- Relatos comunitários: informações fornecidas pelos usuários, sujeitas às regras de validação. Registros simulados são destinados à demonstração.

Os períodos, recortes e fontes dos indicadores devem ser interpretados de acordo com os dados utilizados no projeto. Não são informações completas ou atualizadas em tempo real.

## Validação da entrega

Situação registrada em 27/11/2026, a partir dos testes e evidências compartilhados pela equipe:

- [x] Publicação do frontend e backend.
- [x] Comunicação entre frontend e backend.
- [x] Geocodificação das estações Santa Cruz e Vila Mariana e de outros endereços numerados.
- [x] Cálculo e visualização de trajetos no site publicado.
- [x] Compilação do frontend.
- [x] Envio de relato com status pendente.
- [x] Legilo funcionando em teste local.
- [x] Integração do código na branch `main`, conferida com `mvp-final`.
- [ ] Validação completa de votação, ativação, rejeição, continuidade, recorrência e expiração no ambiente publicado.
- [ ] Conferência completa do impacto de alertas no Score e dos locais de apoio.
- [ ] Revisão final de acessibilidade, responsividade e desempenho em diferentes dispositivos.
- [ ] Auditoria completa de segurança e privacidade para uso público real.

O repositório inclui testes automatizados. Com o ambiente Python preparado, o teste de integração consolidado pode ser executado a partir da raiz:

```powershell
python tests/test_integracao_final.py
```

A API também oferece os endpoints `/api/saude`, `/api/ambiente` e `/api/comunidade/saude` para verificações de disponibilidade e configuração. A aprovação desses testes não substitui a validação das regras no navegador e no banco publicado.

## Limitações e segurança

- Cobertura restrita à área-piloto da Vila Mariana; não cobre toda a cidade.
- Podem existir apenas uma ou duas alternativas quando não houver três caminhos suficientemente distintos.
- A geocodificação depende de serviços externos, limites de uso e qualidade dos dados. Endereços podem não ser reconhecidos ou apresentar imprecisão. As duas estações de referência utilizam coordenadas previamente conferidas.
- O Render gratuito pode apresentar demora após períodos de inatividade.
- A pontuação não prevê crimes nem garante segurança. A plataforma não oferece navegação GPS em tempo real, instruções faladas de percurso ou rotas salvas.
- Recursos de acessibilidade auxiliam a utilização da interface, mas não certificam conformidade integral com normas de acessibilidade.
- Sessões comunitárias anônimas não equivalem a autenticação robusta. Moderação, proteção contra abuso, privacidade e limites de requisições exigem revisão antes de uma operação real.
- Não publique `.env`, `.env.local`, `.streamlit/secrets.toml`, chaves privadas ou caches de endereços. Variáveis `VITE_` são incorporadas ao frontend e podem ser vistas no navegador; use apenas chaves destinadas a esse tipo de acesso e aplique restrições quando disponíveis.
- O texto de endereços é enviado ao provedor de geocodificação. Evite inserir endereços pessoais ou dados sensíveis em demonstrações.

## Equipe

Projeto desenvolvido em equipe para fins acadêmicos. Os perfis das integrantes estão disponíveis na página [Sobre nós](https://poronde.vercel.app/).

