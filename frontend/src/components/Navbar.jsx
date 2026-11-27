
import { NavLink, Link, useLocation } from 'react-router-dom'
import { MapPin } from 'lucide-react'
import logo from '../assets/logo_poronde.png'

// Páginas da nossa plataforma
const paginas = [
  { nome: 'Início', caminho: '/' },
  { nome: 'Trajeto', caminho: '/trajeto' },
  { nome: 'Nossa pesquisa', caminho: '/pesquisa' },
  { nome: 'Sobre nós', caminho: '/sobre' },
]

function Navbar() {
  const { pathname } = useLocation()
  const inicio = pathname === '/'

  return (
    <header
      className={`z-50 w-full ${
        inicio
          ? 'absolute inset-x-0 top-0 bg-transparent'
          : 'sticky top-0 border-b border-gray-200 bg-fundo'
      }`}
    >

      <nav className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-3 lg:px-10">

        {/* Logo oficial */}
        <Link to="/" aria-label="PorOnde? - Página inicial">
          <img
            src={logo}
            alt="PorOnde?"
            className="h-12 w-auto object-contain lg:h-14"
          />
        </Link>

        {/* Links de navegação */}
        <div className="flex w-full flex-wrap items-center justify-center gap-x-6 gap-y-2 md:w-auto lg:gap-10">

          {paginas.map((pagina) => (
            <NavLink
              key={pagina.caminho}
              to={pagina.caminho}
              end={pagina.caminho === '/'}
              className={({ isActive }) =>
                `flex items-center gap-2 border-b-[3px] py-3 text-sm transition-colors lg:text-base ${
                  isActive
                    ? 'border-verde-escuro font-bold text-verde-escuro'
                    : 'border-transparent font-medium text-marinho hover:text-verde-escuro'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <MapPin
                    size={21}
                    className={
                      isActive
                        ? 'text-verde-escuro'
                        : 'text-marinho/45'
                    }
                  />

                  {pagina.nome}
                </>
              )}
            </NavLink>
          ))}

        </div>
      </nav>
    </header>
  )
}

export default Navbar
