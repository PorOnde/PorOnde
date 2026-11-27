const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')
const CHAVE_SESSAO = 'poronde_id_sessao_v1'

// Identificador anônimo, compartilhado pelas próximas ações da comunidade.
// Não representa autenticação e não impede fraudes por si só.
export function obterIdSessao() {
  try {
    let id = localStorage.getItem(CHAVE_SESSAO)
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem(CHAVE_SESSAO, id)
    }
    return id
  } catch {
    throw new Error('Não foi possível criar a sessão. Permita o armazenamento do navegador e use localhost ou HTTPS.')
  }
}

export async function enviarRelato(relato) {
  const id_sessao = obterIdSessao()
  const controle = new AbortController()
  const limite = setTimeout(() => controle.abort(), 30000)
  try {
    const resposta = await fetch(`${API_URL}/api/relatos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...relato, id_sessao }),
      signal: controle.signal,
    })
    const dados = await resposta.json().catch(() => null)
    if (resposta.status >= 500) {
      throw new Error('Não foi possível confirmar o envio. Verifique se o relato foi registrado antes de tentar novamente.')
    }
    if (!resposta.ok) {
      throw new Error(typeof dados?.detail === 'string' ? dados.detail : 'Confira os dados do relato e tente novamente.')
    }
    if (resposta.status !== 201 || dados?.status !== 'pendente' || dados?.id == null) {
      throw new Error('Resposta inesperada. Verifique se o relato foi registrado antes de reenviar.')
    }
    return dados
  } catch (erro) {
    if (controle.signal.aborted || erro instanceof TypeError) {
      throw new Error('Não foi possível confirmar o envio por falha de comunicação. O relato pode ter sido registrado; verifique antes de reenviar.')
    }
    throw erro
  } finally {
    clearTimeout(limite)
  }
}

async function consultarComunidade(caminho, opcoes = {}) {
  const controle = new AbortController()
  const limite = setTimeout(() => controle.abort(), 30000)
  try {
    const resposta = await fetch(`${API_URL}${caminho}`, { ...opcoes, signal: controle.signal })
    const dados = await resposta.json().catch(() => null)
    if (!resposta.ok) {
      throw new Error(typeof dados?.detail === 'string' ? dados.detail : 'Não foi possível concluir a consulta comunitária.')
    }
    return dados
  } catch (erro) {
    if (controle.signal.aborted || erro instanceof TypeError) {
      throw new Error('Falha de comunicação com a comunidade. Atualize os dados antes de repetir uma ação.')
    }
    throw erro
  } finally {
    clearTimeout(limite)
  }
}

export async function listarComunidade() {
  const dados = await consultarComunidade('/api/comunidade/relatos')
  if (!Array.isArray(dados?.relatos)) throw new Error('Resposta comunitária inválida.')
  return dados.relatos
}

export async function votarRelato(id, voto) {
  const dados = await consultarComunidade(`/api/comunidade/relatos/${encodeURIComponent(id)}/voto`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_sessao: obterIdSessao(), voto }),
  })
  if (dados?.status !== 'registrado') throw new Error('Não foi possível confirmar o voto.')
  return dados
}


export async function listarContextoComunidade() {
  const dados = await consultarComunidade('/api/comunidade/relatos')
  if (!Array.isArray(dados?.relatos)) throw new Error('Resposta comunitária inválida.')
  return { relatos: dados.relatos, recorrencias: Array.isArray(dados.recorrencias) ? dados.recorrencias : null, ambiente: dados.ambiente }
}

export async function verificarContinuidade(id, continua) {
  const dados = await consultarComunidade(`/api/comunidade/relatos/${encodeURIComponent(id)}/verificacao`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_sessao: obterIdSessao(), continua }),
  })
  if (dados?.status !== 'registrado') throw new Error('Não foi possível confirmar a verificação.')
  return dados
}
