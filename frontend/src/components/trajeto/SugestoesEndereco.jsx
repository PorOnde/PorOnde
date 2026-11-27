import { useEffect, useState } from 'react'
import { sugerirEnderecos } from '../../services/api'

// A lista fica abaixo do formulário existente; não altera seus campos nem seu visual.
export default function SugestoesEndereco({ campo, texto, onEscolher, carregando }) {
  const [itens, setItens] = useState([])
  const [erro, setErro] = useState(false)
  useEffect(() => {
    setItens([])
    setErro(false)
    if (!campo || carregando || texto.trim().length < 2 || /\d/.test(texto)) return
    const controle = new AbortController()
    const espera = setTimeout(async () => {
      try {
        const resultado = await sugerirEnderecos(texto, controle.signal)
        if (!controle.signal.aborted) setItens(resultado.filter(n => n.toLowerCase() !== texto.trim().toLowerCase()))
      } catch {
        if (!controle.signal.aborted) setErro(true)
      }
    }, 300)
    return () => { clearTimeout(espera); controle.abort() }
  }, [campo, texto, carregando])
  if (!campo || carregando || (!itens.length && !erro)) return null
  return (
    <div className="mt-2 rounded-xl border border-marinho/15 bg-white p-3 text-sm text-marinho">
      <p className="font-bold text-xs">Sugestões de {campo === 'origem' ? 'origem' : 'destino'}</p>
      {erro ? <p className="mt-1 text-xs">Sugestões indisponíveis. Você ainda pode pesquisar pelo endereço.</p> : (
        <ul className="mt-1 divide-y divide-marinho/10">
          {itens.map(nome => <li key={nome}><button type="button" className="w-full py-2 text-left hover:text-verde-escuro focus-visible:outline-2" onClick={() => onEscolher(nome)}>{nome}</button></li>)}
        </ul>
      )}
      <p className="mt-1 text-xs text-marinho/60">Nomes cadastrados no piloto; confirme a rua e o número na busca.</p>
    </div>
  )
}
