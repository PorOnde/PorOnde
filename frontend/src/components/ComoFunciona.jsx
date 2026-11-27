
import { useEffect, useRef, useState } from 'react'

// Ícone de localização
function IconeLocalizacao() {
  return (
    <svg
      viewBox="0 0 48 48"
      width="38"
      height="38"
      className="icone-localizacao"
      aria-hidden="true"
    >
      <path
        d="M24 43S9 28 9 19a15 15 0 0 1 30 0c0 9-15 24-15 24Z"
        fill="#16834B"
      />
      <circle cx="24" cy="19" r="6" fill="white" />
    </svg>
  )
}

// Ícone de trajeto inspirado na identidade do PorOnde?
function IconeRota() {
  return (
    <svg
      viewBox="0 0 48 48"
      width="38"
      height="38"
      aria-hidden="true"
    >
      <path
        d="M9 37C28 41 13 17 30 20Q42 23 38 9"
        fill="none"
        stroke="#0A2940"
        strokeWidth="5"
        strokeLinecap="round"
      />

      <circle
        cx="9"
        cy="37"
        r="6"
        fill="#48A85C"
        stroke="#0A2940"
        strokeWidth="3"
      />

      <circle
        cx="38"
        cy="9"
        r="6"
        fill="#FFC107"
        stroke="#0A2940"
        strokeWidth="3"
      />
    </svg>
  )
}

// Velocímetro com ponteiro independente
function IconePontuacao() {
  return (
    <svg
      viewBox="0 0 48 48"
      width="38"
      height="38"
      aria-hidden="true"
    >
      <path
        d="M5 36a20 20 0 1 1 38 0"
        fill="none"
        stroke="#0A2940"
        strokeWidth="4"
        strokeLinecap="round"
      />

      <path
        className="ponteiro-pontuacao"
        d="M24 31L36 17"
        stroke="#16834B"
        strokeWidth="5"
        strokeLinecap="round"
      />

      <circle cx="24" cy="31" r="3" fill="#16834B" />
    </svg>
  )
}

const etapas = [
  {
    titulo: 'Defina seu trajeto',
    descricao: 'Informe origem e destino.',
    icone: IconeLocalizacao,
  },
  {
    titulo: 'Compare as opções',
    descricao: 'Veja as rotas lado a lado.',
    icone: IconeRota,
  },
  {
    titulo: 'Entenda a pontuação',
    descricao: 'Veja o que entrou na nota.',
    icone: IconePontuacao,
  },
]

function ComoFunciona() {
  const secaoRef = useRef(null)
  const [visivel, setVisivel] = useState(false)

  // Inicia a animação quando a seção entra na tela
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
  threshold: 0,
  rootMargin: '0px 0px -20% 0px',
}
    )

    observador.observe(secao)

    return () => observador.disconnect()
  }, [])

  return (
    <section
      ref={secaoRef}
      id="como-funciona"
      className={`relative overflow-hidden bg-fundo px-6 py-16 lg:px-10 lg:py-20 ${
        visivel ? 'secao-visivel' : ''
      }`}
    >
      <div className="mx-auto max-w-6xl">

        {/* Título com animação */}
        <h2
          className="revelar mb-10 text-3xl font-extrabold tracking-tight text-marinho md:text-4xl"
          style={{ '--atraso': '0ms' }}
        >
          Como{' '}

          <span className="titulo-funciona relative inline-block text-verde-escuro">
            funciona?
          </span>
        </h2>

        {/* Etapas */}
        <div className="grid grid-cols-1 gap-7 md:grid-cols-3 md:gap-0">

          {etapas.map((etapa, indice) => {
            const Icone = etapa.icone

            return (
              <div
                key={etapa.titulo}
                className={`revelar etapa-funciona flex items-center gap-5 ${
                  indice !== 0
                    ? 'md:border-l md:border-marinho/10 md:pl-7'
                    : ''
                }`}
                style={{
                  '--atraso': `${150 + indice * 250}ms`,
                }}
              >

                {/* Ícone personalizado */}
                <div className="simbolo-funciona flex h-[68px] w-[68px] shrink-0 items-center justify-center rounded-2xl border border-white bg-white shadow-sm">
                  <Icone />
                </div>

                {/* Texto */}
                <div>
                  <h3 className="text-base font-extrabold text-marinho lg:text-lg">
                    {etapa.titulo}
                  </h3>

                  <p className="mt-1 text-sm leading-relaxed text-marinho/70">
                    {etapa.descricao}
                  </p>
                </div>

              </div>
            )
          })}

        </div>

        <div className="mt-12 h-px w-full bg-marinho/10" />

      </div>
    </section>
  )
}

export default ComoFunciona
