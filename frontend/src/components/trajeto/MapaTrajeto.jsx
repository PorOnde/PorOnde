import { Fragment, useEffect } from 'react'
import { divIcon } from 'leaflet'

import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Marker,
  Tooltip,
  Popup,
  useMapEvents,
  Polyline,
  useMap,
} from 'react-leaflet'

import 'leaflet/dist/leaflet.css'

const centroVilaMariana = [-23.5895, -46.6345]


function criarMarcadorEndereco(nome) {
  const origem = nome === 'Origem'
  const cor = origem ? '#387B96' : '#0A2940'

  const simbolo = origem
    ? `<circle cx="22" cy="19" r="6" fill="none"
         stroke="white" stroke-width="2"/>
       <circle cx="22" cy="19" r="2" fill="white"/>`
    : `<path d="M19 26V12H28L25 16L28 20H19"
         fill="none" stroke="white" stroke-width="2"
         stroke-linejoin="round" stroke-linecap="round"/>`

  return divIcon({
    className: 'marcador-endereco',
    iconSize: [112, 48],
    iconAnchor: [56, 44],
    html: `
      <svg width="112" height="48" viewBox="0 0 112 48"
        style="filter: drop-shadow(0 2px 3px #00000025)">
        
        <path
          d="M20 3H92A16 16 0 0 1 92 35H63L56 44L49 35H20A16 16 0 0 1 20 3Z"
          fill="white"
          stroke="${cor}"
          stroke-width="1.5"
        />

        <circle cx="22" cy="19" r="12" fill="${cor}"/>

        ${simbolo}

        <text x="40" y="23"
          font-family="Plus Jakarta Sans, sans-serif"
          font-size="12"
          font-weight="700"
          fill="#0A2940">
          ${nome}
        </text>

      </svg>
    `,
  })
}

const iconeOrigem = criarMarcadorEndereco('Origem')
const iconeDestino = criarMarcadorEndereco('Destino')

const estiloPadrao = { cor: '#64748B', traco: null }


/* Ícones dos locais de apoio */

const simbolosApoio = {
  farmacia: `
    <rect x="3" y="8" width="18" height="8" rx="4"
      transform="rotate(-45 12 12)"/>
    <path d="M12 8v8" transform="rotate(-45 12 12)"/>
  `,

  hospital: `
    <path d="M9 4h6v5h5v6h-5v5H9v-5H4V9h5z"/>
  `,

  delegacia: `
    <path d="M12 2 4 6v6c0 5 8 10 8 10s8-5 8-10V6z"/>
    <path d="m8 12 3 3 5-6"/>
  `,

  mercado: `
    <path d="M2 3h3l3 12h12l2-9H6"/>
    <circle cx="9" cy="20" r="1"/>
    <circle cx="19" cy="20" r="1"/>
  `,

  loja: `
    <path d="M3 9 5 3h14l2 6H3"/>
    <path d="M4 13v8h16v-8"/>
    <path d="M9 21v-7h6v7"/>
    <path d="M3 9v2a3 3 0 0 0 6 0
             3 3 0 0 0 6 0
             3 3 0 0 0 6 0V9z"/>
  `,

  clinica: `
    <path d="M4 3v6a6 6 0 0 0 12 0V3"/>
    <path d="M10 15v2a5 5 0 0 0 10 0v-2"/>
    <circle cx="20" cy="12" r="3"/>
  `,

  metro: `
    <rect x="5" y="2" width="14" height="17" rx="4"/>
    <path d="M5 11h14M12 3v8M8 19l-3 3m11-3 3 3"/>
    <circle cx="9" cy="15" r="1"/>
    <circle cx="15" cy="15" r="1"/>
  `,

  posto: `
    <rect x="3" y="3" width="11" height="18" rx="2"/>
    <rect x="6" y="6" width="5" height="5" rx="1"/>
    <path d="M14 13h3v4a2 2 0 0 0 4 0V8l-3-3"/>
  `,

  outro: `
    <path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0z"/>
    <circle cx="12" cy="10" r="3"/>
  `,
}

const estilosApoio = {
  farmacia: { nome: 'Farmácia', cor: '#168B80', fundo: '#E4F3EF' },
  hospital: { nome: 'Hospital', cor: '#D65A66', fundo: '#FCE7E9' },
  delegacia: { nome: 'Delegacia', cor: '#315B96', fundo: '#E7EEF9' },
  mercado: { nome: 'Mercado', cor: '#B57A36', fundo: '#F8EDDB' },
  loja: { nome: 'Loja', cor: '#B57A36', fundo: '#F8EDDB' },
  clinica: { nome: 'Clínica', cor: '#D65A66', fundo: '#FCE7E9' },
  metro: { nome: 'Metrô', cor: '#7955A5', fundo: '#EFE7F7' },
  posto: { nome: 'Posto de combustível', cor: '#7955A5', fundo: '#EFE7F7' },
  outro: { nome: 'Outro local de apoio', cor: '#344E5C', fundo: '#E4E8EB' },
}

const estilosRelato = {
  'Iluminação insuficiente': { cor: '#9C782D', fundo: '#FFF3CD', simbolo: '<path d="M9 18h6m-5 4h4M8 14a6 6 0 1 1 8 0l-1 2h-5zM3 3l18 18"/>' },
  'Obras ou bloqueios': { cor: '#C06A28', fundo: '#FFE7D1', simbolo: '<rect x="3" y="7" width="18" height="9" rx="1"/><path d="m3 7 9 9m0-9 9 9M6 16v5m12-5v5"/>' },
  'Problema na calçada': { cor: '#956B4C', fundo: '#F1E3D6', simbolo: '<path d="M8 3v4m8 10v4M5 9c0-2 6-2 6 0v5c0 2-6 2-6 0zM13 10c0-2 6-2 6 0v5c0 2-6 2-6 0z"/>' },
  'Tumulto ou confusão': { cor: '#89509A', fundo: '#F1E4F5', simbolo: '<circle cx="7" cy="7" r="3"/><circle cx="17" cy="7" r="3"/><path d="M2 20v-3a5 5 0 0 1 10 0v3m0-3a5 5 0 0 1 10 0v3M12 1v3"/>' },
  'Aglomeração comum': { cor: '#587B94', fundo: '#DFEBF4', simbolo: '<circle cx="12" cy="6" r="3"/><path d="M6 21v-4a6 6 0 0 1 12 0v4M5 4a3 3 0 0 0 0 6m14-6a3 3 0 0 1 0 6M2 19v-3a4 4 0 0 1 4-4m16 7v-3a4 4 0 0 0-4-4"/>' },
  'Problema no transporte': { cor: '#4666A4', fundo: '#DFE8FA', simbolo: '<rect x="4" y="3" width="16" height="15" rx="3"/><path d="M4 11h16M8 18v3m8-3v3"/><circle cx="8" cy="15" r="1"/><circle cx="16" cy="15" r="1"/>' },
  'Roubo ou furto relatado': { cor: '#BC4855', fundo: '#FCE0E3', simbolo: '<path d="M12 2 4 6v6c0 5 8 10 8 10s8-5 8-10V6zM12 7v5m0 4h.01"/>' },
  'Alagamento': { cor: '#2387B5', fundo: '#D9EFF8', simbolo: '<path d="M2 7q3-4 5 0t5 0t5 0t5 0M2 12q3-4 5 0t5 0t5 0t5 0M2 17q3-4 5 0t5 0t5 0t5 0"/>' },
  'Outros': { cor: '#65737F', fundo: '#E4E8EB', simbolo: '<path d="M21 11a9 9 0 0 1-9 9H3l2-4a9 9 0 1 1 16-5zM8 11h.01m4 0h.01m4 0h.01"/>' },
}
const estiloRecorrencia = { cor: '#9A3412', fundo: '#FED7AA', simbolo: estilosRelato['Roubo ou furto relatado'].simbolo }
const categoriasContinuidade = ['Iluminação insuficiente', 'Problema na calçada', 'Obras ou bloqueios', 'Tumulto ou confusão']
const cacheIcones = new Map()
const numeroBR = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })

function dadosApoio(tipo) {
  const chave = String(tipo || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim()
  const categoria = Object.hasOwn(estilosApoio, chave) ? chave : 'outro'
  return { ...estilosApoio[categoria], simbolo: simbolosApoio[categoria], categoria }
}

function dadosRelato(categoria) {
  return Object.hasOwn(estilosRelato, categoria) ? estilosRelato[categoria] : estilosRelato.Outros
}

// Apenas desenhos SVG definidos acima entram no HTML dos ícones.
function svgApoio(estilo) {
  return `<svg width="36" height="44" viewBox="0 0 36 44" style="filter:drop-shadow(0 2px 3px #00000025)">
    <path d="M11 2H25Q34 2 34 11V25Q34 34 25 34H24L18 42L12 34H11Q2 34 2 25V11Q2 2 11 2Z" fill="white" stroke="#A6ADB2" stroke-width="1.2"/>
    <svg x="7" y="7" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="${estilo.cor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${estilo.simbolo}</svg>
  </svg>`
}

function svgRelato(estilo, status) {
  const ativo = status === 'ativo'
  const recorrencia = status === 'recorrencia'
  return `<svg width="38" height="38" viewBox="0 0 38 38" style="filter:drop-shadow(0 2px 2px #00000025)">
    <circle cx="19" cy="19" r="18" fill="white"/>
    <circle cx="19" cy="19" r="15.7" fill="${estilo.fundo}" stroke="${estilo.cor}" stroke-width="${ativo || recorrencia ? 2.5 : 1.7}" ${!ativo && !recorrencia ? 'stroke-dasharray="3 2"' : ''}/>
    ${recorrencia ? `<circle cx="19" cy="19" r="12.5" fill="none" stroke="${estilo.cor}" stroke-width="1"/>` : ''}
    <svg x="8" y="8" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="${estilo.cor}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">${estilo.simbolo}</svg>
  </svg>`
}

function criarIconeApoio(tipo) {
  const estilo = dadosApoio(tipo)
  const chave = `apoio:${estilo.categoria}`
  if (!cacheIcones.has(chave)) cacheIcones.set(chave, divIcon({
    className: 'marcador-local-apoio', iconSize: [36, 44], iconAnchor: [18, 42],
    popupAnchor: [0, -40], tooltipAnchor: [0, -40], html: svgApoio(estilo),
  }))
  return cacheIcones.get(chave)
}

function criarIconeRelato(categoria, status) {
  const tipo = Object.hasOwn(estilosRelato, categoria) ? categoria : 'Outros'
  const estado = status === 'ativo' || status === 'recorrencia' ? status : 'pendente'
  const chave = `relato:${tipo}:${estado}`
  const estilo = estado === 'recorrencia' ? estiloRecorrencia : dadosRelato(tipo)
  if (!cacheIcones.has(chave)) cacheIcones.set(chave, divIcon({
    className: 'marcador-relato', iconSize: [38, 38], iconAnchor: [19, 19],
    popupAnchor: [0, -18], tooltipAnchor: [0, -18], html: svgRelato(estilo, estado),
  }))
  return cacheIcones.get(chave)
}

function Simbolo({ estilo }) {
  return <svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke={estilo.cor}
    strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"
    dangerouslySetInnerHTML={{ __html: estilo.simbolo }} />
}

function CabecalhoPopup({ estilo, tipo, titulo }) {
  return <div className="flex items-center gap-3 border-b border-marinho/10 pb-3 pr-3">
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" style={{ backgroundColor: estilo.fundo }}><Simbolo estilo={estilo} /></div>
    <div className="min-w-0"><div className="text-[11px] text-marinho/65">{tipo}</div><div className="break-words text-sm font-extrabold text-marinho">{titulo}</div></div>
  </div>
}

function LinhaPopup({ titulo, children }) {
  return <div className="flex flex-wrap items-start justify-between gap-x-3 gap-y-1 text-xs"><span className="text-marinho/65">{titulo}</span><span className="min-w-0 break-words font-semibold text-marinho">{children}</span></div>
}

function PopupApoio({ local }) {
  const estilo = dadosApoio(local.tipo)
  return <div className="space-y-3 text-marinho">
    <CabecalhoPopup estilo={estilo} tipo={`Local de apoio · ${estilo.nome}`} titulo={local.nome} />
    <LinhaPopup titulo="Distância aproximada">{Number.isFinite(local.distancia_metros) ? `${numeroBR.format(local.distancia_metros)} m da rota` : 'Não informada'}</LinhaPopup>
    <LinhaPopup titulo="Horário cadastrado">{local.horario || 'Não informado'}</LinhaPopup>
    <div className="rounded-lg bg-fundo p-2 text-[11px] leading-relaxed text-marinho/75">Confirme a disponibilidade antes de ir. A distância é aproximada, não a distância a pé.</div>
    {local.fonte && <div className="break-words text-[11px] text-marinho/65">Fonte: {local.fonte}</div>}
  </div>
}

function PopupRelato({ relato, votando, onVotarRelato, onVerificar, mensagemVoto }) {
  const estilo = dadosRelato(relato.categoria)
  const ativo = relato.status === 'ativo'
  return <div className="space-y-3 text-marinho">
    <CabecalhoPopup estilo={estilo} tipo="Relato da comunidade" titulo={relato.categoria} />
    <div className="flex flex-wrap gap-1.5">
      <span className="rounded-full border px-2 py-1 text-[11px] font-semibold" style={{ borderColor: ativo ? '#6D28D9' : '#B45309', color: ativo ? '#6D28D9' : '#92400E', backgroundColor: ativo ? '#F3E8FF' : '#FEF3C7' }}>{ativo ? 'Alerta ativo' : 'Aguardando confirmação'}</span>
      {relato.simulado && <span className="rounded-full bg-fundo px-2 py-1 text-[11px] font-semibold">Simulado</span>}
    </div>
    <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">{relato.descricao}</div>
    {relato.rua && <LinhaPopup titulo="Rua informada">{relato.rua}</LinhaPopup>}
    {Number.isFinite(relato.distancia_metros) && <LinhaPopup titulo="Distância aproximada">{numeroBR.format(relato.distancia_metros)} m da rota</LinhaPopup>}
    <div className="grid grid-cols-2 divide-x divide-marinho/10 rounded-lg bg-fundo py-2 text-center">
      <div><div className="text-lg font-extrabold text-verde-escuro">{relato.confirmacoes ?? 0}</div><div className="text-[11px] text-marinho/65">Confirmações</div></div>
      <div><div className="text-lg font-extrabold text-[#B52D2D]">{relato.rejeicoes ?? 0}</div><div className="text-[11px] text-marinho/65">Contestações</div></div>
    </div>
    <div className="space-y-2 border-t border-marinho/10 pt-3">
      <div className="text-xs font-bold">Você também identificou essa situação?</div>
      <div className="grid grid-cols-2 gap-2">
        <button type="button" disabled={votando} onClick={() => onVotarRelato?.(relato.id, 1)} className="rounded-lg border border-verde-escuro/40 px-2 py-2 text-xs font-semibold text-verde-escuro hover:bg-verde-escuro/5 disabled:opacity-50">Confirmar</button>
        <button type="button" disabled={votando} onClick={() => onVotarRelato?.(relato.id, -1)} className="rounded-lg border border-vermelho/30 px-2 py-2 text-xs font-semibold text-[#B52D2D] hover:bg-fundo disabled:opacity-50">Contestar</button>
      </div>
    </div>
    {ativo && categoriasContinuidade.includes(relato.categoria) && <div className="space-y-2 border-t border-marinho/10 pt-3">
      <div className="text-xs font-bold">A situação ainda acontece?</div>
      <div className="grid grid-cols-2 gap-2">
        <button type="button" disabled={votando} onClick={() => onVerificar?.(relato.id, true)} className="rounded-lg border border-verde-escuro/40 px-2 py-2 text-xs font-semibold text-verde-escuro disabled:opacity-50">Sim, continua</button>
        <button type="button" disabled={votando} onClick={() => onVerificar?.(relato.id, false)} className="rounded-lg border border-marinho/20 px-2 py-2 text-xs font-semibold text-marinho disabled:opacity-50">Não, terminou</button>
      </div>
    </div>}
    {mensagemVoto && <div role="status" className="rounded-lg bg-fundo p-2 text-xs">{mensagemVoto}</div>}
    <div className="text-[11px] leading-relaxed text-marinho/65">Informação comunitária, não registro oficial.</div>
  </div>
}

// A legenda usa os mesmos desenhos e cores que o mapa.
export function LegendaMarcadores({ mostrarApoio }) {
  return <div className="space-y-3">
    {mostrarApoio && <div className="space-y-2">
      <div className="text-xs font-bold text-marinho">Locais de apoio da rota selecionada</div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {Object.keys(estilosApoio).filter(tipo => tipo !== 'outro').map(tipo => {
          const estilo = dadosApoio(tipo)
          return <div key={tipo} className="flex items-center gap-2 text-xs"><span className="inline-flex h-9 w-8 shrink-0 items-center justify-center" aria-hidden="true" dangerouslySetInnerHTML={{ __html: svgApoio(estilo) }} />{estilo.nome}</div>
        })}
      </div>
    </div>}
    <div className="space-y-2 border-t border-marinho/10 pt-3">
      <div className="text-xs font-bold text-marinho">Relatos da comunidade</div>
      <div className="flex flex-wrap gap-x-5 gap-y-2">
        {['pendente', 'ativo', 'recorrencia'].map(status => <div key={status} className="flex items-center gap-2 text-xs"><span className="inline-flex shrink-0" aria-hidden="true" dangerouslySetInnerHTML={{ __html: svgRelato(status === 'recorrencia' ? estiloRecorrencia : estilosRelato.Outros, status) }} />{status === 'pendente' ? 'Pendente (não confirmado)' : status === 'ativo' ? 'Alerta ativo' : 'Recorrência (ponto aproximado)'}</div>)}
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(estilosRelato).map(([nome, estilo]) => <div key={nome} className="flex items-center gap-2 text-xs"><span className="inline-flex shrink-0" aria-hidden="true" dangerouslySetInnerHTML={{ __html: svgRelato(estilo, 'ativo') }} />{nome}</div>)}
      </div>
      <div className="text-[11px] text-marinho/65">O desenho e a cor indicam a categoria. A borda tracejada indica relato pendente; a borda contínua, alerta ativo.</div>
    </div>
  </div>
}

// Identifica o ponto selecionado pelo usuário
function SelecionarPonto({ selecionandoLocal, onSelecionarPonto }) {
  useMapEvents({
    click(evento) {
      if (selecionandoLocal) {
        onSelecionarPonto({ lat: evento.latlng.lat, lng: evento.latlng.lng })
      }
    },
  })
  return null
}

// Desenha as rotas e destaca a alternativa selecionada.
function RotasNoMapa({ rotas, estilosRotas, indiceSelecionado, onSelecionarRota, selecionandoLocal, pontosConsulta }) {
  const mapa = useMap()

  useEffect(() => {
    const coordenadas = rotas.flatMap((rota) => rota.coordenadas || [])
    if (pontosConsulta) coordenadas.push(pontosConsulta.origem, pontosConsulta.destino)
    if (coordenadas.length > 0) {
      mapa.fitBounds(coordenadas, { padding: [35, 35], maxZoom: 17 })
    }
  }, [rotas, mapa, pontosConsulta])

  function desenharRota(rota, indice, destaque = false) {
    const estilo = estilosRotas[indice] || estiloPadrao
    const atenuada = indiceSelecionado !== null && !destaque
    return (
      <Fragment key={`${destaque ? 'destaque' : 'base'}-${indice}`}>
        <Polyline positions={rota.coordenadas} interactive={false} pathOptions={{
          color: '#FFFFFF', weight: destaque ? 12 : 10, opacity: atenuada ? 0.35 : 0.95,
          lineCap: 'round', lineJoin: 'round', dashArray: null,
        }} />
        <Polyline
          positions={rota.coordenadas}
          pathOptions={{ color: estilo.cor, dashArray: null, weight: destaque ? 8 : 6,
            opacity: atenuada ? 0.28 : 0.98, lineCap: 'round', lineJoin: 'round' }}
          interactive={!selecionandoLocal}
          eventHandlers={{ click: () => { if (!selecionandoLocal) onSelecionarRota?.(indice) } }}
        >
          <Tooltip sticky>Opção {indice + 1} — {rota.nome}</Tooltip>
        </Polyline>
      </Fragment>
    )
  }

  // A camada selecionada é desenhada por último, acima das demais.
  const selecionada = indiceSelecionado === null ? null : rotas[indiceSelecionado]
  return (
    <>
      {rotas.map((rota, indice) =>
        indice !== indiceSelecionado ? desenharRota(rota, indice) : null
      )}
      {selecionada && desenharRota(selecionada, indiceSelecionado, true)}
    </>
  )
}

// Componente principal do mapa
function MapaTrajeto({
  rotas = [],
  pontosConsulta = null,
  estilosRotas = [],
  indiceSelecionado = null,
  onSelecionarRota,
  pontoRelato,
  selecionandoLocal,
  onSelecionarPonto,
  relatosComunidade = [],
  onVotarRelato,
  onVerificar,
  recorrencias = [],
  votando = false,
  mensagemVoto = '', 
}) {
  const locaisApoio = indiceSelecionado === null ? [] : (rotas[indiceSelecionado]?.locais_apoio || [])
  return (
    <div
      className={`relative isolate h-full min-h-[400px] overflow-hidden rounded-2xl border border-marinho/15 ${
        selecionandoLocal ? 'mapa-selecionando' : ''
      }`}
    >
      <MapContainer
        center={centroVilaMariana}
        zoom={15}
        scrollWheelZoom={false}
        className="z-0 h-full w-full"
        style={{ height: '100%', minHeight: '400px', width: '100%' }}
      >
        {/* Mapa geográfico minimalista */}
<TileLayer
  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attribution/">CARTO</a> | Powered by <a href="https://www.geoapify.com/">Geoapify</a>'
url={`https://basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}{r}.png?key=${import.meta.env.VITE_CARTO_API_KEY}`}
maxZoom={19}
/>

        <RotasNoMapa
          rotas={rotas}
          pontosConsulta={pontosConsulta}
          estilosRotas={estilosRotas}
          indiceSelecionado={indiceSelecionado}
          onSelecionarRota={onSelecionarRota}
          selecionandoLocal={selecionandoLocal}
        />

        
        {/* Locais de apoio personalizados */}
        {locaisApoio.filter(local => Number.isFinite(local.lat) && Number.isFinite(local.lon)).map((local, indice) => (
          <Marker key={`apoio-${local.lat}-${local.lon}-${indice}-${Boolean(selecionandoLocal)}`}
            position={[local.lat, local.lon]} icon={criarIconeApoio(local.tipo)}
            interactive={!selecionandoLocal} keyboard={!selecionandoLocal} bubblingMouseEvents={false} title={local.nome}>
            {!selecionandoLocal && <><Tooltip>{local.nome}</Tooltip><Popup minWidth={220} maxWidth={280} maxHeight={360}><PopupApoio local={local} /></Popup></>}
          </Marker>
        ))}

        {/* Relatos da comunidade: símbolo por categoria e contorno por status. */}
        {relatosComunidade.filter(relato => Number.isFinite(relato.lat) && Number.isFinite(relato.lon)).map(relato => (
          <Marker key={`comunidade-${relato.id}-${Boolean(selecionandoLocal)}`}
            position={[relato.lat, relato.lon]} icon={criarIconeRelato(relato.categoria, relato.status)}
            interactive={!selecionandoLocal} keyboard={!selecionandoLocal} bubblingMouseEvents={false}
            title={`${relato.categoria} — ${relato.status === 'ativo' ? 'Ativo' : 'Pendente'}`}>
            {!selecionandoLocal && <><Tooltip>{relato.categoria} — {relato.status === 'ativo' ? 'Ativo' : 'Pendente'}</Tooltip>
              <Popup minWidth={230} maxWidth={290} maxHeight={390}>
                <PopupRelato relato={relato} votando={votando} onVotarRelato={onVotarRelato} onVerificar={onVerificar} mensagemVoto={mensagemVoto} />
              </Popup></>}
          </Marker>
        ))}

        {/* Recorrências: ponto médio aproximado, separado dos relatos individuais. */}
        {recorrencias.filter(r => Number.isFinite(r.lat) && Number.isFinite(r.lon)).map(r => (
          <Marker key={`recorrencia-${r.id}-${Boolean(selecionandoLocal)}`} position={[r.lat, r.lon]}
            icon={criarIconeRelato('Roubo ou furto relatado', 'recorrencia')}
            interactive={!selecionandoLocal} keyboard={!selecionandoLocal} bubblingMouseEvents={false}
            title="Recorrência comunitária de roubo ou furto">
            {!selecionandoLocal && <><Tooltip>Recorrência comunitária de roubo ou furto</Tooltip>
              <Popup minWidth={220} maxWidth={280} maxHeight={360}>
                <div className="space-y-3 text-marinho">
                  <CabecalhoPopup estilo={estiloRecorrencia} tipo="Recorrência comunitária" titulo="Roubo ou furto" />
                  {r.simulado && <div className="text-xs font-semibold">Simulada</div>}
                  {r.rua && <LinhaPopup titulo="Rua informada">{r.rua}</LinhaPopup>}
                  <div className="rounded-lg bg-fundo p-2 text-xs leading-relaxed">Ponto médio aproximado de dois relatos associados, não registro oficial. Não altera diretamente o Score.</div>
                </div>
              </Popup></>}
          </Marker>
        ))}

        {/* Marcadores personalizados de origem e destino */}
{pontosConsulta && (
  <>
    <Marker
      position={pontosConsulta.origem}
      icon={iconeOrigem}
      interactive={false}
      keyboard={false}
      zIndexOffset={1000}
    />

    <Marker
      position={pontosConsulta.destino}
      icon={iconeDestino}
      interactive={false}
      keyboard={false}
      zIndexOffset={1000}
    />
  </>
)}

        {/* Captura o clique no mapa */}
        <SelecionarPonto
          selecionandoLocal={selecionandoLocal}
          onSelecionarPonto={onSelecionarPonto}
        />

        {/* Marcador do local escolhido */}
        {pontoRelato && (
          <CircleMarker
            center={[pontoRelato.lat, pontoRelato.lng]}
            radius={9}
            interactive={false}
            pathOptions={{
              color: '#0A2940',
              fillColor: '#16834B',
              fillOpacity: 1,
              weight: 3,
            }}
          >
            <Tooltip permanent direction="top" offset={[0, -12]}>
              Local do relato
            </Tooltip>
          </CircleMarker>
        )}
      </MapContainer>
    </div>
  )
}

export default MapaTrajeto
