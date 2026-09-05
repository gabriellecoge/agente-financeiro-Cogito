"""Interface web (Streamlit) do agente educador financeiro - via Ollama local.

Reaproveita a identificação/isolamento de dados_cliente.py e o modelo
configurado em agente_local.py (Ollama, sem custo de API). A lógica de
identificação aqui é uma adaptação de dados_cliente.solicitar_identificacao
para formulários web em vez de input() de terminal: identifica pelo nome
completo e só pede cliente_id para desempatar quando há mais de um cliente
com o mesmo nome - as mesmas regras de isolamento de dados_cliente.py.
"""

import ollama
import streamlit as st

from agente_local import MODEL, verificar_ollama_disponivel
from dados_cliente import buscar_por_nome, carregar_tudo, montar_contexto_cliente, montar_system_prompt

st.set_page_config(page_title="Cogito, Financeiro", page_icon="🤖", layout="centered")

# Paleta e tipografia adaptadas do sistema de marca "Cogito Financeiro":
# vermelho carmim só como acento pontual, nunca como fundo dominante -
# o fundo predominante é o creme, com texto quase-preto e cinzas quentes.
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@300;400;500;600;700&family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900&display=swap" rel="stylesheet">
    <style>
    :root {
        --cogito-primary: #B21229;
        --cogito-primary-hover: #E0203A;
        --cogito-primary-pressed: #6E0A18;
        --cogito-dark: #0E0E0E;
        --cogito-dark-alt: #1C1A17;
        --cogito-cream: #F3EFE9;
        --cogito-cream-alt: #E7E2DA;
        --cogito-border: #D6D0C7;
        --cogito-text-secondary: #6E6A64;
    }
    html, body, .stApp {
        font-family: 'Archivo', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .app-header {
        background: var(--cogito-dark-alt);
        padding: 1.5rem 1.75rem;
        border-radius: 0.75rem;
        margin-bottom: 1.5rem;
        border: 1px solid var(--cogito-dark);
    }
    .app-header h1 {
        font-family: 'Bodoni Moda', Georgia, serif;
        color: var(--cogito-primary);
        font-size: 1.9rem;
        font-weight: 600;
        margin: 0;
    }
    .app-header p {
        font-family: 'Archivo', sans-serif;
        color: #C9C3BB;
        margin: 0.35rem 0 0 0;
        font-size: 0.9rem;
    }
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border-left: 3px solid var(--cogito-primary);
        border-radius: 0.5rem;
        padding: 0.5rem 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="app-header">
        <h1>Cogito, Financeiro</h1>
        <p>Cogito, seu assistente virtual - Penso, logo prospero!</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not verificar_ollama_disponivel():
    st.error(
        f"Não consegui falar com o Ollama ou o modelo `{MODEL}` não está disponível.\n\n"
        f"Confira se o Ollama está rodando e se o modelo foi baixado com `ollama pull {MODEL}`."
    )
    st.stop()


@st.cache_data
def dados():
    return carregar_tudo()


clientes, perfis, historico, produtos = dados()

if "cliente" not in st.session_state:
    st.session_state.cliente = None
if "candidatos" not in st.session_state:
    st.session_state.candidatos = None
if "erro_identificacao" not in st.session_state:
    st.session_state.erro_identificacao = None
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []


def confirmar_cliente(cliente: dict) -> None:
    contexto_cliente = montar_contexto_cliente(cliente["cliente_id"], perfis, historico)
    st.session_state.cliente = cliente
    st.session_state.system_prompt = montar_system_prompt(cliente, contexto_cliente, produtos)
    st.session_state.candidatos = None
    st.session_state.erro_identificacao = None
    st.rerun()


def tela_identificacao() -> None:
    st.subheader("Antes de começar, preciso confirmar quem está falando comigo.")

    with st.form("form_identificacao"):
        nome = st.text_input("Nome completo")
        enviado = st.form_submit_button("Confirmar")

    if enviado:
        candidatos = buscar_por_nome(nome.strip(), clientes) if nome.strip() else []
        if len(candidatos) == 1:
            confirmar_cliente(candidatos[0])
        elif len(candidatos) > 1:
            st.session_state.candidatos = candidatos
            st.session_state.erro_identificacao = None
        else:
            st.session_state.candidatos = None
            st.session_state.erro_identificacao = "Não consegui confirmar esse nome. Confira e tente de novo."

    if st.session_state.erro_identificacao:
        st.error(st.session_state.erro_identificacao)

    if st.session_state.candidatos:
        st.info(
            f"Encontrei {len(st.session_state.candidatos)} clientes com esse nome. "
            "Para confirmar, informe seu cliente_id."
        )
        with st.form("form_desambiguacao"):
            cliente_id = st.text_input("cliente_id")
            enviado_id = st.form_submit_button("Confirmar ID")

        if enviado_id:
            alvo = cliente_id.strip().upper()
            candidato = next(
                (c for c in st.session_state.candidatos if c["cliente_id"].strip().upper() == alvo),
                None,
            )
            if candidato:
                confirmar_cliente(candidato)
            else:
                st.error("Esse cliente_id não corresponde a nenhum dos clientes encontrados com esse nome.")


if st.session_state.cliente is None:
    tela_identificacao()
    st.stop()

cliente = st.session_state.cliente
primeiro_nome = cliente["nome"].split()[0]

with st.sidebar:
    st.markdown(f"### 👤 {cliente['nome']}")
    st.caption(f"cliente_id: {cliente['cliente_id']}")
    st.caption(f"Modelo local: {MODEL}")
    if st.button("Trocar de cliente"):
        st.session_state.cliente = None
        st.session_state.mensagens = []
        st.rerun()

st.success(f"Identificação confirmada. Olá, {primeiro_nome}! Pode perguntar sobre investimentos e finanças.")

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

pergunta = st.chat_input("Digite sua pergunta...")

if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    mensagens_modelo = [{"role": "system", "content": st.session_state.system_prompt}, *st.session_state.mensagens]

    with st.chat_message("assistant"):
        placeholder = st.empty()
        resposta_completa = ""
        try:
            for chunk in ollama.chat(model=MODEL, messages=mensagens_modelo, stream=True):
                resposta_completa += chunk["message"]["content"]
                placeholder.markdown(resposta_completa + "▌")
            placeholder.markdown(resposta_completa)
        except ollama.ResponseError as e:
            resposta_completa = f"Erro do Ollama: {e.error}"
            placeholder.error(resposta_completa)
        except ConnectionError:
            resposta_completa = "Não consegui conectar ao Ollama. Ele ainda está rodando?"
            placeholder.error(resposta_completa)

    st.session_state.mensagens.append({"role": "assistant", "content": resposta_completa})
