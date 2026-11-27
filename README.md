# PorOnde
Plataforma colaborativa para comparar caminhos a pé, com informações sobre iluminação, condições das ruas e relatos da comunidade.

## Interface integrada em Streamlit

A interface usa o export do Lovable como referência. A base Python é a
`develop` enviada. `src/config.py` e `src/supabase_db.py` vêm de
`b/regras-alertas`. A cópia de `rotas` enviada é igual à `develop`.
A página pública anterior de relatos foi substituída pelo formulário
contextual da rota. Nenhuma branch remota foi alterada.

### Bloco 1 — Abrir e navegar

Na pasta extraída, com o ambiente Python do projeto ativado, execute:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

No Início, confira a marca, a ilustração e o botão **Buscar um trajeto**.
O botão deve abrir a tela Trajeto. Confira também os links **Nossa pesquisa**
e **Sobre nós**. A fonte Manrope é carregada pela web quando disponível.

### Bloco 2 — Calcular e comparar

Na tela Trajeto, informe dois endereços dentro da cobertura da Vila Mariana.
A busca de endereços e os mosaicos do mapa dependem de internet. O grafo,
os locais de apoio e o CSV de pontuações acompanham este ZIP.

Depois de calcular, confira se aparecem de uma a três alternativas.
Selecione outra rota quando disponível e confirme que o mapa muda. Em
**Por que esta pontuação?**, confira os fatores e o período da SSP-SP.
O mesmo limite de faixa é usado na lista e na linha principal do mapa.
O atalho **Emergência** fica abaixo do canto direito do mapa.

### Bloco 3 — Enviar um relato

Use as credenciais do Supabase que a equipe já utiliza, configuradas em
`.streamlit/secrets.toml`. O arquivo `.streamlit/secrets.toml.example` só
mostra o formato. A aplicação espera o esquema e as funções SQL da
branch `b/regras-alertas`, já configurados no ambiente da equipe. O arquivo
SQL vindo dessa branch é material de referência e não é executado pelo app.

Com uma rota escolhida, clique em **Deixar um relato**, marque o ponto no mapa,
informe a categoria e envie em um banco de teste já configurado. Confirme
que o registro chegou para avaliação. Em modo `demo`, o formulário fica
indisponível e o app não consulta o banco real. Se a consulta de alertas
falhar em modo real, a explicação da rota informa que a nota foi calculada
sem alertas da comunidade.

### Bloco 4 — Inserir conteúdo da pesquisa e da equipe

- Na Pesquisa, coloque o arquivo `data/pesquisa_agregada.csv` com o cabeçalho
  `tema,resposta,total,base`. Use uma linha por opção e repita a quantidade
  de respondentes em `base` para as opções de uma mesma pergunta. `total`
  é a contagem daquela opção. A página lê resultados agregados.
- No Sobre, a foto coletiva opcional é `assets/equipe.jpg`. Para perfis
  individuais, use `data/equipe.json` como uma lista de objetos com
  `nome`, `papel`, `bio` e, se disponível, `foto` com o nome do arquivo
  em `assets/`.

### Arquivos por bloco

| Bloco | Arquivos |
| --- | --- |
| 1 | `app.py`, `src/ui_paginas.py`, `assets/`, `.streamlit/config.toml` |
| 2 | `src/ui_rotas.py`, `src/rotas.py`, `src/mapa.py` |
| 3 | `src/ui_relatos.py`, `src/supabase_db.py`, `src/config.py` |
| 4 | `src/ui_paginas.py`, arquivos opcionais em `data/` e `assets/` |
