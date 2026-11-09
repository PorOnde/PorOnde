import streamlit as st
import base64
import json

from src.ui_relatos import aba_relatos
from src.ui_rotas import aba_rotas
from supabase import create_client


st.set_page_config(
    page_title="PorOnde?",
    page_icon="🗺️",
    layout="wide",
)

# Login opcional para acessar funcionalidades pessoais.
if not st.user.is_logged_in:
    if st.button("Entrar com Google"):
        st.login()

else:
    st.write("Conectado ao PorOnde?")

    token = st.user.tokens.id

    try:
        parte = token.split(".")[1]
        parte += "=" * (-len(parte) % 4)

        dados_token = json.loads(
            base64.urlsafe_b64decode(parte)
        )

        st.write(
            "Cliente Google corresponde:",
            dados_token.get("aud") == st.secrets["auth"]["client_id"],
        )

        st.write(
            "Emissor Google reconhecido:",
            dados_token.get("iss") in (
                "https://accounts.google.com",
                "accounts.google.com",
            ),
        )

        st.write(
            "Token possui nonce:",
            "nonce" in dados_token,
        )

    except (ValueError, IndexError, KeyError):
        st.warning("Não foi possível examinar o formato do token.")

    if token:
        st.success("Token de identidade disponível.")

        if st.button("Testar autenticação no Supabase"):
            try:
                cliente = create_client(
                    st.secrets["supabase"]["url"],
                    st.secrets["supabase"]["key"],
                )

                resposta = cliente.auth.sign_in_with_id_token({
                    "provider": "google",
                    "token": token,
                })

                if resposta.user and resposta.session:
                    st.success(
                        "TESTE APROVADO: Supabase autenticou a conta."
                    )
                else:
                    st.error(
                        "Supabase não confirmou a autenticação."
                    )

            except Exception as erro:
              st.error(f"TESTE FALHOU: {type(erro).__name__}")

              codigo = getattr(erro, "code", None)
              status = getattr(erro, "status", None)

              st.write("Código do erro:", codigo)
              st.write("Status HTTP:", status)

              mensagem = getattr(erro, "message", None)

              if mensagem:
               st.write("Motivo da falha:", mensagem)
            else:
               st.write("Motivo da falha não informado.")
    else:
        st.warning("Token de identidade não disponível.")

    if st.button("Sair da conta"):
        st.logout()

aba_rotas_tab, aba_relatos_tab, aba_salvas_tab, aba_sobre_tab = st.tabs(
    [
        "Rotas",
        "Relatos",
        "Rotas salvas",
        "Sobre",
    ]
)

with aba_rotas_tab:
    aba_rotas()

with aba_relatos_tab:
    aba_relatos()

with aba_salvas_tab:
    st.header("Rotas salvas")
    st.info("Esta funcionalidade será implementada na próxima etapa.")

with aba_sobre_tab:
    st.header("Sobre o PorOnde?")
    st.write(
        "O PorOnde? ajuda a comparar trajetos a pé na Vila Mariana "
        "com informações de distância, tempo, relatos da região "
        "e locais úteis próximos ao caminho."
    )
    st.caption(
        "As informações apresentadas não representam garantia de segurança."
    )