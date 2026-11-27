import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import {
  Target,
  Eye,
  HeartHandshake,
  ArrowRight,
  MapPin,
  Code2,
  Database,
  Map,
  GitBranch,
  ChartNoAxesCombined,
} from 'lucide-react'

import {
  FaLinkedin as Linkedin,
  FaGithub as Github,
} from 'react-icons/fa'

// ========================================
// MISSÃO, VISÃO E VALORES
// ========================================

const proposito = [
  {
    numero: '01',
    titulo: 'Missão',
    descricao:
      'Oferecer informações sobre o contexto urbano para apoiar escolhas mais conscientes e informadas nos deslocamentos a pé.',
    icone: Target,
    cor: '#16834B',
  },
  {
    numero: '02',
    titulo: 'Visão',
    descricao:
      'Contribuir para uma mobilidade urbana mais informada, acessível e colaborativa, ampliando o conhecimento das pessoas sobre seus caminhos.',
    icone: Eye,
    cor: '#B88A00',
  },
  {
    numero: '03',
    titulo: 'Valores',
    valores: [
      'Transparência',
      'Responsabilidade',
      'Inclusão',
      'Autonomia',
      'Colaboração',
    ],
    icone: HeartHandshake,
    cor: '#EF4444',
  },
]

// ========================================
// INTEGRANTES
// ========================================

const equipe = [
  {
    nome: 'Emilly Barauna',
    inicial: 'E',
    foto: 'emilly.jpg',
    linkedin: 'https://www.linkedin.com/in/emilly-barauna/',
    github: 'https://github.com/Emilly-Barauna',
    cor: '#48A85C',
  },
  {
    nome: 'Larissa Araujo',
    inicial: 'L',
    foto: 'larissa.jpg',
    linkedin: 'https://www.linkedin.com/in/larissa-t-araujo/',
    github: 'https://github.com/larissataraujo',
    cor: '#FFC107',
  },
  {
    nome: 'Letícia Pereira',
    inicial: 'L',
    foto: 'leticia.jpg',
    linkedin: 'https://www.linkedin.com/in/letícia-pereira-7b766b219?utm_source=share_via&utm_content=profile&utm_medium=member_android',
    github: 'https://github.com/Leticia16Ps',
    cor: '#EF4444',
  },
]

// ========================================
// TECNOLOGIAS
// ========================================


const baseLogo = 'https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons'

const tecnologias = [
  {
    nome: 'React',
    descricao: 'Interface da plataforma',
    logo: `${baseLogo}/react/react-original.svg`,
  },
  {
    nome: 'JavaScript',
    descricao: 'Interatividade do front-end',
    logo: `${baseLogo}/javascript/javascript-original.svg`,
  },
  {
    nome: 'Python',
    descricao: 'Processamento e lógica do sistema',
    logo: `${baseLogo}/python/python-original.svg`,
  },
  {
    nome: 'FastAPI',
    descricao: 'Comunicação entre frontend e backend',
    logo: `${baseLogo}/fastapi/fastapi-original.svg`,
  },
  {
    nome: 'Supabase',
    descricao: 'Gerenciamento dos relatos e votos',
    logo: `${baseLogo}/supabase/supabase-original.svg`,
  },
  {
    nome: 'PostgreSQL',
    descricao: 'Armazenamento relacional dos dados',
    logo: `${baseLogo}/postgresql/postgresql-original.svg`,
  },
  {
    nome: 'Pandas',
    descricao: 'Tratamento e análise dos dados',
    logo: `${baseLogo}/pandas/pandas-original.svg`,
    fundoClaro: true,
  },
  {
    nome: 'GeoPandas',
    descricao: 'Manipulação e análise de dados geográficos',
    logo: 'https://raw.githubusercontent.com/geopandas/geopandas/main/doc/source/_static/logo/geopandas_icon_green.svg',
  },
  {
    nome: 'OSMnx',
    descricao: 'Obtenção e modelagem da malha viária',
    logo: null,
  },
  {
    nome: 'React Leaflet',
    descricao: 'Mapa geográfico interativo',
    logo: 'https://react-leaflet.js.org/img/logo.svg',
  },
]


const linhaSobre =
  'M-30 110 H100 Q130 110 130 80 V45 Q130 20 160 20 H300 Q330 20 330 50 V80 Q330 110 360 110 H560 Q590 110 590 80 V45 Q590 20 620 20 H800 Q830 20 830 50 V80 Q830 110 860 110 H1040 Q1070 110 1070 80 V45 Q1070 20 1100 20 H1470'

// ========================================
// COMPONENTE DOS LINKS SOCIAIS
// ========================================

function LinkSocial({ url, nome, icone: Icone, integrante }) {
  if (!url) {
    return (
      <span
        title={`${nome} ainda não cadastrado`}
        className="flex h-10 w-10 items-center justify-center rounded-full border border-marinho/10 text-marinho/30"
      >
        <Icone size={18} aria-hidden="true" />
        <span className="sr-only">
          {nome} ainda não cadastrado
        </span>
      </span>
    )
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${nome} de ${integrante}`}
      title={`${nome} de ${integrante}`}
      className="sobre-social flex h-10 w-10 items-center justify-center rounded-full border border-marinho/15 text-marinho hover:border-marinho hover:bg-marinho hover:text-white"
    >
      <Icone size={18} aria-hidden="true" />
    </a>
  )
}

// ========================================
// COMPONENTE DE CADA INTEGRANTE
// ========================================

function Integrante({ pessoa, indice }) {
  const [fotoDisponivel, setFotoDisponivel] = useState(true)

  return (
    <article
      className="sobre-revelar sobre-integrante group"
      style={{
        '--atraso-sobre': `${indice * 180}ms`,
        '--cor-integrante': pessoa.cor,
      }}
    >

      {/* Fotografia */}
      <div className="relative aspect-[4/4.5] overflow-hidden rounded-2xl bg-marinho/5">

        {fotoDisponivel ? (
          <img
            src={`${import.meta.env.BASE_URL}equipe/${pessoa.foto}`}
            alt={`Foto de ${pessoa.nome}`}
            onError={() => setFotoDisponivel(false)}
            loading="lazy"
            className="sobre-foto h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <span className="text-7xl font-extrabold text-marinho/20">
              {pessoa.inicial}
            </span>
          </div>
        )}

        {/* Número da integrante */}
        <span className="absolute left-4 top-4 rounded-md bg-white/90 px-2.5 py-1.5 text-xs font-bold text-marinho">
          {String(indice + 1).padStart(2, '0')}
        </span>

        {/* Linha colorida */}
        <div className="sobre-linha-foto absolute inset-x-0 bottom-0 h-1.5" />

      </div>

      {/* Nome */}
      <div className="pt-5 text-center">

        <h3 className="text-2xl font-extrabold tracking-tight text-marinho">
          {pessoa.nome}
        </h3>

        <p className="mt-1 text-sm text-marinho/65">
          {pessoa.funcao}
        </p>

        {/* Redes sociais */}
        <div className="mt-4 flex justify-center gap-3">

          <LinkSocial
            url={pessoa.linkedin}
            nome="LinkedIn"
            icone={Linkedin}
            integrante={pessoa.nome}
          />

          <LinkSocial
            url={pessoa.github}
            nome="GitHub"
            icone={Github}
            integrante={pessoa.nome}
          />

        </div>

      </div>

    </article>
  )
}

// ========================================
// PÁGINA SOBRE NÓS
// ========================================

function Sobre() {
  const paginaRef = useRef(null)

  // Animações durante a rolagem
  useEffect(() => {
    const pagina = paginaRef.current

    if (!pagina) return

    const secoes = pagina.querySelectorAll(
      '[data-sobre-secao]'
    )

    if (!('IntersectionObserver' in window)) {
      return
    }

    const observador = new IntersectionObserver(
      (entradas) => {
        entradas.forEach((entrada) => {
          if (entrada.isIntersecting) {
            entrada.target.classList.add('sobre-visivel')
            observador.unobserve(entrada.target)
          }
        })
      },
      {
        threshold: 0.08,
      }
    )

    pagina.classList.add('sobre-pronto')

    secoes.forEach((secao) => {
      observador.observe(secao)
    })

    return () => {
      observador.disconnect()
      pagina.classList.remove('sobre-pronto')
    }
  }, [])

  return (
    <main ref={paginaRef} className="overflow-hidden bg-fundo">

      {/* ========================================
          ABERTURA
      ======================================== */}

      <section
        data-sobre-secao
        className="relative pb-16 pt-8 lg:pb-24"
      >

        <svg
          viewBox="0 0 1440 140"
          preserveAspectRatio="xMidYMid slice"
          className="h-24 w-full md:h-36"
          aria-hidden="true"
        >

          <path
            d={linhaSobre}
            fill="none"
            stroke="#0A2940"
            strokeWidth="6"
            strokeLinecap="round"
          />

          <path
            d={linhaSobre}
            fill="none"
            stroke="#48A85C"
            strokeWidth="8"
            strokeLinecap="round"
            pathLength="100"
            className="trajeto-animado"
          />

          {[
            { x: 130, cor: '#48A85C' },
            { x: 590, cor: '#FFC107' },
            { x: 1070, cor: '#EF4444' },
          ].map((ponto) => (
            <circle
              key={ponto.x}
              cx={ponto.x}
              cy="80"
              r="10"
              fill={ponto.cor}
              stroke="#0A2940"
              strokeWidth="5"
            />
          ))}

        </svg>

        <div className="mx-auto max-w-6xl px-6 pt-8 text-center">


          <h1
            className="sobre-revelar text-4xl font-extrabold leading-tight tracking-[-0.045em] text-marinho md:text-5xl lg:text-[64px]"
            style={{ '--atraso-sobre': '180ms' }}
          >
            Toda rota tem uma história.

            <span className="mt-2 block text-verde-escuro">
              A nossa começa nas ruas.
            </span>
          </h1>

          <p
            className="sobre-revelar mx-auto mt-6 max-w-2xl text-base leading-relaxed text-marinho/70 lg:text-lg"
            style={{ '--atraso-sobre': '350ms' }}
          >
            Tecnologia para compreender a cidade e
            transformar a maneira como escolhemos
            nossos caminhos.
          </p>

        </div>

      </section>

      
      {/* ========================================
          MISSÃO, VISÃO E VALORES
      ======================================== */}

      <section
        data-sobre-secao
        className="overflow-hidden border-y border-marinho/5 bg-white px-6 py-14 lg:px-10 lg:py-20"
      >

        <div className="mx-auto max-w-6xl">

          {/* Título */}
          <div className="sobre-revelar text-center">

            <h2 className="text-3xl font-extrabold tracking-tight text-marinho md:text-4xl">
              Missão, visão e{' '}
              <span className="text-verde-escuro">
                valores.
              </span>
            </h2>

            <p className="mt-3 text-sm leading-relaxed text-marinho/65 md:text-base">
              O propósito que orienta cada passo do PorOnde?
            </p>

          </div>

          {/* Estrutura do trajeto */}
          <div className="relative mt-12">

            {/* Linha que conecta os três princípios */}
            <div
              className="absolute left-[16.66%] right-[16.66%] top-[52px] hidden md:block"
              aria-hidden="true"
            >
              <svg
                viewBox="0 0 1000 10"
                preserveAspectRatio="none"
                className="h-2.5 w-full"
              >
                <path
                  d="M0 5 H1000"
                  fill="none"
                  stroke="#DCE4DD"
                  strokeWidth="2"
                  strokeDasharray="7 7"
                />

                <path
                  d="M0 5 H1000"
                  fill="none"
                  stroke="#16834B"
                  strokeWidth="2"
                  pathLength="100"
                  className="mvv-linha-trajeto"
                />
              </svg>
            </div>

            {/* Missão, visão e valores */}
            <div className="relative grid gap-12 md:grid-cols-3 md:gap-10">

              {proposito.map((item, indice) => {
                const Icone = item.icone

                const frases = [
                  'Informar para transformar.',
                  'Uma cidade mais conectada.',
                  'Pessoas em primeiro lugar.',
                ]

                return (
                  <article
                    key={item.titulo}
                    className="sobre-revelar mvv-item group flex flex-col items-center text-center"
                    style={{
                      '--atraso-sobre': `${200 + indice * 250}ms`,
                      '--mvv-cor': item.cor,
                    }}
                  >

                    {/* Círculo animado */}
                    <div className="mvv-circulo-externo relative flex h-28 w-28 items-center justify-center rounded-full">

                      <div className="mvv-circulo-interno flex h-[82px] w-[82px] items-center justify-center rounded-full bg-white">

                        <Icone
                          size={38}
                          strokeWidth={1.6}
                          className="mvv-icone"
                          style={{ color: item.cor }}
                          aria-hidden="true"
                        />

                      </div>

                    </div>

                    {/* Nome */}
                    <h3
                      className="mt-6 text-2xl font-extrabold"
                      style={{ color: item.cor }}
                    >
                      {item.titulo}
                    </h3>

                    {/* Frase de destaque */}
                    <p className="mt-3 text-base font-bold text-marinho">
                      {frases[indice]}
                    </p>

                    {/* Descrição */}
                    {item.descricao && (
                      <p className="mt-3 max-w-xs text-sm leading-[1.8] text-marinho/70">
                        {item.descricao}
                      </p>
                    )}

                    {/* Valores sem quadradinhos */}
                    {item.valores && (
                      <p className="mt-3 max-w-xs text-sm leading-[1.8] text-marinho/70">
                        Transparência, responsabilidade,
                        inclusão, autonomia e colaboração.
                      </p>
                    )}

                  </article>
                )
              })}

            </div>

          </div>

        </div>

      </section>



      {/* ========================================
          NOSSA EQUIPE
      ======================================== */}

      <section
        data-sobre-secao
        className="px-6 py-16 lg:px-10 lg:py-24"
      >

        <div className="mx-auto max-w-5xl">

          <div className="sobre-revelar text-center">


            <h2 className="text-3xl font-extrabold tracking-tight text-marinho md:text-4xl">
              Quem faz o{' '}
              <span className="text-verde-escuro">
                PorOnde?
              </span>
            </h2>

            <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-marinho/70 md:text-base">
              Três estudantes unidas pela tecnologia,
              pela análise de dados e pela vontade de
              compreender os desafios da mobilidade urbana.
            </p>

          </div>

          <div className="mt-10 grid gap-8 sm:grid-cols-3 lg:gap-12">

            {equipe.map((pessoa, indice) => (
              <Integrante
                key={pessoa.nome}
                pessoa={pessoa}
                indice={indice}
              />
            ))}

          </div>

        </div>

      </section>

      {/* ========================================
          TECNOLOGIAS UTILIZADAS
      ======================================== */}

      <section
        data-sobre-secao
        className="relative isolate overflow-hidden bg-marinho px-6 py-16 text-white lg:px-10 lg:py-20"
      >

        {/* Fundo decorativo */}
        <div
          className="sobre-grade-tecnologias pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
        />

        <div className="mx-auto max-w-6xl">

          <div className="sobre-revelar text-center">


            <h2 className="text-3xl font-extrabold tracking-tight md:text-4xl">
              Tecnologia que conecta caminhos.
            </h2>

            <p className="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-white/75">
              Da análise dos dados à construção da interface,
              diferentes tecnologias trabalham juntas
              para dar vida ao PorOnde?.
            </p>

          </div>

          <div className="mt-10 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">

            
{tecnologias.map((tecnologia, indice) => (
  <article
    key={tecnologia.nome}
    className="sobre-revelar"
    style={{
      '--atraso-sobre': `${indice * 90}ms`,
    }}
  >
    <div className="sobre-tecnologia group h-full rounded-2xl border border-white/15 bg-white/5 p-5 transition-all duration-300 hover:-translate-y-1 hover:border-white/40 hover:bg-white/10 motion-reduce:transform-none">

      {/* Logotipo da tecnologia */}
      <div className="mb-4 flex h-12 items-center">

        {tecnologia.logo ? (
          <img
            src={tecnologia.logo}
            alt={`Logo ${tecnologia.nome}`}
            className={`h-12 w-12 object-contain ${
              tecnologia.fundoClaro
                ? 'rounded-md bg-white p-1'
                : ''
            }`}
            loading="lazy"
            onError={(evento) => {
              evento.currentTarget.style.display = 'none'
            }}
          />
        ) : (
          <span className="text-xl font-extrabold tracking-tight text-white">
            OSMnx
          </span>
        )}

      </div>

      <h3 className="text-base font-bold text-white">
        {tecnologia.nome}
      </h3>

      <p className="mt-2 text-sm leading-relaxed text-white/70">
        {tecnologia.descricao}
      </p>

    </div>
  </article>
))}


          </div>

          {/* Histórico de desenvolvimento */}
          <div
            className="sobre-revelar mt-8 border-t border-white/15 pt-6 text-center"
            style={{ '--atraso-sobre': '300ms' }}
          >

          </div>

        </div>

      </section>

      {/* ========================================
          ÁREA DE ATUAÇÃO
      ======================================== */}

      <section
        data-sobre-secao
        className="px-6 py-14 lg:px-10"
      >

        <div className="sobre-revelar mx-auto flex max-w-5xl flex-col items-center gap-7 text-center md:flex-row md:text-left">

          <div
            className="sobre-localizacao relative flex h-28 w-28 shrink-0 items-center justify-center rounded-full bg-verde-escuro/10"
            aria-hidden="true"
          >
            <MapPin
              size={54}
              strokeWidth={1.5}
              className="text-verde-escuro"
            />
          </div>

          <div>


            <h2 className="text-3xl font-extrabold tracking-tight text-marinho">
              Começamos pela Vila Mariana.
            </h2>

            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-marinho/70">
              Escolhemos um recorte da cidade de São Paulo
              para desenvolver e testar nossa proposta,
              considerando os dados disponíveis e as
              características da região.
            </p>

          </div>

        </div>

      </section>

      {/* ========================================
          ENCERRAMENTO
      ======================================== */}

      <section
        data-sobre-secao
        className="px-6 pb-12"
      >

        <div className="sobre-revelar mx-auto max-w-6xl border-t border-marinho/10 pt-10 text-center">

          <div className="mb-5 flex justify-center gap-2">
            {['#48A85C', '#FFC107', '#EF4444'].map(
              (cor, indice) => (
                <span
                  key={cor}
                  className="sobre-ponto-final h-3 w-3 rounded-full"
                  style={{
                    backgroundColor: cor,
                    animationDelay: `${indice * 180}ms`,
                  }}
                />
              )
            )}
          </div>

          <h2 className="text-3xl font-extrabold tracking-tight text-marinho">
            A cidade é de todos.

            <span className="mt-1 block text-verde-escuro">
              A escolha do caminho é sua.
            </span>
          </h2>

          <Link
            to="/trajeto"
            className="group mx-auto mt-6 inline-flex items-center gap-3 rounded-xl bg-verde-escuro px-6 py-3 text-sm font-bold text-white transition-colors hover:bg-[#106B3D]"
          >
            Explore seu trajeto

            <ArrowRight
              size={19}
              className="transition-transform motion-safe:group-hover:translate-x-1"
            />
          </Link>

          <p className="mx-auto mt-5 max-w-lg text-xs leading-relaxed text-marinho/60">
            O PorOnde? oferece informações de contexto
            para apoiar suas decisões, mas não garante
            segurança durante os deslocamentos.
          </p>

        </div>

      </section>

    </main>
  )
}

export default Sobre
