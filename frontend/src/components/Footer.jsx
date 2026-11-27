
import { Link } from 'react-router-dom'
import { MapPin } from 'lucide-react'
import logo from '../assets/logo_poronde.png'

const paginas = [
  { nome: 'Início', caminho: '/' },
  { nome: 'Trajeto', caminho: '/trajeto' },
  { nome: 'Nossa pesquisa', caminho: '/pesquisa' },
  { nome: 'Sobre nós', caminho: '/sobre' },
]

function Footer() {
  return (
    <footer className="overflow-hidden">

      {/* Ondas decorativas animadas */}
      <div
        className="relative h-10 overflow-hidden bg-fundo md:h-14"
        aria-hidden="true"
      >
        <svg
          viewBox="0 0 1440 150"
          preserveAspectRatio="none"
          className="absolute inset-0 h-full w-full"
        >
          <path
            className="onda-footer-verde"
            d="M-100 150 C250 180 500 120 800 65 S1250 -20 1540 45 V160 H-100Z"
            fill="#16834B"
          />

          <path
            className="onda-footer-marinho"
            d="M-100 100 C200 -30 450 30 750 95 S1250 30 1540 80 V160 H-100Z"
            fill="#0A2940"
          />
        </svg>
      </div>

      {/* Conteúdo compacto */}
      <div className="bg-marinho px-6 pb-3 pt-4 text-white lg:px-10">

        <div className="mx-auto max-w-6xl">

          <div className="grid gap-5 pb-4 md:grid-cols-[1fr_1fr_1fr] md:gap-8">

            {/* Identidade visual */}
            <div>
              <Link to="/" aria-label="PorOnde? - Início">
                <img
                  src={logo}
                  alt="PorOnde?"
                  className="h-12 w-auto object-contain brightness-0 invert"
                />
              </Link>

              <p className="mt-1 text-xs text-white/75">
                Seu caminho com mais contexto.
              </p>

              <div className="mt-2 flex gap-1.5" aria-hidden="true">
                <span className="h-2 w-2 rounded-full bg-verde" />
                <span className="h-2 w-2 rounded-full bg-amarelo" />
                <span className="h-2 w-2 rounded-full bg-vermelho" />
              </div>
            </div>

            {/* Navegação */}
            <div>
              <h3 className="mb-2 text-sm font-bold">
                Explore
              </h3>

              <ul className="grid grid-cols-2 gap-x-3 gap-y-2">

                {paginas.map((pagina) => (
                  <li key={pagina.caminho}>
                    <Link
                      to={pagina.caminho}
                      className="text-xs text-white/75 transition-colors hover:text-white"
                    >
                      {pagina.nome}
                    </Link>
                  </li>
                ))}

              </ul>
            </div>

            {/* Área de atuação */}
            <div>
              <h3 className="mb-2 text-sm font-bold">
                Nossa área de atuação
              </h3>

              <div className="flex items-center gap-2">
                <MapPin
                  size={16}
                  className="shrink-0 text-verde"
                />

                <span className="text-xs text-white/80">
                  Vila Mariana, São Paulo
                </span>
              </div>

              <p className="mt-2 max-w-xs text-xs leading-relaxed text-white/65">
                O Score de Contexto apoia sua decisão,
                mas não garante segurança.
              </p>
            </div>

          </div>

          {/* Direitos autorais */}
          <div className="border-t border-white/15 pt-3 text-center">
            <p className="text-xs text-white/70">
              © 2026 PorOnde? Todos os direitos reservados.
            </p>
          </div>

        </div>
      </div>

    </footer>
  )
}

export default Footer
