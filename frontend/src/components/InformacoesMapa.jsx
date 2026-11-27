
import { useEffect, useRef, useState } from 'react'
import {
  Clock,
  Lightbulb,
  TriangleAlert,
  Store,
} from 'lucide-react'

// Três trajetos ilustrativos
const rotas = [
  {
    id: 'verde',
    caminho: 'M100 246 V84 Q100 68 116 68 H430',
    cor: '#16834B',
    tracejado: undefined,
  },
  {
    id: 'amarela',
    caminho: 'M100 246 H414 Q430 246 430 230 V68',
    cor: '#EAB308',
    tracejado: '10 7',
  },
  {
    id: 'vermelha',
    caminho: 'M100 246 L205 158 Q210 154 220 154 H334 Q343 154 350 147 L430 68',
    cor: '#EF4444',
    tracejado: '3 7',
  },
]

// Informações apresentadas pelo PorOnde?
const informacoes = [
  {
    titulo: 'Tempo e distância',
    icone: Clock,
    cor: '#16834B',
  },
  {
    titulo: 'Iluminação da rota',
    icone: Lightbulb,
    cor: '#D6A400',
  },
  {
    titulo: 'Ocorrências registradas',
    icone: TriangleAlert,
    cor: '#EF4444',
  },
  {
    titulo: 'Locais de apoio próximos',
    icone: Store,
    cor: '#0A2940',
  },
]

function InformacoesMapa() {
  const secaoRef = useRef(null)
  const [visivel, setVisivel] = useState(false)

  // Detecta quando a seção aparece na tela
  useEffect(() => {
    const secao = secaoRef.current

    if (!secao) return

    if (!('IntersectionObserver' in window)) {
      setVisivel(true)
      return
    }

    const observador = new IntersectionObserver(
      ([entrada]) => {
        if (entrada.isIntersecting) {
          setVisivel(true)
          observador.unobserve(secao)
        }
      },
      {
        threshold: 0.12,
      }
    )

    observador.observe(secao)

    return () => observador.disconnect()
  }, [])

  return (
    <section
      ref={secaoRef}
      className={`overflow-hidden bg-fundo px-6 pb-16 lg:px-10 lg:pb-20 ${
        visivel ? 'secao-visivel' : ''
      }`}
    >

      <div className="mx-auto grid max-w-6xl items-center gap-10 lg:grid-cols-[1.08fr_1fr] lg:gap-14">

        {/* MAPA ILUSTRATIVO */}

        <figure
          className="revelar"
          style={{ '--atraso': '0ms' }}
        >

          <div className="overflow-hidden rounded-2xl border border-marinho/20 p-3">

            <svg
              viewBox="0 0 520 310"
              className="block h-auto w-full rounded-xl"
              role="img"
              aria-label="Ilustração de três caminhos entre a mesma origem e o mesmo destino"
            >

              {/* Máscaras responsáveis pela animação */}
              <defs>

                {rotas.map((rota) => (
                  <mask
                    key={rota.id}
                    id={`mascara-rota-${rota.id}`}
                    maskUnits="userSpaceOnUse"
                    x="0"
                    y="0"
                    width="520"
                    height="310"
                  >
                    <path
                      d={rota.caminho}
                      pathLength="100"
                      fill="none"
                      stroke="white"
                      strokeWidth="15"
                      strokeLinecap="round"
                      className={`desenhar-rota desenhar-rota-${rota.id}`}
                    />
                  </mask>
                ))}

              </defs>

              {/* Fundo do mapa */}
              <rect
                width="520"
                height="310"
                fill="#EAE7E1"
              />

              {/* Áreas verdes */}
              <path
                d="M0 0 H85 Q85 50 35 56 L0 85Z"
                fill="#D3E8CA"
              />

              <path
                d="M520 235 Q455 239 455 310 H520Z"
                fill="#D3E8CA"
              />

              {/* Ruas ilustrativas */}
              <g
                stroke="#FFFFFF"
                strokeWidth="7"
                fill="none"
                strokeLinejoin="round"
              >
                <path d="M0 68 H520" />
                <path d="M0 154 H520" />
                <path d="M0 246 H520" />
                <path d="M0 110 L520 119" />
                <path d="M0 290 L520 280" />

                <path d="M45 0 L30 310" />
                <path d="M100 0 V310" />
                <path d="M220 0 L190 310" />
                <path d="M330 0 L340 310" />
                <path d="M430 0 V310" />

                {/* Ruas que acompanham os trajetos */}
                {rotas.map((rota) => (
                  <path
                    key={rota.id}
                    d={rota.caminho}
                  />
                ))}
              </g>

              {/* Três trajetos coloridos e animados */}

              {rotas.map((rota) => (
                <path
                  key={rota.id}
                  d={rota.caminho}
                  fill="none"
                  stroke={rota.cor}
                  strokeWidth="6"
                  strokeDasharray={rota.tracejado}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  mask={`url(#mascara-rota-${rota.id})`}
                />
              ))}

              {/* Ponto de origem */}

              <circle
                cx="100"
                cy="246"
                r="10"
                fill="white"
                stroke="#0A2940"
                strokeWidth="4"
              />

              {/* Pino do destino */}

              <g>
                <path
                  d="M430 68 S411 43 411 33 A19 19 0 0 1 449 33 C449 43 430 68 430 68Z"
                  fill="#0A2940"
                />

                <circle
                  cx="430"
                  cy="33"
                  r="11"
                  fill="white"
                />

                <circle
                  cx="430"
                  cy="33"
                  r="7"
                  fill="#EF4444"
                />
              </g>

            </svg>

          </div>

          <figcaption className="mt-3 text-center text-xs text-marinho/65">
            Representação ilustrativa de três alternativas de trajeto.
          </figcaption>

        </figure>

        {/* INFORMAÇÕES DO MAPA */}

        <div>

          <h2
            className="revelar mb-5 text-3xl font-extrabold tracking-tight text-marinho lg:text-[32px]"
            style={{ '--atraso': '150ms' }}
          >
            O que você vê no mapa?
          </h2>

          <ul>

            {informacoes.map((informacao, indice) => {
              const Icone = informacao.icone

              return (
                <li
                  key={informacao.titulo}
                  className="revelar group flex items-center gap-5 border-b border-marinho/10 py-4 last:border-b-0"
                  style={{
                    '--atraso': `${300 + indice * 150}ms`,
                  }}
                >

                  <Icone
                    size={30}
                    strokeWidth={1.8}
                    className="shrink-0 transition-transform duration-300 motion-safe:group-hover:scale-115"
                    style={{ color: informacao.cor }}
                    aria-hidden="true"
                  />

                  <span className="text-base font-semibold text-marinho lg:text-lg">
                    {informacao.titulo}
                  </span>

                </li>
              )
            })}

          </ul>

        </div>

      </div>

    </section>
  )
}

export default InformacoesMapa
