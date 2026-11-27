const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')

async function consultarAPI(caminho, { timeout = 30000, signal } = {}) {
  const controle = new AbortController()
  const cancelar = () => controle.abort()
  if (signal?.aborted) cancelar()
  signal?.addEventListener('abort', cancelar, { once: true })
  const limite = setTimeout(cancelar, timeout)
  try {
    const resposta = await fetch(`${API_URL}${caminho}`, { signal: controle.signal })
    const dados = await resposta.json().catch(() => null)
    if (!resposta.ok) throw new Error(typeof dados?.detail === 'string' ? dados.detail : 'Não foi possível concluir a solicitação.')
    if (dados == null) throw new Error('Resposta inválida do servidor.')
    return dados
  } catch (erro) {
    if (signal?.aborted) throw erro
    if (controle.signal.aborted) throw new Error('A consulta demorou mais que o esperado. Tente novamente em instantes.')
    if (erro instanceof TypeError) throw new Error('Não foi possível conectar ao servidor.')
    throw erro
  } finally {
    clearTimeout(limite)
    signal?.removeEventListener('abort', cancelar)
  }
}

export async function verificarServidor() {
  return consultarAPI('/api/saude', { timeout: 10000 })
}

export async function geocodificarEndereco(endereco) {
  const parametros = new URLSearchParams({ endereco: endereco.trim() })
  return consultarAPI(`/api/geocodificar?${parametros}`, { timeout: 25000 })
}

export async function buscarRotas(origem, destino) {
  const parametros = new URLSearchParams({
    origem_lat: origem.latitude, origem_lon: origem.longitude,
    destino_lat: destino.latitude, destino_lon: destino.longitude,
  })
  return consultarAPI(`/api/rotas?${parametros}`, { timeout: 60000 })
}

export async function consultarAmbiente() {
  return consultarAPI('/api/ambiente', { timeout: 10000 })
}

export async function sugerirEnderecos(texto, signal) {
  const parametros = new URLSearchParams({ q: texto.trim() })
  const dados = await consultarAPI(`/api/enderecos/sugestoes?${parametros}`, { timeout: 8000, signal })
  return Array.isArray(dados.sugestoes) ? dados.sugestoes : []
}
