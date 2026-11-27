
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapPin, ArrowRight } from 'lucide-react'
import logo from '../assets/logo_poronde.png'
import ComoFunciona from '../components/ComoFunciona'
import InformacoesMapa from '../components/InformacoesMapa'

function Home() {
  const [origem, setOrigem] = useState('')
  const [destino, setDestino] = useState('')
  const navigate = useNavigate()

  function planejarTrajeto(evento) {
    evento.preventDefault()

    if (!origem.trim() || !destino.trim()) return

    navigate('/trajeto', {
      state: {
        origem: origem.trim(),
        destino: destino.trim(),
      },
    })
  }

  return (
    <main>
      <section className="relative isolate overflow-hidden bg-fundo pt-40 sm:pt-32 lg:pt-20">

        {/* FUNDO ILUSTRATIVO DO MAPA */}
        <svg
          className="pointer-events-none absolute inset-0 -z-20 h-full w-full"
          viewBox="0 0 1440 640"
          preserveAspectRatio="xMidYMid slice"
          aria-hidden="true"
        >
          <rect width="1440" height="640" fill="#EAE7E1" />

          {/* Áreas verdes */}
          <path
            d="M0 0 H210 Q180 85 110 100 Q40 110 0 170Z"
            fill="#DCEAD5"
          />

          <path
            d="M1440 445 Q1300 445 1250 530 Q1190 610 1100 640 H1440Z"
            fill="#DCEAD5"
          />

          {/* Ruas do mapa */}
          <g
            stroke="#FFFFFF"
            strokeWidth="5"
            fill="none"
            strokeLinejoin="round"
          >
            <path d="M-40 120 L220 185 L450 240 L700 175 L980 220 L1480 350" />
            <path d="M-40 275 L260 350 L500 300 L820 390 L1480 510" />
            <path d="M-40 470 L330 540 L680 450 L1050 560 L1480 610" />
            <path d="M100 -40 L55 250 L150 480 L110 680" />
            <path d="M300 -40 L240 185 L280 380 L250 680" />
            <path d="M490 -40 L450 240 L500 300 L430 680" />
            <path d="M730 -40 L700 175 L680 450 L710 680" />
            <path d="M990 -40 L980 220 L910 430 L940 680" />
            <path d="M1190 -40 L1100 250 L1180 440 L1140 680" />
            <path d="M1390 -40 L1300 260 L1380 510 L1340 680" />
            <path d="M0 60 L380 135 L760 60 L1440 160" />
            <path d="M80 640 L370 430 L570 510 L850 280 L1440 80" />

            {/* Ruas que acompanham os trajetos animados */}

<path
  d="M870 85 C1040 10 1060 180 1230 170 C1450 150 1440 420 1270 490 Q1190 525 1160 590"
  strokeWidth="15"
  strokeLinecap="round"
/>

<path
  d="M260 295 C30 330 15 485 155 520 Q270 550 340 640"
  strokeWidth="15"
  strokeLinecap="round"
/>
          </g>
        </svg>

        {/* Suavização do mapa */}
        <div
          className="pointer-events-none absolute inset-0 -z-10"
          style={{
            background:
              'radial-gradient(ellipse at center, rgba(248,247,244,0.55) 22%, rgba(248,247,244,0.12) 100%)',
          }}
        />

        {/* LINHAS ANIMADAS */}
        <svg
          className="pointer-events-none absolute inset-0 -z-10 hidden h-full w-full xl:block"
          viewBox="0 0 1440 640"
          preserveAspectRatio="xMidYMid slice"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="linha-direita">
              <stop offset="0%" stopColor="#0A2940" stopOpacity="0" />
              <stop offset="30%" stopColor="#0A2940" />
              <stop offset="85%" stopColor="#0A2940" />
              <stop offset="100%" stopColor="#0A2940" stopOpacity="0" />
            </linearGradient>

            <linearGradient id="linha-esquerda">
              <stop offset="0%" stopColor="#0A2940" stopOpacity="0" />
              <stop offset="30%" stopColor="#0A2940" />
              <stop offset="85%" stopColor="#0A2940" />
              <stop offset="100%" stopColor="#0A2940" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Linha direita */}
          <path
            d="M870 85 C1040 10 1060 180 1230 170 C1450 150 1440 420 1270 490 Q1190 525 1160 590"
            fill="none"
            stroke="url(#linha-direita)"
            strokeWidth="7"
            strokeLinecap="round"
          />

          {/* Linha esquerda */}
          <path
            d="M260 295 C30 330 15 485 155 520 Q270 550 340 640"
            fill="none"
            stroke="url(#linha-esquerda)"
            strokeWidth="7"
            strokeLinecap="round"
          />

          {/* Ponto em movimento na linha direita */}
          <path
            d="M870 85 C1040 10 1060 180 1230 170 C1450 150 1440 420 1270 490 Q1190 525 1160 590"
            fill="none"
            stroke="#FFC107"
            strokeWidth="7"
            strokeLinecap="round"
            pathLength="100"
            className="trajeto-animado"
          />

          {/* Ponto em movimento na linha esquerda */}
          <path
            d="M260 295 C30 330 15 485 155 520 Q270 550 340 640"
            fill="none"
            stroke="#EF4444"
            strokeWidth="7"
            strokeLinecap="round"
            pathLength="100"
            className="trajeto-animado trajeto-animado-secundario"
          />

          {/* Pontos fixos */}
          <circle
            cx="1230"
            cy="170"
            r="10"
            fill="#FFC107"
            stroke="#0A2940"
            strokeWidth="5"
          />

          <circle
            cx="155"
            cy="520"
            r="10"
            fill="#EF4444"
            stroke="#0A2940"
            strokeWidth="5"
          />

          {/* Iluminação */}
          <g transform="translate(1145 105)">
            <rect
              width="170"
              height="46"
              rx="12"
              fill="white"
              stroke="#E8E6E1"
            />
            <g
              transform="translate(13 10)"
              fill="none"
              stroke="#D9A400"
              strokeWidth="2"
              strokeLinecap="round"
            >
              <path d="M9 0 A9 9 0 0 1 18 9 C18 13 13 15 13 19 H5 C5 15 0 13 0 9 A9 9 0 0 1 9 0Z" />
              <path d="M6 23 H12" />
            </g>
            <text
              x="45"
              y="29"
              fontSize="15"
              fontWeight="600"
              fill="#0A2940"
            >
              Iluminação
            </text>
          </g>

          {/* Bloqueios */}
          <g transform="translate(80 450)">
            <rect
              width="150"
              height="46"
              rx="12"
              fill="white"
              stroke="#E8E6E1"
            />
            <g
              transform="translate(13 10)"
              fill="none"
              stroke="#EF4444"
              strokeWidth="2"
              strokeLinejoin="round"
            >
              <rect x="0" y="3" width="22" height="11" rx="2" />
              <path d="M3 14 V25 M19 14 V25 M2 3 L10 14 M11 3 L19 14" />
            </g>
            <text
              x="44"
              y="29"
              fontSize="15"
              fontWeight="600"
              fill="#0A2940"
            >
              Bloqueios
            </text>
          </g>
        </svg>

        {/* CONTEÚDO PRINCIPAL */}
        <div className="relative mx-auto flex min-h-[560px] max-w-6xl flex-col items-center justify-center px-5 py-14 text-center lg:min-h-[600px]">

          {/* Símbolo da logo sem cortar o desenho */}
          <svg
            viewBox="70 110 730 460"
            className="mb-5 h-auto w-36 sm:w-44 lg:w-48"
            aria-hidden="true"
          >
            <image
              href={logo}
              x="0"
              y="0"
              width="2172"
              height="724"
            />
          </svg>

          {/* Título */}
          <h1 className="hero-titulo">
  <span className="hero-linha hero-linha-1">
    Não é só chegar.
  </span>

  <span className="hero-linha hero-linha-2">
    É saber <span className="hero-destaque">por onde</span> ir.
  </span>
</h1>

          {/* Subtítulo */}
          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-marinho/75 lg:text-lg">
            Planeje rotas considerando o que importa no seu trajeto.
          </p>

          {/* FORMULÁRIO */}
          <form
            onSubmit={planejarTrajeto}
            className="mx-auto mt-8 flex w-full max-w-[820px] flex-col items-center gap-3 rounded-2xl border border-white bg-white/95 p-4 shadow-[0_8px_35px_rgba(10,41,64,0.08)] md:flex-row"
          >
            <label className="flex w-full min-w-0 flex-1 items-center gap-3 rounded-xl border border-gray-300 px-4 py-3 focus-within:border-verde-escuro">
              <MapPin
                size={21}
                className="shrink-0 text-verde-escuro"
              />

              <input
                type="text"
                placeholder="Origem"
                aria-label="Origem"
                value={origem}
                onChange={(evento) => setOrigem(evento.target.value)}
                className="w-full min-w-0 bg-transparent text-sm outline-none"
                required
              />
            </label>

            <ArrowRight
              size={19}
              className="hidden shrink-0 text-gray-400 md:block"
            />

            <label className="flex w-full min-w-0 flex-1 items-center gap-3 rounded-xl border border-gray-300 px-4 py-3 focus-within:border-vermelho">
              <MapPin
                size={21}
                className="shrink-0 text-vermelho"
              />

              <input
                type="text"
                placeholder="Destino"
                aria-label="Destino"
                value={destino}
                onChange={(evento) => setDestino(evento.target.value)}
                className="w-full min-w-0 bg-transparent text-sm outline-none"
                required
              />
            </label>

            <button
              type="submit"
              className="flex w-full shrink-0 items-center justify-center gap-3 rounded-xl bg-verde-escuro px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-[#106B3D] md:w-auto"
            >
              Planejar trajeto
            </button>
          </form>

          <p className="mt-4 text-xs font-medium text-marinho/70">
            Disponível inicialmente na Vila Mariana, São Paulo.
          </p>

        </div>
      </section>

      <ComoFunciona />

      <InformacoesMapa />

    </main>
  )
}

export default Home
