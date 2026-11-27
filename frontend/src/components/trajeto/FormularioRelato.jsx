
import { useEffect, useRef, useState } from 'react'
import { enviarRelato } from '../../services/comunidade'

import {
  MessageSquarePlus,
  X,
  Lightbulb,
  Construction,
  Footprints,
  TriangleAlert,
  Users,
  Bus,
  ShieldAlert,
  Waves,
  Ellipsis,
  MapPin,
  CheckCircle2,
} from 'lucide-react'

const categorias = [
  {
    nome: 'Iluminação insuficiente',
    icone: Lightbulb,
    cor: '#B88A00',
  },
  {
    nome: 'Obras ou bloqueios',
    icone: Construction,
    cor: '#EF4444',
  },
  {
    nome: 'Problema na calçada',
    icone: Footprints,
    cor: '#B88A00',
  },
  {
    nome: 'Tumulto ou confusão',
    icone: TriangleAlert,
    cor: '#EF4444',
  },
  {
    nome: 'Aglomeração comum',
    icone: Users,
    cor: '#16834B',
  },
  {
    nome: 'Problema no transporte',
    icone: Bus,
    cor: '#0A2940',
  },
  {
    nome: 'Roubo ou furto relatado',
    icone: ShieldAlert,
    cor: '#EF4444',
  },
  {
    nome: 'Alagamento',
    icone: Waves,
    cor: '#2986C5',
  },
  {
    nome: 'Outros',
    icone: Ellipsis,
    cor: '#64748B',
  },
]

function FormularioRelato({
  ambiente = null,
  pontoRelato,
  selecionandoLocal,
  onEscolherLocal,
  onRelatoEnviado,
}) {
  const modalRef = useRef(null)
  const aguardandoLocal = useRef(false)
  const envioEmCurso = useRef(false)

  const [categoria, setCategoria] = useState('')
  const [descricao, setDescricao] = useState('')
  const [rua, setRua] = useState('')
  const [data, setData] = useState('')
  const [hora, setHora] = useState('')
  const [sabeHorario, setSabeHorario] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [erroEnvio, setErroEnvio] = useState('')
  const [sucesso, setSucesso] = useState(false)

  const hoje = new Date()
  const dataMaxima = [
    hoje.getFullYear(),
    String(hoje.getMonth() + 1).padStart(2, '0'),
    String(hoje.getDate()).padStart(2, '0'),
  ].join('-')

  const estiloCampo =
    'w-full rounded-lg border border-marinho/15 bg-white px-3 py-2.5 text-sm outline-none focus:border-verde-escuro'

  // Reabre o formulário após a seleção do local
  useEffect(() => {
    if (!selecionandoLocal && aguardandoLocal.current) {
      aguardandoLocal.current = false

      if (modalRef.current && !modalRef.current.open) {
        modalRef.current.showModal()
      }
    }
  }, [selecionandoLocal])

  function escolherLocal() {
    aguardandoLocal.current = true
    modalRef.current?.close()
    onEscolherLocal()
  }

  function selecionarCategoria(nome) {
    setCategoria(nome)

    // Limpa informações específicas da categoria anterior
    setRua('')
    setData('')
    setHora('')
    setSabeHorario(false)
  }

  async function submeterRelato(evento) {
    evento.preventDefault()
    if (envioEmCurso.current || sucesso) return
    if (!ambiente) { setErroEnvio('Aguarde a identificação do ambiente antes de enviar.'); return }
    setErroEnvio('')

    if (!categoria || !descricao.trim() || descricao.trim().length > 200) {
      setErroEnvio('Selecione a categoria e informe uma descrição de até 200 caracteres.')
      return
    }
    if (!pontoRelato || !Number.isFinite(pontoRelato.lat) || !Number.isFinite(pontoRelato.lng)) {
      setErroEnvio('Selecione o local da ocorrência no mapa.')
      return
    }
    if (['Obras ou bloqueios', 'Roubo ou furto relatado'].includes(categoria) && !rua.trim()) {
      setErroEnvio('Informe o nome da rua.')
      return
    }
    if (categoria === 'Roubo ou furto relatado' && (!data || (sabeHorario && !hora))) {
      setErroEnvio('Informe a data e, se conhecido, o horário da ocorrência.')
      return
    }

    envioEmCurso.current = true
    setEnviando(true)
    try {
      await enviarRelato({
        categoria,
        descricao: descricao.trim(),
        lat: pontoRelato.lat,
        lon: pontoRelato.lng,
        rua: ['Obras ou bloqueios', 'Roubo ou furto relatado'].includes(categoria) ? rua.trim() : null,
        data_ocorrencia: categoria === 'Roubo ou furto relatado' ? data : null,
        horario_ocorrencia: categoria === 'Roubo ou furto relatado' && sabeHorario ? hora : null,
      })
      setSucesso(true)
      selecionarCategoria('')
      setDescricao('')
      onRelatoEnviado?.()
    } catch (erro) {
      setErroEnvio(erro.message || 'Não foi possível confirmar o envio.')
    } finally {
      envioEmCurso.current = false
      setEnviando(false)
    }
  }

  function abrirFormulario() {
    setSucesso(false)
    setErroEnvio('')
    modalRef.current?.showModal()
  }

  return (
    <>
      {/* BOTÃO FLUTUANTE SOBRE O MAPA */}
      {!selecionandoLocal && (
        <div className="absolute bottom-6 left-4 z-10">
          <button
            type="button"
            onClick={abrirFormulario}
            className="flex items-center gap-2 rounded-xl bg-marinho px-4 py-3 text-sm font-bold text-white shadow-lg transition-colors hover:bg-verde-escuro"
          >
            <MessageSquarePlus size={18} />
            Deixar um relato
          </button>
        </div>
      )}

      {/* JANELA DO FORMULÁRIO */}
      <dialog
        ref={modalRef}
        onCancel={(evento) => { if (envioEmCurso.current) evento.preventDefault() }}
        aria-labelledby="titulo-relato"
        className="modal-relato fixed inset-0 m-auto max-h-[90dvh] w-11/12 max-w-xl overflow-y-auto rounded-2xl border border-marinho/10 bg-fundo p-5 text-marinho shadow-2xl backdrop:bg-marinho/50 sm:p-6"
      >

        {/* CABEÇALHO */}
        <div className="mb-4 flex items-start gap-3">

          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-verde-escuro/10">
            <MessageSquarePlus
              size={22}
              className="text-verde-escuro"
            />
          </div>

          <div className="flex-1">
            <h2
              id="titulo-relato"
              className="text-lg font-extrabold"
            >
              Deixar um relato
            </h2>

            <p className="mt-1 text-xs text-marinho/65">
              Compartilhe informações sobre seu caminho.
            </p>
          </div>

          <button
            type="button"
            onClick={() => modalRef.current?.close()}
            disabled={enviando}
            aria-label="Fechar formulário"
            className="text-marinho/60 transition-colors hover:text-marinho"
          >
            <X size={21} />
          </button>

        </div>

        <form onSubmit={submeterRelato} aria-busy={enviando}>
          <fieldset disabled={enviando || sucesso} className="min-w-0">

          {/* CATEGORIAS */}
          <fieldset>
            <legend className="mb-3 text-sm font-bold">
              O que você encontrou?
            </legend>

            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">

              {categorias.map((item) => {
                const Icone = item.icone
                const selecionada = categoria === item.nome

                return (
                  <label
                    key={item.nome}
                    className={`flex min-h-11 cursor-pointer items-center gap-2.5 rounded-lg border px-3 py-3 transition-colors focus-within:ring-2 focus-within:ring-verde-escuro ${
                      item.nome === 'Outros'
                        ? 'sm:col-span-2'
                        : ''
                    } ${
                      selecionada
                        ? 'border-verde-escuro bg-verde-escuro/10'
                        : 'border-marinho/15 bg-white hover:border-verde-escuro/50'
                    }`}
                  >

                    <input
                      type="radio"
                      name="categoria-relato"
                      value={item.nome}
                      checked={selecionada}
                      onChange={() =>
                        selecionarCategoria(item.nome)
                      }
                      className="sr-only"
                      required
                    />

                    <Icone
                      size={19}
                      strokeWidth={1.8}
                      style={{ color: item.cor }}
                      className="shrink-0"
                      aria-hidden="true"
                    />

                    <span className="flex-1 text-xs font-medium sm:text-sm">
                      {item.nome}
                    </span>

                    {selecionada && (
                      <CheckCircle2
                        size={17}
                        className="shrink-0 text-verde-escuro"
                        aria-hidden="true"
                      />
                    )}

                  </label>
                )
              })}

            </div>
          </fieldset>

          {/* CAMPO ESPECÍFICO: OBRAS OU BLOQUEIOS */}
          {['Obras ou bloqueios', 'Roubo ou furto relatado'].includes(categoria) && (
            <div className="mt-4 animar-campo-relato">
              <label
                htmlFor="rua-relato"
                className="mb-2 block text-sm font-bold"
              >
                Nome da rua
              </label>

              <input
                id="rua-relato"
                type="text"
                maxLength={200}
                value={rua}
                maxLength={200}
                onChange={(evento) => setRua(evento.target.value)}
                placeholder="Informe o nome da rua"
                className={estiloCampo}
                required
              />
            </div>
          )}

          {/* CAMPOS ESPECÍFICOS: ROUBO OU FURTO */}
          {categoria === 'Roubo ou furto relatado' && (
            <div className="mt-4 space-y-3 animar-campo-relato">

              <div>
                <label
                  htmlFor="data-relato"
                  className="mb-2 block text-sm font-bold"
                >
                  Data da ocorrência
                </label>

                <input
                  id="data-relato"
                  type="date"
                  value={data}
                  max={dataMaxima}
                  onChange={(evento) => setData(evento.target.value)}
                  className={estiloCampo}
                  required
                />
              </div>

              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={sabeHorario}
                  onChange={(evento) => {
                    setSabeHorario(evento.target.checked)

                    if (!evento.target.checked) {
                      setHora('')
                    }
                  }}
                  className="accent-verde-escuro"
                />

                Sei o horário aproximado
              </label>

              {sabeHorario && (
                <div className="animar-campo-relato">
                  <label
                    htmlFor="hora-relato"
                    className="mb-2 block text-sm font-bold"
                  >
                    Horário aproximado
                  </label>

                  <input
                    id="hora-relato"
                    type="time"
                    value={hora}
                    onChange={(evento) =>
                      setHora(evento.target.value)
                    }
                    className={estiloCampo}
                    required
                  />
                </div>
              )}

            </div>
          )}

          {/* DIVISÃO */}
          <div className="my-4 h-px bg-marinho/10" />

          {/* LOCAL DA OCORRÊNCIA */}
          <div>
            <h3 className="mb-2 text-sm font-bold">
              Local da ocorrência
            </h3>

            <button
              type="button"
              onClick={escolherLocal}
              className={`flex w-full items-center gap-3 rounded-lg border bg-white px-3 py-3 text-left text-sm transition-colors hover:border-verde-escuro ${
                pontoRelato
                  ? 'border-verde-escuro'
                  : 'border-marinho/15'
              }`}
            >
              <MapPin
                size={19}
                className="shrink-0 text-verde-escuro"
              />

              <span className="flex-1">
                {pontoRelato
                  ? 'Local selecionado — alterar'
                  : 'Selecione o ponto no mapa'}
              </span>

              {pontoRelato && (
                <CheckCircle2
                  size={18}
                  className="text-verde-escuro"
                />
              )}
            </button>

            {pontoRelato && (
              <p className="mt-2 text-xs text-marinho/60">
                Coordenadas: {pontoRelato.lat.toFixed(6)}, {' '}
                {pontoRelato.lng.toFixed(6)}
              </p>
            )}
          </div>

          {/* DESCRIÇÃO */}
          <div className="mt-4">

            <label
              htmlFor="descricao-relato"
              className="mb-2 block text-sm font-bold"
            >
              O que aconteceu?
            </label>

            <textarea
              id="descricao-relato"
              rows={3}
              maxLength={200}
              value={descricao}
              onChange={(evento) =>
                setDescricao(evento.target.value)
              }
              placeholder="Descreva brevemente a situação."
              className={`${estiloCampo} resize-y`}
              required
            />

            <div className="mt-1.5 flex items-center justify-between gap-2 text-xs text-marinho/60">
              <span>Evite nomes e dados pessoais.</span>

              <span
                className={`tabular-nums ${
                  descricao.length === 200
                    ? 'font-bold text-vermelho'
                    : ''
                }`}
              >
                {descricao.length}/200
              </span>
            </div>

          </div>

          </fieldset>

          {erroEnvio && (
            <p role="alert" className="mt-3 rounded-lg border border-vermelho/25 bg-white p-3 text-sm text-[#B52D2D]">
              {erroEnvio}
            </p>
          )}

          {sucesso ? (
            <div className="mt-4 space-y-3">
              <div role="status" className="rounded-lg border border-verde-escuro/25 bg-white p-3 text-sm text-marinho">
                <p className="flex items-center gap-2 font-bold text-verde-escuro">
                  <CheckCircle2 size={19} /> Relato enviado!
                </p>
                <p className="mt-1">Seu relato foi recebido como pendente. Ele ainda não altera o Score de Contexto e depende das regras de validação da comunidade.</p>
              </div>
              <button type="button" onClick={() => modalRef.current?.close()} className="w-full rounded-xl bg-verde-escuro py-3 text-sm font-bold text-white">
                Concluir
              </button>
            </div>
          ) : (
            <>
              <button
                type="submit"
                disabled={enviando || !ambiente}
                className="mt-4 w-full rounded-xl bg-verde-escuro py-3 text-sm font-bold text-white transition-colors disabled:cursor-not-allowed disabled:bg-marinho/10 disabled:text-marinho/40"
              >
                {enviando ? 'Enviando relato...' : 'Enviar relato'}
              </button>
              <p className="mt-2 text-center text-xs leading-relaxed text-marinho/60">
                {ambiente === 'demonstracao' ? 'Relato simulado para o MVP. Não informe dados pessoais. Começa pendente de validação.' : ambiente === 'real' ? 'Envie apenas situações reais. O relato começa pendente de validação.' : 'Aguardando identificação do ambiente.'}
              </p>
            </>
          )}

        </form>

      </dialog>
    </>
  )
}

export default FormularioRelato
