
import {
  MapPin,
  ArrowLeftRight,
  Route,
  X,
} from 'lucide-react'

function FormularioTrajeto({
  origem,
  destino,
  setOrigem,
  setDestino,
  onComparar,
}) {

  // Inverte os endereços
  function inverterTrajeto() {
    setOrigem(destino)
    setDestino(origem)
  }

  return (
    <form onSubmit={onComparar}>

      <div className="flex flex-col items-end gap-3 md:flex-row">

        {/* Origem */}
        <div className="w-full min-w-0 flex-1">

          <label
            htmlFor="origem-trajeto"
            className="mb-2 block text-sm font-semibold text-marinho"
          >
            Origem
          </label>

          <div className="flex items-center gap-3 rounded-xl border border-marinho/15 bg-white px-4 py-3 transition-colors focus-within:border-verde-escuro">

            <MapPin
              size={21}
              className="shrink-0 text-verde-escuro"
            />

            <input
              id="origem-trajeto"
              type="text"
              placeholder="De onde você vai sair?"
              value={origem}
              onChange={(evento) => setOrigem(evento.target.value)}
              className="w-full min-w-0 bg-transparent text-sm outline-none"
              required
            />

            {origem && (
              <button
                type="button"
                onClick={() => setOrigem('')}
                aria-label="Limpar origem"
                className="text-marinho/40 hover:text-marinho"
              >
                <X size={16} />
              </button>
            )}

          </div>
        </div>

        {/* Inverter origem e destino */}
        <button
          type="button"
          onClick={inverterTrajeto}
          aria-label="Inverter origem e destino"
          title="Inverter origem e destino"
          className="flex h-12 w-12 shrink-0 items-center justify-center self-center rounded-xl border border-marinho/15 bg-white text-marinho transition-colors hover:border-verde-escuro hover:text-verde-escuro md:self-end"
        >
          <ArrowLeftRight size={20} />
        </button>

        {/* Destino */}
        <div className="w-full min-w-0 flex-1">

          <label
            htmlFor="destino-trajeto"
            className="mb-2 block text-sm font-semibold text-marinho"
          >
            Destino
          </label>

          <div className="flex items-center gap-3 rounded-xl border border-marinho/15 bg-white px-4 py-3 transition-colors focus-within:border-vermelho">

            <MapPin
              size={21}
              className="shrink-0 text-vermelho"
            />

            <input
              id="destino-trajeto"
              type="text"
              placeholder="Para onde você vai?"
              value={destino}
              onChange={(evento) => setDestino(evento.target.value)}
              className="w-full min-w-0 bg-transparent text-sm outline-none"
              required
            />

            {destino && (
              <button
                type="button"
                onClick={() => setDestino('')}
                aria-label="Limpar destino"
                className="text-marinho/40 hover:text-marinho"
              >
                <X size={16} />
              </button>
            )}

          </div>
        </div>

        {/* Comparar */}
        <button
          type="submit"
          className="flex h-12 w-full shrink-0 items-center justify-center gap-2 rounded-xl bg-verde-escuro px-6 text-sm font-bold text-white transition-colors hover:bg-[#106B3D] md:w-auto"
        >
          <Route size={19} />
          Comparar trajetos
        </button>

      </div>

      <p className="mt-3 text-xs leading-relaxed text-marinho/60">
        Informe a origem e o destino na região da Vila Mariana.
      </p>

    </form>
  )
}

export default FormularioTrajeto
