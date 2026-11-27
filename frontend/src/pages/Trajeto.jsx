import { useCallback, useEffect, useRef, useState } from 'react'
import { listarContextoComunidade, votarRelato, verificarContinuidade } from '../services/comunidade'
import { useLocation } from 'react-router-dom'
import FormularioRelato from '../components/trajeto/FormularioRelato'

import {
  Route,
  Gauge,
  TriangleAlert,
  MapPin,
  MessagesSquare,
  Layers,
  Phone,
  MessageSquarePlus,
  ChevronDown,
  Info,
  CheckCircle2,
  Clock,
} from 'lucide-react'
import {
  geocodificarEndereco,
  buscarRotas,
  consultarAmbiente,
} from '../services/api'

import FormularioTrajeto from '../components/trajeto/FormularioTrajeto'
import MapaTrajeto, { LegendaMarcadores } from '../components/trajeto/MapaTrajeto'
import SugestoesEndereco from '../components/trajeto/SugestoesEndereco'

const detalhes = [
  {
    titulo: 'Por que esta pontuação?',
    icone: Gauge,
    descricao: 'Entenda os fatores considerados no Score de Contexto.',
  },
  {
    titulo: 'Ocorrências registradas',
    icone: TriangleAlert,
    descricao: 'Consulte os registros associados ao trajeto.',
  },
  {
    titulo: 'Locais de apoio',
    icone: MapPin,
    descricao: 'Conheça os locais de apoio próximos à rota.',
  },
  {
    titulo: 'Alertas da comunidade',
    icone: MessagesSquare,
    descricao: 'Consulte os relatos e alertas próximos à alternativa selecionada.',
  },
]

// Faixas do Score de Contexto definidas no config.py do piloto.
// A cor representa o contexto; a seleção destaca a alternativa.
const tracos = [null, null, null]
const numeroBR = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })

function estiloDaRota(rota, indice) {
  const score = rota.score_contexto
  const traco = tracos[indice % tracos.length]

  if (!Number.isFinite(score)) {
    return { cor: '#64748B', texto: '#475569', classe: 'Contexto indisponível', traco }
  }
  if (score >= 70) {
    return { cor: '#16834B', texto: '#166534', classe: 'Contexto mais favorável', traco }
  }
  if (score >= 40) {
    return { cor: '#E5A11A', texto: '#805D00', classe: 'Contexto intermediário', traco }
  }
  return { cor: '#EF4444', texto: '#B52D2D', classe: 'Contexto menos favorável', traco }
}

function formatarDistancia(metros) {
  if (!Number.isFinite(metros)) return 'Indisponível'
  return metros >= 1000
    ? `${numeroBR.format(metros / 1000)} km`
    : `${numeroBR.format(metros)} m`
}

function formatarNumero(valor) {
  return Number.isFinite(valor) ? numeroBR.format(valor) : '—'
}

const tiposApoio = {
  farmacia: 'Farmácia', mercado: 'Mercado', loja: 'Loja',
  delegacia: 'Delegacia', hospital: 'Hospital', clinica: 'Clínica',
  posto: 'Posto de combustível', metro: 'Metrô',
}

function DetalhesPontuacao({ rota, estilo, alertasDisponiveis }) {
  const avaliacao = rota.avaliacao
  return (
    <div className="space-y-3">
      <p><strong>Motivo da alternativa:</strong> {rota.justificativa || 'Indisponível.'}</p>
      <p>Score de Contexto: <strong>{formatarNumero(rota.score_contexto)}/100</strong></p>
      <p>Score de iluminação: <strong>{formatarNumero(rota.score_iluminacao)}/100</strong></p>
      {avaliacao ? (
        <>
          {avaliacao.dados_piloto && <p className="rounded-lg bg-fundo p-2 text-xs">Score piloto: dados de locais de apoio pendentes na avaliação.</p>}
          <dl className="space-y-2 rounded-lg bg-fundo p-3">
            <div className="flex justify-between gap-3"><dt>Trechos com iluminação cadastrada próxima</dt><dd className="font-bold">{formatarNumero(avaliacao.n_trechos_com_luz)}</dd></div>
            <div className="flex justify-between gap-3"><dt>Registros associados aos trechos no score</dt><dd className="font-bold">{formatarNumero(avaliacao.n_ocorrencias)}</dd></div>
            <div className="flex justify-between gap-3"><dt>Trechos em áreas de concentração de registros</dt><dd className="font-bold">{formatarNumero(avaliacao.n_trechos_em_hotspot)}</dd></div>
            <div className="flex justify-between gap-3"><dt>Trechos com locais de apoio próximos</dt><dd className="font-bold">{formatarNumero(avaliacao.n_trechos_com_abrigos)}</dd></div>
          </dl>
          {alertasDisponiveis && <p>Alertas considerados no Score: {formatarNumero(avaliacao.n_alertas_na_rota)} · Penalidade: {formatarNumero(avaliacao.penalidade_alertas)} pontos.</p>}
          <p className="text-xs leading-relaxed">A nota resume os dados de contexto dos trechos, ponderados pelo comprimento. As contagens acima não equivalem a pontos individuais do score.</p>
        </>
      ) : <p className="text-xs">Detalhamento dos fatores indisponível.</p>}
      <p className="text-xs font-semibold" style={{ color: estilo.texto }}>{estilo.classe}.</p>
      {!alertasDisponiveis && <p className="text-xs">Alertas comunitários ainda não considerados.</p>}
    </div>
  )
}

function DetalhesOcorrencias({ ocorrencias }) {
  if (!ocorrencias) return <p>Detalhamento de ocorrências indisponível.</p>
  return (
    <div className="space-y-3">
      {ocorrencias.dados_piloto && <p className="rounded-lg bg-fundo p-2 text-xs">Dados do score piloto; não representam necessariamente ocorrências reais.</p>}
      {ocorrencias.categorias_disponiveis ? (
        <>
          <p><strong>{formatarNumero(ocorrencias.total_categorias)}</strong> registros associados aos trechos deste trajeto, no recorte da base.</p>
          {ocorrencias.categorias.length > 0 ? (
            <ul className="divide-y divide-marinho/10">
              {ocorrencias.categorias.map((item) => (
                <li key={item.categoria} className="flex justify-between gap-3 py-2"><span>{item.categoria}</span><strong>{formatarNumero(item.total)}</strong></li>
              ))}
            </ul>
          ) : <p>Nenhum registro encontrado nos trechos consultados.</p>}
          <p className="text-xs leading-relaxed">O detalhamento reúne os dois sentidos de cada trecho. Categorias combinadas permanecem agrupadas. Não representa necessariamente boletins únicos nem previsão de ocorrências.</p>
        </>
      ) : (
        <>
          <p><strong>{formatarNumero(ocorrencias.registros_associados_ao_score)}</strong> registros associados aos trechos no score.</p>
          <p className="text-xs">Detalhamento por categoria indisponível.</p>
        </>
      )}
      {ocorrencias.fonte && <p className="text-xs">Fonte: {ocorrencias.fonte} · Recorte do piloto: {ocorrencias.periodo}.</p>}
      <p className="text-xs">Dados históricos; ausência de registros não significa ausência de risco.</p>
    </div>
  )
}

function DetalhesApoio({ locais }) {
  if (!Array.isArray(locais)) return <p>Cadastro de locais de apoio indisponível.</p>
  if (!locais.length) return <p>Nenhum local de apoio cadastrado encontrado no raio consultado.</p>
  return (
    <div className="space-y-3">
      <p>{locais.length} {locais.length === 1 ? 'local de apoio sugerido' : 'locais de apoio sugeridos'} — até 200 m de pontos do trajeto.</p>
      <ul className="divide-y divide-marinho/10">
        {locais.map((local, indice) => (
          <li key={`${local.lat}-${local.lon}-${indice}`} className="flex items-start gap-2 py-3">
            <MapPin size={17} className="mt-0.5 shrink-0 text-verde-escuro" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="break-words font-semibold text-marinho">{local.nome}</p>
              <p className="text-xs">{tiposApoio[local.tipo] || local.tipo} · aprox. {formatarNumero(local.distancia_metros)} m</p>
              {local.fonte && <p className="mt-1 text-xs">Fonte: {local.fonte}</p>}
              <p className="text-xs">Horário cadastrado: {local.horario || 'Não informado'}</p>
            </div>
          </li>
        ))}
      </ul>
      <p className="text-xs leading-relaxed">Até cinco sugestões de locais cadastrados. Distância aproximada em linha reta até os pontos da rota, não distância a pé. Confirme horário e disponibilidade de atendimento.</p>
    </div>
  )
}

function DetalhesComunidade({ relatos, recorrencias, estado, erro, mensagemVoto, onAtualizar, onVotar, onVerificar, votando }) {
  return (
    <div className="space-y-3">
      <p className="text-xs leading-relaxed">Relatos e alertas a até 50 m deste caminho, na última pesquisa. São informações da comunidade, não registros oficiais. Somente alertas ativos autorizados pelo banco afetam o Score.</p>
      <button type="button" onClick={onAtualizar} disabled={estado === 'carregando' || votando}
        className="rounded-lg border border-marinho/15 px-3 py-2 text-xs font-bold text-verde-escuro disabled:opacity-50">Atualizar cálculo e relatos</button>
      {mensagemVoto && <p role="status" className="text-sm">{mensagemVoto}</p>}
      {estado === 'carregando' && <p role="status">Consultando a comunidade...</p>}
      {estado === 'erro' && <p role="alert">{erro}</p>}
      {estado === 'pronto' && relatos.length === 0 && <p>Nenhum relato pendente ou alerta ativo encontrado no raio consultado. Isso não garante segurança.</p>}
      {estado === 'pronto' && relatos.map((relato) => (
        <article key={relato.id} className="space-y-2 rounded-lg border border-marinho/10 p-3">
          <p className="font-bold text-marinho">{relato.categoria}{relato.simulado && <span className="ml-2 text-xs text-[#805D00]">Simulado</span>}</p>
          <p className={`text-xs font-semibold ${relato.status === 'ativo' ? 'text-[#6D28D9]' : 'text-[#92400E]'}`}>
            {relato.status === 'ativo' ? 'Alerta ativo da comunidade' : 'Relato pendente — não confirmado'}
          </p>
          <p className="break-words">{relato.descricao}</p>
          {relato.rua && <p className="text-xs break-words">Rua informada: {relato.rua}</p>}
          <p className="text-xs">Distância aproximada da rota: {formatarNumero(relato.distancia_metros)} m</p>
          <p className="text-xs">Confirmações: {relato.confirmacoes ?? 0} · Rejeições: {relato.rejeicoes ?? 0}</p>
          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={votando} onClick={() => onVotar(relato.id, 1)} className="rounded-lg border border-verde-escuro/30 px-3 py-2 text-xs font-semibold text-verde-escuro disabled:opacity-50">Confirmar relato</button>
            <button type="button" disabled={votando} onClick={() => onVotar(relato.id, -1)} className="rounded-lg border border-vermelho/30 px-3 py-2 text-xs font-semibold text-[#B52D2D] disabled:opacity-50">Contestar relato</button>
          </div>
          {relato.status === 'ativo' && ['Iluminação insuficiente', 'Problema na calçada', 'Obras ou bloqueios', 'Tumulto ou confusão'].includes(relato.categoria) && (
            <div className="space-y-2 border-t border-marinho/10 pt-2">
              <p className="text-xs font-semibold">A situação ainda acontece?</p>
              <div className="flex flex-wrap gap-2">
                <button type="button" disabled={votando} onClick={() => onVerificar(relato.id, true)} className="rounded-lg border border-verde-escuro/30 px-3 py-2 text-xs text-verde-escuro disabled:opacity-50">Sim, continua</button>
                <button type="button" disabled={votando} onClick={() => onVerificar(relato.id, false)} className="rounded-lg border border-marinho/20 px-3 py-2 text-xs disabled:opacity-50">Não, terminou</button>
              </div>
            </div>
          )}
        </article>
      ))}
      <div className="space-y-2 border-t border-marinho/10 pt-3">
        <p className="font-bold text-marinho">Recorrências comunitárias de roubo ou furto</p>
        <p className="text-xs">Pares de relatos associados pela regra de recorrência do banco, não boletins oficiais. Não alteram diretamente o Score.</p>
        {!Array.isArray(recorrencias) ? <p>Consulta de recorrências indisponível.</p> : recorrencias.length === 0 ? <p>Nenhuma recorrência encontrada no raio consultado.</p> : recorrencias.map(r => (
          <div key={r.id} className="rounded-lg border border-marinho/10 p-3">
            <p className="font-semibold break-words">{r.rua}</p>
            <p className="text-xs">Ponto médio aproximado · {formatarNumero(r.distancia_metros)} m da rota</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function Trajeto() {
  const location = useLocation()
const buscaAutomatica = useRef(null)

  // Recebe os endereços informados na homepage
  const [origem, setOrigem] = useState(
    location.state?.origem || ''
  )

  const [destino, setDestino] = useState(
    location.state?.destino || ''
  )

  const [campoSugestao, setCampoSugestao] = useState(null)
  const [ambiente, setAmbiente] = useState(null)
  useEffect(() => {
    let ativo = true
    consultarAmbiente().then(dados => { if (ativo) setAmbiente(dados.ambiente) }).catch(() => {})
    return () => { ativo = false }
  }, [])
  const [mensagem, setMensagem] = useState('')
  const [selecionandoLocal, setSelecionandoLocal] = useState(false)
  const [pontoRelato, setPontoRelato] = useState(null)
  const [carregando, setCarregando] = useState(false)
  const [rotas, setRotas] = useState([])
  const [indiceSelecionado, setIndiceSelecionado] = useState(null)
  const [alertasDisponiveis, setAlertasDisponiveis] = useState(false)
  const [consultaRealizada, setConsultaRealizada] = useState(null)
  const [pontosConsulta, setPontosConsulta] = useState(null)
  const [relatosComunidade, setRelatosComunidade] = useState([])
  const [recorrenciasComunidade, setRecorrenciasComunidade] = useState(null)
  const [estadoComunidade, setEstadoComunidade] = useState('carregando')
  const [erroComunidade, setErroComunidade] = useState('')
  const [mensagemVoto, setMensagemVoto] = useState('')
  const [votando, setVotando] = useState(false)
  const [dadosDesatualizados, setDadosDesatualizados] = useState(false)
  const versaoComunidade = useRef(0)

  function marcarDadosDesatualizados() {
    versaoComunidade.current += 1
    setDadosDesatualizados(true)
  }
  const votoEmCurso = useRef(false)
  const consultaComunidade = useRef(0)

  const atualizarComunidade = useCallback(async () => {
    const consulta = ++consultaComunidade.current
    setEstadoComunidade('carregando')
    setErroComunidade('')
    try {
      const dados = await listarContextoComunidade()
      if (consulta !== consultaComunidade.current) return
      if (dados.ambiente) setAmbiente(dados.ambiente)
      setRelatosComunidade(dados.relatos)
      setRecorrenciasComunidade(dados.recorrencias)
      setEstadoComunidade('pronto')
    } catch (erro) {
      if (consulta !== consultaComunidade.current) return
      setRelatosComunidade([])
      setRecorrenciasComunidade(null)
      setErroComunidade(erro.message || 'Comunidade indisponível.')
      setEstadoComunidade('erro')
    }
  }, [])

  useEffect(() => {
    atualizarComunidade()
    return () => { consultaComunidade.current += 1 }
  }, [atualizarComunidade])

  async function registrarVoto(id, voto) {
    if (votoEmCurso.current) return
    votoEmCurso.current = true
    setVotando(true)
    setMensagemVoto('')
    try {
      await votarRelato(id, voto)
      setMensagemVoto('Voto registrado.')
    } catch (erro) {
      setMensagemVoto(erro.message || 'Não foi possível confirmar o voto.')
    } finally {
      marcarDadosDesatualizados()
      await atualizarComunidade()
      votoEmCurso.current = false
      setVotando(false)
    }
  }

  async function registrarContinuidade(id, continua) {
    if (votoEmCurso.current) return
    votoEmCurso.current = true
    setVotando(true)
    setMensagemVoto('')
    try {
      await verificarContinuidade(id, continua)
      setMensagemVoto('Verificação registrada.')
    } catch (erro) {
      setMensagemVoto(erro.message || 'Não foi possível confirmar a verificação.')
    } finally {
      marcarDadosDesatualizados()
      await atualizarComunidade()
      votoEmCurso.current = false
      setVotando(false)
    }
  }

  const rotaSelecionada = indiceSelecionado === null ? null : rotas[indiceSelecionado]
  const estilosRotas = rotas.map(estiloDaRota)
  // Antes da busca, o mapa geral permite explorar relatos. Depois, mostra
  // apenas o recorte das rotas, ou o recorte da alternativa selecionada.
  const relatosNoMapa = rotas.length === 0
    ? (estadoComunidade === 'pronto' ? relatosComunidade : [])
    : dadosDesatualizados ? [] : rotaSelecionada
      ? (rotaSelecionada.relatos_proximos || [])
      : [...new Map(rotas.flatMap(rota => rota.relatos_proximos || []).map(relato => [relato.id, relato])).values()]

  const recorrenciasNoMapa = rotas.length === 0
    ? (estadoComunidade === 'pronto' ? recorrenciasComunidade || [] : [])
    : dadosDesatualizados ? [] : rotaSelecionada
      ? (rotaSelecionada.recorrencias_proximas || [])
      : [...new Map(rotas.flatMap(rota => rota.recorrencias_proximas || []).map(r => [r.id, r])).values()]

  function atualizarTrajeto() {
    if (consultaRealizada) {
      compararTrajetos({ preventDefault() {} }, consultaRealizada)
    }
  }

  function selecionarPontoRelato(ponto) {
    setPontoRelato(ponto)
    setSelecionandoLocal(false)
  }


  async function compararTrajetos(evento, enderecos = null) {
    evento.preventDefault()
    if (carregando || votoEmCurso.current) return
    const origemBusca = enderecos?.origem ?? origem
    const destinoBusca = enderecos?.destino ?? destino

    if (!origemBusca.trim() || !destinoBusca.trim()) {
      setMensagem('Informe a origem e o destino.')
      return
    }

    if (
      origemBusca.trim().toLowerCase() ===
      destinoBusca.trim().toLowerCase()
    ) {
      setMensagem('A origem e o destino precisam ser diferentes.')
      return
    }

    const versaoBusca = versaoComunidade.current
    const caminhoAnterior = enderecos && rotaSelecionada ? JSON.stringify(rotaSelecionada.coordenadas) : null
    setCampoSugestao(null)
    setCarregando(true)
    setDadosDesatualizados(false)
    setRotas([])
    setIndiceSelecionado(null)
    setAlertasDisponiveis(false)
    setConsultaRealizada(null)
    setPontosConsulta(null)

    try {
      setMensagem('Localizando o endereço de origem...')

      const pontoOrigem = await geocodificarEndereco(origemBusca)

      setMensagem('Localizando o endereço de destino...')

      const pontoDestino = await geocodificarEndereco(destinoBusca)

      setMensagem('Analisando as alternativas de trajetos...')

      const resultado = await buscarRotas(
        pontoOrigem,
        pontoDestino
      )

      if (
        !Array.isArray(resultado?.rotas) ||
        resultado.rotas.length === 0
      ) {
        throw new Error(
          'Não encontramos alternativas para esse trajeto.'
        )
      }

      setRotas(resultado.rotas)
      if (caminhoAnterior) {
        const indice = resultado.rotas.findIndex(rota => JSON.stringify(rota.coordenadas) === caminhoAnterior)
        setIndiceSelecionado(indice >= 0 ? indice : null)
      }
      setDadosDesatualizados(versaoBusca !== versaoComunidade.current)
      setAlertasDisponiveis(resultado.alertas_disponiveis === true)
      if (resultado.ambiente) setAmbiente(resultado.ambiente)
      setConsultaRealizada({ origem: origemBusca.trim(), destino: destinoBusca.trim() })
      setPontosConsulta({
        origem: [pontoOrigem.latitude, pontoOrigem.longitude],
        destino: [pontoDestino.latitude, pontoDestino.longitude],
      })
      setMensagem('')

    } catch (erro) {
      setMensagem(
        erro instanceof TypeError
          ? 'Não foi possível conectar ao servidor.'
          : erro.message
      )

    } finally {
      setCarregando(false)
    }
  }

  // Calcula automaticamente o trajeto recebido da homepage
useEffect(() => {
  const origemHome = location.state?.origem
  const destinoHome = location.state?.destino

  if (!origemHome?.trim() || !destinoHome?.trim()) return

  if (buscaAutomatica.current === location.key) return

  if (carregando) return

  buscaAutomatica.current = location.key

  setOrigem(origemHome)
  setDestino(destinoHome)

  compararTrajetos(
    { preventDefault() {} },
    {
      origem: origemHome,
      destino: destinoHome
    }
  )
}, [location.key, location.state, carregando, compararTrajetos])

  return (
    <main className="bg-fundo">

      <div className="entrada-pagina-trajeto mx-auto max-w-7xl px-6 pb-10 pt-10 lg:px-10">

        {/* TÍTULO DA PÁGINA */}
        <div
          className="animar-entrada mb-7"
          style={{ '--atraso': '0ms' }}
        >

          <h1 className="text-3xl font-extrabold tracking-tight text-marinho md:text-4xl">
  Hoje, vamos{' '}
  <span className="text-[#16834b]">
    por onde?
  </span>
</h1>

          <p className="mt-2 text-sm leading-relaxed text-marinho/65">
            Compare caminhos e conheça o contexto de cada alternativa.
          </p>

        </div>
        {/* FORMULÁRIO */}
        <FormularioTrajeto
          origem={origem}
          destino={destino}
          setOrigem={(valor) => { setOrigem(valor); setCampoSugestao('origem') }}
          setDestino={(valor) => { setDestino(valor); setCampoSugestao('destino') }}
          onComparar={compararTrajetos}
        />
        <SugestoesEndereco campo={campoSugestao} texto={campoSugestao === 'origem' ? origem : destino}
          carregando={carregando} onEscolher={nome => {
            if (campoSugestao === 'origem') setOrigem(nome)
            else setDestino(nome)
            setCampoSugestao(null)
          }} />


        {/* Mensagens do formulário */}
        {mensagem && (
          <div
            role="status"
            className="mt-4 flex items-center gap-3 rounded-xl border border-marinho/10 bg-white p-3 text-sm text-marinho"
          >
            <Info size={19} className="shrink-0" />
            {mensagem}
          </div>
        )}

        {/* MAPA E ALTERNATIVAS */}
        <div className="mt-7 flex w-full flex-col gap-6">

          {/* Alternativas de trajeto */}
          <section
            className="animar-entrada flex min-w-0 flex-col rounded-2xl border border-marinho/10 bg-white p-5"
            style={{ '--atraso': '400ms' }}
          >

            <h2 className="text-lg font-extrabold text-marinho">
              Alternativas de trajeto
            </h2>

            

            {carregando ? (
              <div role="status" className="flex flex-1 flex-col items-center justify-center py-10 text-center">
                <div className="mb-4 h-8 w-8 animate-spin rounded-full border-2 border-verde-escuro/20 border-t-verde-escuro motion-reduce:animate-none" aria-hidden="true" />
                <p className="text-sm font-semibold text-marinho">Buscando alternativas...</p>
              </div>
            ) : rotas.length > 0 ? (
              <div className="mt-4 space-y-3">
                <p role="status" className="text-xs text-marinho/65">
                  {rotas.length === 1 ? '1 alternativa encontrada.' : `${rotas.length} alternativas encontradas.`}
                </p>
                {consultaRealizada && (
                  <p className="break-words text-xs text-marinho/65">
                    {consultaRealizada.origem} → {consultaRealizada.destino}
                  </p>
                )}
                {dadosDesatualizados && (
                  <div className="rounded-lg border border-[#B88A00]/40 bg-fundo p-3 text-xs leading-relaxed text-marinho">
                    Os dados da comunidade podem ter mudado. As notas abaixo são da última pesquisa.
                    <button type="button" disabled={votando} onClick={atualizarTrajeto} className="mt-2 block font-bold text-verde-escuro underline disabled:opacity-50">Atualizar cálculo e relatos</button>
                  </div>
                )}
                {!alertasDisponiveis && (
                  <p className="rounded-lg bg-fundo p-2 text-xs leading-relaxed text-marinho/75">
                    Dados comunitários indisponíveis neste cálculo. A nota considera apenas o contexto histórico e os demais dados disponíveis.
                  </p>
                )}
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">

  {rotas.map((rota, indice) => {
    const estilo = estilosRotas[indice]
                  const selecionada = indice === indiceSelecionado
                  const score = rota.score_contexto
                  return (
                    <button
                      key={indice}
                      type="button"
                      aria-pressed={selecionada}
                      onClick={() => setIndiceSelecionado(indice)}
                      className={`w-full rounded-xl border p-3 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-verde-escuro ${selecionada ? 'border-verde-escuro bg-verde-escuro/5' : 'border-marinho/15 bg-white hover:bg-fundo'}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 text-xs text-marinho/65">
                            <svg width="32" height="8" viewBox="0 0 32 8" aria-hidden="true" className="shrink-0">
                              <line x1="2" y1="4" x2="30" y2="4" stroke={estilo.cor} strokeWidth="3" strokeLinecap="round" strokeDasharray={estilo.traco || undefined} />
                            </svg>
                            Opção {indice + 1}
                          </div>
                          <h3 className="mt-1 text-sm font-extrabold text-marinho">{rota.nome}</h3>
                        </div>
                        <div className="shrink-0 text-right">
                          <span className="text-lg font-extrabold" style={{ color: estilo.texto }}>{formatarNumero(score)}</span>
                          <span className="text-xs text-marinho/60">/100</span>
                          <p className="text-[10px] text-marinho/65">Score de Contexto</p>
                        </div>
                      </div>
                      <p className="mt-2 text-xs font-semibold" style={{ color: estilo.texto }}>{estilo.classe}</p>
                      {Number.isFinite(score) && (
                        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-marinho/10" aria-hidden="true">
                          <div className="h-full rounded-full" style={{ width: `${Math.max(0, Math.min(100, score))}%`, backgroundColor: estilo.cor }} />
                        </div>
                      )}
                      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs text-marinho/80">
                        <span className="flex items-center gap-1.5"><Route size={15} aria-hidden="true" />{formatarDistancia(rota.distancia_metros)}</span>
                        <span className="flex items-center gap-1.5"><Clock size={15} aria-hidden="true" />{formatarNumero(rota.tempo_minutos)} min</span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-marinho/75">
                        <span>Registros: {formatarNumero(rota.ocorrencias?.total_categorias ?? rota.ocorrencias?.registros_associados_ao_score)}</span>
                        <span>Locais de apoio: {Array.isArray(rota.locais_apoio) ? rota.locais_apoio.length : '—'}</span>
                        <span>Alertas ativos: {Array.isArray(rota.relatos_proximos) && !dadosDesatualizados ? rota.relatos_proximos.filter(r => r.status === 'ativo').length : '—'}</span>
                        <span>Relatos pendentes: {Array.isArray(rota.relatos_proximos) && !dadosDesatualizados ? rota.relatos_proximos.filter(r => r.status === 'pendente').length : '—'}</span>
                      </div>
                      <div className="mt-3 flex items-center gap-2 text-xs font-bold text-verde-escuro">
                        {selecionada ? <><CheckCircle2 size={16} aria-hidden="true" /> Trajeto selecionado</> : 'Selecionar trajeto'}
                      </div>
                    </button>
                  )
                })}
</div>

{indiceSelecionado !== null && (
                  <button type="button" onClick={() => setIndiceSelecionado(null)} className="text-xs font-semibold text-marinho underline underline-offset-4">
                    Ver todas as alternativas
                  </button>
                )}
              </div>
            ) : (
              <div className="flex flex-1 flex-col items-center justify-center px-4 py-10 text-center">
                <div className="mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-verde-escuro/8">
                  <Route size={38} strokeWidth={1.6} className="text-verde-escuro" />
                </div>
                <h3 className="text-base font-bold text-marinho">Seu próximo caminho começa aqui.</h3>
                <p className="mt-3 max-w-xs text-sm leading-relaxed text-marinho/60">
                  Informe a origem e o destino para comparar as alternativas de trajeto.
                </p>
              </div>
            )}

          </section>

          {/* Mapa em largura total */}
          <div
            className="animar-entrada flex min-w-0 flex-col gap-3"
            style={{ '--atraso': '200ms' }}
          >

            
            <div className="relative h-[420px] w-full lg:h-[580px]">

              <MapaTrajeto
                rotas={rotas}
                pontosConsulta={pontosConsulta}
                estilosRotas={estilosRotas}
                indiceSelecionado={indiceSelecionado}
                onSelecionarRota={setIndiceSelecionado}
                selecionandoLocal={selecionandoLocal}
                pontoRelato={pontoRelato}
                onSelecionarPonto={selecionarPontoRelato}
                relatosComunidade={relatosNoMapa}
                onVotarRelato={registrarVoto}
                onVerificar={registrarContinuidade}
                recorrencias={recorrenciasNoMapa}
                votando={votando}
                mensagemVoto={mensagemVoto}
              />

              <FormularioRelato
                ambiente={ambiente}
                pontoRelato={pontoRelato}
                selecionandoLocal={selecionandoLocal}
                onEscolherLocal={() => setSelecionandoLocal(true)}
                onRelatoEnviado={() => { setPontoRelato(null); marcarDadosDesatualizados(); atualizarComunidade() }}
              />

              {/* Instruções para selecionar o local */}
              {selecionandoLocal && (
                <div className="absolute inset-x-3 bottom-7 z-20 animar-campo-relato">

                  <div className="flex flex-wrap items-center gap-3 rounded-xl border border-marinho/10 bg-white p-4 shadow-lg">

                    <MapPin
                      size={24}
                      className="shrink-0 text-verde-escuro"
                    />

                    <div className="min-w-0 flex-1">

                      <p className="text-sm font-bold text-marinho">
                        Onde aconteceu?
                      </p>

                      <p className="mt-1 text-xs text-marinho/65">
                        Clique no mapa para marcar o local da ocorrência.
                      </p>

                    </div>

                    <button
                      type="button"
                      onClick={() => setSelecionandoLocal(false)}
                      className="rounded-lg border border-marinho/15 px-3 py-2 text-xs font-semibold text-marinho transition-colors hover:bg-fundo"
                    >
                      Cancelar
                    </button>

                  </div>

                </div>
              )}

            </div>


            {mensagemVoto && <p role="status" className="rounded-lg bg-white p-2 text-xs text-marinho">{mensagemVoto}</p>}
            {!rotas.length && estadoComunidade === 'erro' && <div role="alert" className="rounded-lg bg-white p-2 text-xs text-marinho">{erroComunidade} <button type="button" onClick={atualizarComunidade} className="font-bold text-verde-escuro underline">Tentar novamente</button></div>}

            {/* Ferramentas do mapa */}
            <div className="grid grid-cols-[1fr_auto] items-start gap-3">

              {/* Legenda */}
              <details className="rounded-xl border border-marinho/15 bg-white">

                <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-sm font-semibold">

                  <Layers size={17} />

                  Legenda do mapa

                  <ChevronDown size={17} className="ml-auto" />

                </summary>

                <div className="space-y-3 border-t border-marinho/10 p-4 text-sm">

                  {rotas.map((rota, indice) => (
                    <div key={indice} className="flex items-center gap-3">
                      <svg width="34" height="8" viewBox="0 0 34 8" aria-hidden="true">
                        <line x1="2" y1="4" x2="32" y2="4"
                          stroke={estilosRotas[indice].cor}
                          strokeWidth="3"
                          strokeLinecap="round"
                          strokeDasharray={estilosRotas[indice].traco || undefined}
                        />
                      </svg>
                      <span>Opção {indice + 1} — {rota.nome}</span>
                    </div>
                  ))}
                  {rotas.length > 0 && (
                    <div className="flex items-center gap-3 text-xs"><span className="rounded-full border border-marinho bg-white px-2 py-1 font-bold">Origem / Destino</span> Endereços consultados</div>
                  )}
                  <LegendaMarcadores mostrarApoio={rotas.length > 0} />
                  <p className="text-xs leading-relaxed text-marinho/65">
                    Verde: 70 a 100. Amarelo: 40 até abaixo de 70.
                    Vermelho: abaixo de 40. As cores representam o contexto,
                    não a garantia de segurança.
                  </p>
                </div>

              </details>

              {/* Emergência */}
              <details className="rounded-xl border border-vermelho/25 bg-white">

                <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-sm font-semibold text-[#B52D2D]">

                  <Phone size={16} />

                  Emergência

                  <ChevronDown size={16} />

                </summary>

                <div className="flex flex-col gap-3 border-t border-vermelho/15 p-4 text-sm">

                  <a href="tel:190" className="hover:underline">
                    Polícia Militar — 190
                  </a>

                  <a href="tel:192" className="hover:underline">
                    SAMU — 192
                  </a>

                  <a href="tel:193" className="hover:underline">
                    Bombeiros — 193
                  </a>

                </div>

              </details>

            </div>

          </div>

          

        </div>

        {/* DETALHAMENTO DO TRAJETO */}
        <section className="mt-9 border-t border-marinho/10 pt-7">

          <div className="mb-5 flex flex-wrap items-center justify-between gap-4">

            <div>

              <h2 className="text-2xl font-extrabold tracking-tight text-marinho">
                Conheça seu{' '}
                <span className="text-verde-escuro">
                  trajeto.
                </span>
              </h2>

            </div>

          </div>

          {/* Detalhes em duas colunas */}
          <div className="mt-8 grid items-start gap-3 md:grid-cols-2">

            {detalhes.map((item) => {
              const Icone = item.icone

              return (
                <details
                  key={item.titulo}
                  className="group rounded-xl border border-marinho/15 bg-white"
                >

                  <summary className="flex cursor-pointer list-none items-center gap-3 p-4">

                    <Icone
                      size={22}
                      className="shrink-0 text-verde-escuro"
                    />

                    <div className="flex-1">

                      <h3 className="text-sm font-bold text-marinho">
                        {item.titulo}
                      </h3>

                      <p className="mt-1 text-xs leading-relaxed text-marinho/60">
                        {item.descricao}
                      </p>

                    </div>

                    <ChevronDown
                      size={18}
                      className="shrink-0 text-marinho/60 transition-transform group-open:rotate-180"
                    />

                  </summary>

                  <div className="border-t border-marinho/10 p-4 text-sm text-marinho/65 ">
                    {item.titulo === 'Alertas da comunidade' ? (
                      !rotaSelecionada ? (
                        <p>Selecione uma alternativa para consultar seus alertas. Você também pode clicar em um marcador do mapa para ver o relato e votar.</p>
                      ) : dadosDesatualizados || !Array.isArray(rotaSelecionada.relatos_proximos) ? (
                        <div className="space-y-2">
                          <p>{dadosDesatualizados ? 'Atualize o cálculo para consultar os relatos e a pontuação atuais.' : 'Consulta de relatos próximos indisponível. Não significa que não existam alertas.'}</p>
                          <button type="button" disabled={votando || carregando} onClick={atualizarTrajeto} className="font-bold text-verde-escuro underline disabled:opacity-50">Atualizar cálculo e relatos</button>
                        </div>
                      ) : (
                        <DetalhesComunidade recorrencias={rotaSelecionada.recorrencias_proximas} onVerificar={registrarContinuidade} relatos={rotaSelecionada.relatos_proximos} estado="pronto" erro="" mensagemVoto={mensagemVoto} onAtualizar={atualizarTrajeto} onVotar={registrarVoto} votando={votando} />
                      )
                    ) : !rotaSelecionada ? (
                      'Selecione uma das alternativas para conhecer o trajeto.'
                    ) : item.titulo === 'Por que esta pontuação?' ? (
                      <><DetalhesPontuacao rota={rotaSelecionada} estilo={estilosRotas[indiceSelecionado]} alertasDisponiveis={alertasDisponiveis} />{dadosDesatualizados && <p className="mt-2 text-xs font-semibold">Pontuação da última pesquisa. Atualize o cálculo.</p>}</>
                    ) : item.titulo === 'Ocorrências registradas' ? (
                      <DetalhesOcorrencias ocorrencias={rotaSelecionada.ocorrencias} />
                    ) : item.titulo === 'Locais de apoio' ? (
                      <DetalhesApoio locais={rotaSelecionada.locais_apoio} />
                    ) : (
                      null
                    )}
                  </div>

                </details>
              )
            })}

          </div>

        </section>

        {/* AVISO SOBRE O SCORE */}
        <div className="mt-7 flex items-center justify-center gap-2 text-center text-xs leading-relaxed text-marinho/65">

          <Info size={16} className="shrink-0" />

          <p>
            O Score de Contexto auxilia na tomada de decisão,
            mas não garante segurança.
          </p>

        </div>

      </div>

    </main>
  )
}

export default Trajeto
