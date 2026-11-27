import { useState } from 'react'
import dados from '../data/observatorio.json'
import './Pesquisa.css'

const cores = ['#0A2940', '#48A85C', '#0A2940', '#FFC107', '#8EA9B3', '#EF4444', '#6C9A76', '#B88A00', '#C7D6CA']
const formatar = (n) => n.toLocaleString('pt-BR')
const porcentagem = (n, total) => total ? (100 * n / total).toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + '%' : '—'


function Cidade() {
  const predios = [
    { x: 70, y: 148, w: 65, h: 92 },
    { x: 151, y: 100, w: 65, h: 140 },
    { x: 232, y: 130, w: 60, h: 110 },
    { x: 310, y: 52, w: 78, h: 188 },
    { x: 406, y: 93, w: 65, h: 147 },
    { x: 490, y: 143, w: 60, h: 97 },
    { x: 566, y: 114, w: 60, h: 126 },
  ]

  const caminho = `
    M30 242
    H120
    Q140 242 140 222
    V205
    Q140 190 155 190
    H216
    Q235 190 235 209
    V222
    Q235 242 255 242
    H415
    Q435 242 435 222
    V177
    Q435 160 452 160
    H525
    Q545 160 545 180
    V222
    Q545 242 565 242
    H665
  `

  const pontos = [
    { x: 180, y: 190, cor: '#48A85C' },
    { x: 350, y: 242, cor: '#FFC107' },
    { x: 490, y: 160, cor: '#EF4444' },
  ]

  return (
    <div className="obs-ilustracao-dados">

      <svg
        viewBox="0 0 700 300"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >

        {/* Linhas de referência de um gráfico */}
        <g
          stroke="#0A2940"
          strokeWidth="1"
          strokeDasharray="5 6"
          opacity="0.09"
        >
          {[60, 100, 140, 180, 220].map((y) => (
            <line
              key={y}
              x1="35"
              y1={y}
              x2="665"
              y2={y}
            />
          ))}
        </g>

        {/* Prédios inspirados em gráficos de barras */}
        {predios.map((predio, indice) => (
          <g key={indice}>

            <rect
              x={predio.x}
              y={predio.y}
              width={predio.w}
              height={predio.h}
              rx="2"
              fill={indice === 3 ? '#0A2940' : '#E4E9EB'}
              stroke="#0A2940"
              strokeWidth="2"
            />

            {/* Janelas */}
            {Array.from({
              length: Math.floor((predio.h - 20) / 24),
            }).map((_, linha) => (
              <g key={linha}>

                {[0, 1, 2].map((coluna) => (
                  <rect
                    key={coluna}
                    x={predio.x + 12 + coluna * 15}
                    y={predio.y + 15 + linha * 24}
                    width="7"
                    height="10"
                    rx="1"
                    fill={indice === 3 ? '#A0B3BF' : '#829AA9'}
                    className={
                      (indice + linha + coluna) % 5 === 0
                        ? 'obs-janela-animada'
                        : ''
                    }
                    style={{
                      '--janela-cor': [
                        '#48A85C',
                        '#FFC107',
                        '#EF4444',
                      ][indice % 3],
                      '--janela-atraso': `${indice * 100 + linha * 80}ms`,
                    }}
                  />
                ))}

              </g>
            ))}

          </g>
        ))}

        {/* Contorno claro para destacar o trajeto */}
        <path
          d={caminho}
          fill="none"
          stroke="#F8F7F4"
          strokeWidth="12"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Trajeto principal */}
        <path
          d={caminho}
          fill="none"
          stroke="#0A2940"
          strokeWidth="4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        
{/* Movimento ao longo do trajeto */}
<g className="obs-sinal-movel">

  <circle
    r="7"
    fill="#0A2940"
    stroke="#F8F7F4"
    strokeWidth="2"
  >

    {/* Movimento da bolinha */}
    <animateMotion
      path={caminho}
      dur="4.5s"
      repeatCount="1"
      fill="freeze"
      calcMode="paced"
    />

    {/* Mudança de cor durante o trajeto */}
    <animate
      attributeName="fill"
      values="#0A2940;#48A85C;#FFC107;#EF4444;#EF4444"
      keyTimes="0;0.223155;0.468166;0.714068;1"
      calcMode="discrete"
      dur="4.5s"
      repeatCount="1"
      fill="freeze"
    />

  </circle>

</g>


        {/* Pontos com as cores da identidade visual */}
        {pontos.map((ponto, indice) => (
          <g key={indice}>

            <circle
              cx={ponto.x}
              cy={ponto.y}
              r="19"
              fill={ponto.cor}
              opacity="0.12"
            />

            <circle
              cx={ponto.x}
              cy={ponto.y}
              r="8"
              fill={ponto.cor}
              stroke="#0A2940"
              strokeWidth="3"
            />

            <circle
              cx={ponto.x}
              cy={ponto.y}
              r="8"
              fill="none"
              stroke={ponto.cor}
              strokeWidth="2"
              className="obs-dados-pulso"
              style={{
                '--pulso-atraso': `${indice * 700}ms`,
              }}
            />

          </g>
        ))}

      </svg>

    </div>
  )
}


function Apoio() {
  const [selecionado, setSelecionado] = useState(null)
  const [expandido, setExpandido] = useState(false)

  const total = dados.apoio.reduce(
    (soma, local) => soma + local.total, 0
  )

  const item = dados.apoio.find(
    (local) => local.nome === selecionado
  )

  const locaisVisiveis = expandido
    ? dados.apoio
    : dados.apoio.slice(0, 3)

  const categoriasRestantes = Math.max(
    0, dados.apoio.length - 3
  )

  let acumulado = 0

  function alternarCategorias() {
    if (expandido) {
      setSelecionado(null)
    }

    setExpandido(!expandido)
  }

  return (
    <article className="obs-card obs-card-apoio">
      <h2>Locais de apoio</h2>

      <p className="obs-sub">
        Distribuição dos locais cadastrados na região.
      </p>

      <div className="obs-rosca-area">
        <svg
          viewBox="0 0 200 200"
          className="obs-rosca"
          aria-hidden="true"
        >
          <circle
            cx="100"
            cy="100"
            r="77"
            fill="none"
            stroke="#E4E9E3"
            strokeWidth="25"
          />

          {total > 0 && dados.apoio.map((local, i) => {
            const parte = local.total / total * 100
            const offset = acumulado

            acumulado += parte

            return (
              <circle
                key={local.nome}
                cx="100"
                cy="100"
                r="77"
                fill="none"
                stroke={cores[i % cores.length]}
                strokeWidth={
                  item?.nome === local.nome ? 29 : 25
                }
                pathLength="100"
                strokeDasharray={`${parte} ${100 - parte}`}
                strokeDashoffset={-offset}
                transform="rotate(-90 100 100)"
                opacity={
                  item && item.nome !== local.nome ? .25 : 1
                }
                className="obs-segmento"
              />
            )
          })}

          <text
            x="100"
            y="98"
            textAnchor="middle"
            className="obs-total"
          >
            {formatar(item?.total ?? total)}
          </text>

          <text
            x="100"
            y="118"
            textAnchor="middle"
            className="obs-total-label"
          >
            {item
              ? porcentagem(item.total, total)
              : 'locais'}
          </text>
        </svg>
      </div>

      <div
        id="categorias-apoio"
        className="obs-legenda"
        aria-label="Categorias dos locais de apoio"
      >
        {locaisVisiveis.map((local, i) => (
          <button
            type="button"
            key={local.nome}
            className={`obs-legenda-item ${
              i >= 3 ? 'obs-categoria-extra' : ''
            }`}
            aria-pressed={selecionado === local.nome}
            onClick={() =>
              setSelecionado(
                selecionado === local.nome
                  ? null
                  : local.nome
              )
            }
          >
            <span
              className="obs-bolinha"
              style={{
                background: cores[i % cores.length],
              }}
            />

            <span>{local.nome}</span>

            <strong>{formatar(local.total)}</strong>
          </button>
        ))}
      </div>

      {categoriasRestantes > 0 && (
        <button
          type="button"
          className="obs-expandir"
          onClick={alternarCategorias}
          aria-expanded={expandido}
          aria-controls="categorias-apoio"
        >
          {expandido
            ? 'Mostrar menos'
            : `Ver mais ${categoriasRestantes} categorias`}

          <svg
            viewBox="0 0 24 24"
            width="17"
            height="17"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="m6 9 6 6 6-6" />
          </svg>
        </button>
      )}

      <p className="obs-fonte">
        Fontes cadastradas: {
          dados.fontes_apoio
            .map((fonte) =>
              `${fonte.nome} (${fonte.total})`
            )
            .join(' e ')
        }. Cadastro não garante funcionamento
        nem acolhimento.
      </p>
    </article>
  )
}


function Ocorrencias() {
  const maximo = Math.max(1, ...dados.ocorrencias.map(x => x.total))
  return (
    <article className="obs-card">
      <h2>Ocorrências por categoria</h2>
      <p className="obs-sub">Registros associados aos trechos da malha viária.</p>
      <div className="obs-barras">
        {dados.ocorrencias.map((item, i) => <div key={item.nome} className="obs-barra-item">
          <div className="obs-barra-label"><span>{item.nome}</span><strong>{formatar(item.total)}</strong></div>
          <div className="obs-trilho" aria-hidden="true"><div className="obs-barra" style={{ width: `${item.total/maximo*100}%`, animationDelay: `${i*120}ms` }}/></div>
        </div>)}
      </div>
      <p className="obs-fonte">Fonte indicada no sistema original: SSP-SP. Recorte informado: 02/07 a 30/09/2026. Totais associados a trechos, não necessariamente ocorrências únicas.</p>
    </article>
  )
}

function Evolucao() {
  const categorias = [...new Set(dados.mensal.map(x => x.categoria))].sort()
  const [categoria, setCategoria] = useState(categorias[0] ?? '')
  const mesesPresentes = [...new Set(dados.mensal.map(x => x.mes))].sort()
  const meses = []
  if (mesesPresentes.length) {
    const [ano, mes] = mesesPresentes[0].split('-').map(Number)
    const cursor = new Date(Date.UTC(ano, mes - 1, 1))
    while (cursor.toISOString().slice(0,7) <= mesesPresentes.at(-1)) {
      meses.push(cursor.toISOString().slice(0,7))
      cursor.setUTCMonth(cursor.getUTCMonth() + 1)
    }
  }
  const valores = meses.map(mes => dados.mensal.find(x => x.mes === mes && x.categoria === categoria)?.total ?? null)
  const max = Math.max(1, ...valores.filter(x => x !== null))
  const x = i => meses.length === 1 ? 185 : 38 + i*285/Math.max(1, meses.length-1)
  const y = v => 150 - v/max*120
  const mesLabel = m => m.slice(5)+'/'+m.slice(2,4)
  return (
    <article className="obs-card">
      <h2>Evolução mensal das ocorrências</h2>
      <p className="obs-sub">Como os registros variam ao longo do tempo.</p>
      {categorias.length === 0 ? <div className="obs-vazio">
        <svg viewBox="0 0 48 48" width="42" height="42" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="M8 8V40H42 M13 31L23 22L31 26L40 13" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="4 4"/></svg>
        <strong>Série histórica indisponível</strong>
        <p>A base atual possui totais por categoria e trecho, mas não contém as datas das ocorrências.</p>
      </div> : <>
        <label className="obs-filtro">Categoria<select value={categoria} onChange={e => setCategoria(e.target.value)}>{categorias.map(c => <option key={c}>{c}</option>)}</select></label>
        <svg viewBox="0 0 350 185" className="obs-mensal" role="img" aria-label={`Evolução mensal: ${categoria}`}>
          {[0, .5, 1].map(fracao => <g key={fracao}><path d={`M38 ${y(max*fracao)}H323`} stroke="#DCE3DE" strokeDasharray="4 4"/><text x="32" y={y(max*fracao)+4} textAnchor="end" className="obs-eixo">{formatar(max*fracao)}</text></g>)}
          {valores.map((v,i) => i > 0 && v !== null && valores[i-1] !== null ? <line key={i} x1={x(i-1)} y1={y(valores[i-1])} x2={x(i)} y2={y(v)} stroke="#0A2940" strokeWidth="3" strokeLinecap="round"/> : null)}
          {meses.map((m,i) => <g key={m}>{valores[i] !== null && <circle cx={x(i)} cy={y(valores[i])} r="4" fill="#0A2940"><title>{mesLabel(m)}: {formatar(valores[i])}</title></circle>}{(i % Math.max(1,Math.ceil(meses.length/6)) === 0 || i === meses.length-1) && <text x={x(i)} y="169" className="obs-eixo" textAnchor="middle">{mesLabel(m)}</text>}</g>)}
        </svg>
        <details className="obs-tabela"><summary>Ver valores por mês</summary><table><thead><tr><th>Mês</th><th>Registros</th></tr></thead><tbody>{meses.map((m,i) => <tr key={m}><td>{mesLabel(m)}</td><td>{valores[i] === null ? 'Não informado' : formatar(valores[i])}</td></tr>)}</tbody></table></details>
      </>}
      <p className="obs-fonte">
  Fonte: SSP-SP — SPDados 2026.
  Período: 02/07 a 30/09/2026.
  Registros filtrados pelo limite geográfico da Vila Mariana
  e agrupados pelo mês da ocorrência e categoria.
</p>
    </article>
  )
}

export default function Pesquisa() {
  return (
    <main className="obs-pagina">
      <div className="obs-container">
        <header className="obs-abertura">
  <div>
    <h1>
      A Vila Mariana <span>em dados.</span>
    </h1>

    <p>
      Uma análise da região a partir dos dados
      utilizados pelo PorOnde?.
    </p>
  </div>

  <Cidade />
</header>
        <section className="obs-grid" aria-label="Análises urbanas">
          <Apoio /><Ocorrencias /><Evolucao />
        </section>
      </div>
    </main>
  )
}
