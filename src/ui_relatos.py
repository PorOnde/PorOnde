from uuid import uuid4

import streamlit as st

from src import config
from src.supabase_db import registrar_relato_supabase


def formulario_relato(ponto):
    """Registra o ponto explicitamente selecionado na rota."""
    st.subheader("Deixe um relato")
    st.caption("Seu relato é enviado para avaliação. Evite nomes e dados pessoais.")
    categoria = st.selectbox(
        "Categoria", config.CATEGORIAS_VALIDADE_HORAS, index=None,
        placeholder="Selecione uma opção",
    )
    roubo_furto = categoria == "Roubo ou furto relatado"
    sabe_horario = roubo_furto and st.checkbox("Sei o horário aproximado")

    with st.form("formulario_relato"):
        descricao = st.text_area("O que aconteceu?", max_chars=config.MAX_CARACTERES_DESCRICAO)
        rua = st.text_input("Nome da rua") if roubo_furto or categoria == "Obras ou bloqueios" else None
        data = st.date_input("Data da ocorrência", value=None) if roubo_furto else None
        horario = st.time_input("Horário aproximado", value=None) if sabe_horario else None
        if not ponto:
            st.caption("Marque no mapa o ponto em que aconteceu.")
        enviar = st.form_submit_button("Enviar relato", disabled=ponto is None, type="primary")

    if not enviar:
        return

    if not categoria or not descricao.strip():
        st.error("Informe a categoria e descreva o que aconteceu.")
        return

    if "id_sessao" not in st.session_state:
        st.session_state["id_sessao"] = str(uuid4())

    try:
        resultado = registrar_relato_supabase(
            categoria, descricao.strip(), ponto["lat"], ponto["lng"],
            st.session_state["id_sessao"], rua=rua,
            data_ocorrencia=data, horario_ocorrencia=horario,
        )
    except Exception:
        st.error("Não foi possível confirmar o envio do relato. Tente novamente mais tarde.")
        return

    if isinstance(resultado, int):
        st.session_state["relato_enviado"] = True
        st.session_state["relatar"] = False
        st.session_state.pop("ponto_relato", None)
        st.rerun()
    else:
        st.error(str(resultado))
