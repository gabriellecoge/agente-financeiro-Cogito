"""Interface web (Streamlit) do agente educador financeiro - via Ollama local.

Reaproveita a identificação/isolamento de dados_cliente.py e o modelo
configurado em agente_local.py (Ollama, sem custo de API). A lógica de
identificação aqui é uma adaptação de dados_cliente.solicitar_identificacao
para formulários web em vez de input() de terminal: identifica pelo nome
completo e só pede cliente_id para desempatar quando há mais de um cliente
com o mesmo nome - as mesmas regras de isolamento de dados_cliente.py.

Identidade visual "Cogito, Financeiro": arestas retas (sem border-radius),
vermelho carmim só como acento pontual, cinza só para estado desabilitado.
"""

import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ollama
import streamlit as st

from agente_local import MODEL, verificar_ollama_disponivel
from dados_cliente import (
    buscar_por_nome,
    carregar_tudo,
    montar_contexto_cliente,
    montar_system_prompt,
    montar_system_prompt_anonimo,
)

AVATAR_ASSISTENTE = str(Path(__file__).parent / "assets" / "avatar_cogito.png")

RESPOSTAS_RAPIDAS = [
    "Dívida no cartão de crédito",
    "Não sobra nada no fim do mês",
    "Quero começar a investir",
]

MENSAGEM_ABERTURA = "Vamos começar pelo que pesa mais. O que mais te tira o sono hoje?"

st.set_page_config(page_title="Cogito, Financeiro", page_icon="🤖", layout="centered")

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@300;400;500;600;700&family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900&display=swap" rel="stylesheet">
    <style>
    :root {
        --cogito-primary: #B21229;
        --cogito-black: #0E0E0E;
        --cogito-black-alt: #1C1A17;
        --cogito-cream: #F3EFE9;
        --cogito-white: #FFFFFF;
        --cogito-border: #D6D0C7;
        --cogito-text-secondary: #6E6A64;
        --cogito-disabled-text: #9A948C;
    }
    html, body, .stApp {
        font-family: 'Archivo', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label, .stApp span, .stApp div {
        color: var(--cogito-black);
    }
    .cogito-header {
        background: var(--cogito-black);
        width: 100vw;
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        margin-bottom: 2.5rem;
    }
    .cogito-header-inner {
        max-width: 46rem;
        margin: 0 auto;
        padding: 1.1rem 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .cogito-brand {
        display: flex;
        align-items: baseline;
        gap: 0.6rem;
    }
    .cogito-brand-name {
        font-family: 'Bodoni Moda', Georgia, serif;
        color: var(--cogito-white) !important;
        font-size: 1.4rem;
        font-weight: 600;
    }
    .cogito-brand-name .comma {
        color: var(--cogito-primary) !important;
    }
    .cogito-brand-divider {
        color: #4A4640 !important;
        font-weight: 300;
    }
    .cogito-brand-sub {
        font-family: 'Archivo', sans-serif;
        color: #C9C3BB !important;
        font-size: 0.72rem;
        letter-spacing: 0.16em;
        font-weight: 600;
    }
    .cogito-header-status {
        font-family: 'Archivo', sans-serif;
        color: #C9C3BB !important;
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .cogito-status-dot {
        width: 6px;
        height: 6px;
        background: #4CAF50;
        display: inline-block;
    }
    .cogito-lead-mark {
        color: var(--cogito-primary) !important;
        font-family: 'Bodoni Moda', Georgia, serif;
        font-size: 2.2rem;
        line-height: 1;
        margin-bottom: 0.25rem;
    }
    .cogito-question {
        font-family: 'Bodoni Moda', Georgia, serif;
        color: var(--cogito-black) !important;
        font-size: 1.7rem;
        font-weight: 600;
        line-height: 1.25;
        margin: 0 0 0.6rem 0;
    }
    .cogito-subtext {
        font-family: 'Archivo', sans-serif;
        color: var(--cogito-text-secondary) !important;
        font-size: 0.9rem;
        margin-bottom: 1.75rem;
    }
    .cogito-field-label {
        font-family: 'Archivo', sans-serif;
        color: var(--cogito-text-secondary) !important;
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        font-weight: 600;
        margin-bottom: 0.3rem;
        text-transform: uppercase;
    }
    [data-testid="stTextInputRootElement"] {
        background: var(--cogito-white) !important;
        border: 1.5px solid var(--cogito-border) !important;
        border-radius: 0 !important;
        box-shadow: none !important;
    }
    [data-testid="stTextInputRootElement"]:focus-within {
        border: 1.5px solid var(--cogito-black) !important;
        box-shadow: 3px 3px 0 0 var(--cogito-black) !important;
    }
    [data-testid="stTextInput"] input {
        background: transparent !important;
        color: var(--cogito-black) !important;
        caret-color: var(--cogito-primary) !important;
        padding: 0.65rem 0.8rem !important;
    }
    [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"],
    [data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primaryFormSubmit"] p,
    [data-testid="stBaseButton-primary"] div, [data-testid="stBaseButton-primaryFormSubmit"] div,
    [data-testid="stBaseButton-primary"] span, [data-testid="stBaseButton-primaryFormSubmit"] span {
        color: var(--cogito-white) !important;
    }
    [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
        background: var(--cogito-black) !important;
        border: none !important;
        border-radius: 0 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-family: 'Archivo', sans-serif !important;
        font-weight: 600 !important;
    }
    [data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover {
        background: var(--cogito-primary) !important;
    }
    [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"],
    [data-testid="stBaseButton-secondary"] p, [data-testid="stBaseButton-secondaryFormSubmit"] p,
    [data-testid="stBaseButton-secondary"] div, [data-testid="stBaseButton-secondaryFormSubmit"] div,
    [data-testid="stBaseButton-secondary"] span, [data-testid="stBaseButton-secondaryFormSubmit"] span {
        color: var(--cogito-black) !important;
    }
    [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"] {
        background: var(--cogito-white) !important;
        border: 1.5px solid var(--cogito-black) !important;
        border-radius: 0 !important;
        font-family: 'Archivo', sans-serif !important;
    }
    [data-testid="stBaseButton-secondary"]:hover, [data-testid="stBaseButton-secondaryFormSubmit"]:hover {
        background: var(--cogito-cream) !important;
    }
    [data-testid="stBaseButton-primary"]:disabled, [data-testid="stBaseButton-primaryFormSubmit"]:disabled,
    [data-testid="stBaseButton-secondary"]:disabled, [data-testid="stBaseButton-secondaryFormSubmit"]:disabled,
    [data-testid="stBaseButton-primary"]:disabled p, [data-testid="stBaseButton-primaryFormSubmit"]:disabled p,
    [data-testid="stBaseButton-secondary"]:disabled p, [data-testid="stBaseButton-secondaryFormSubmit"]:disabled p,
    [data-testid="stBaseButton-primary"]:disabled div, [data-testid="stBaseButton-primaryFormSubmit"]:disabled div,
    [data-testid="stBaseButton-secondary"]:disabled div, [data-testid="stBaseButton-secondaryFormSubmit"]:disabled div {
        background: var(--cogito-border) !important;
        color: var(--cogito-disabled-text) !important;
        border: none !important;
    }
    .cogito-skip {
        font-family: 'Archivo', sans-serif;
        color: var(--cogito-text-secondary) !important;
        font-size: 0.85rem;
        text-decoration: underline;
        background: transparent !important;
        border: none !important;
    }
    .cogito-erro {
        color: var(--cogito-primary) !important;
        font-family: 'Archivo', sans-serif;
        font-size: 0.85rem;
        margin: -0.75rem 0 1rem 0;
    }
    .cogito-footer {
        display: flex;
        justify-content: space-between;
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid var(--cogito-border);
        font-family: 'Archivo', sans-serif;
        font-size: 0.8rem;
        color: var(--cogito-text-secondary) !important;
    }
    .cogito-footer .tag {
        font-style: italic;
    }
    [data-testid="stChatInput"] {
        border-radius: 0 !important;
        border: 1.5px solid var(--cogito-border) !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border: 1.5px solid var(--cogito-black) !important;
        box-shadow: 3px 3px 0 0 var(--cogito-black) !important;
    }
    [data-testid="stChatInput"] textarea {
        caret-color: var(--cogito-primary) !important;
    }
    [data-testid="stChatMessageAvatarUser"] {
        display: none !important;
    }
    [data-testid="stChatMessageAvatarAssistant"], [data-testid="stChatMessageAvatarCustom"] {
        border-radius: 0 !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        justify-content: flex-end;
    }
    [data-testid="stChatMessageContent"] {
        border-radius: 0 !important;
        padding: 0.65rem 0.9rem !important;
    }
    [data-testid="stChatMessageContent"][aria-label="Chat message from user"] {
        background: var(--cogito-black) !important;
        color: var(--cogito-white) !important;
        border-left: none !important;
        max-width: 78%;
        margin-left: auto;
    }
    [data-testid="stChatMessageContent"][aria-label="Chat message from user"] p {
        color: var(--cogito-white) !important;
    }
    [data-testid="stChatMessageContent"][aria-label="Chat message from assistant"] {
        background: var(--cogito-white) !important;
        color: var(--cogito-black) !important;
        border-left: 3px solid var(--cogito-primary) !important;
    }
    [data-testid="stAlert"] {
        background: var(--cogito-white) !important;
        border-radius: 0 !important;
    }
    .cogito-pensando {
        font-family: 'Archivo', sans-serif;
        color: var(--cogito-text-secondary) !important;
        font-size: 0.9rem;
        font-style: italic;
    }
    .cogito-pensando .dot {
        animation: cogito-pulse 1.2s infinite ease-in-out;
        display: inline-block;
    }
    .cogito-pensando .dot:nth-child(2) { animation-delay: 0.2s; }
    .cogito-pensando .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes cogito-pulse {
        0%, 80%, 100% { opacity: 0.25; }
        40% { opacity: 1; }
    }
    </style>
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
if "anonimo" not in st.session_state:
    st.session_state.anonimo = False
if "candidatos" not in st.session_state:
    st.session_state.candidatos = None
if "erro_identificacao" not in st.session_state:
    st.session_state.erro_identificacao = None
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = None
if "mostrar_respostas_rapidas" not in st.session_state:
    st.session_state.mostrar_respostas_rapidas = False
if "pergunta_pendente" not in st.session_state:
    st.session_state.pergunta_pendente = None


def render_header():
    if st.session_state.cliente:
        primeiro_nome = st.session_state.cliente["nome"].split()[0]
        status_html = f'<div class="cogito-header-status">Olá, {primeiro_nome}</div>'
    else:
        status_html = (
            '<div class="cogito-header-status">'
            '<span class="cogito-status-dot"></span>Assistente ativo</div>'
        )
    st.markdown(
        f"""
        <div class="cogito-header">
        <div class="cogito-header-inner">
        <div class="cogito-brand">
        <span class="cogito-brand-name">Cogito<span class="comma">,</span></span>
        <span class="cogito-brand-divider">|</span>
        <span class="cogito-brand-sub">FINANCEIRO</span>
        </div>
        {status_html}
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def iniciar_conversa():
    st.session_state.mensagens = [{"role": "assistant", "content": MENSAGEM_ABERTURA}]
    st.session_state.mostrar_respostas_rapidas = True


def confirmar_cliente(cliente: dict) -> None:
    contexto_cliente = montar_contexto_cliente(cliente["cliente_id"], perfis, historico)
    st.session_state.cliente = cliente
    st.session_state.anonimo = False
    st.session_state.system_prompt = montar_system_prompt(cliente, contexto_cliente, produtos)
    st.session_state.candidatos = None
    st.session_state.erro_identificacao = None
    iniciar_conversa()
    st.rerun()


def confirmar_anonimo() -> None:
    st.session_state.cliente = {"nome": "Visitante", "cliente_id": None}
    st.session_state.anonimo = True
    st.session_state.system_prompt = montar_system_prompt_anonimo(produtos)
    st.session_state.candidatos = None
    st.session_state.erro_identificacao = None
    iniciar_conversa()
    st.rerun()


def tela_identificacao() -> None:
    render_header()
    st.markdown('<div class="cogito-lead-mark">,</div>', unsafe_allow_html=True)
    st.markdown('<p class="cogito-question">Antes da gente começar,<br>como posso te chamar?</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="cogito-subtext">Uso seu nome só para personalizar a conversa. Nada é compartilhado.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="cogito-field-label">Seu nome</div>', unsafe_allow_html=True)
    with st.form("form_identificacao", border=False):
        nome = st.text_input("Seu nome", label_visibility="collapsed")
        col_continuar, col_pular = st.columns([1, 1])
        with col_continuar:
            enviado = st.form_submit_button("Continuar →", type="primary", use_container_width=True)
        with col_pular:
            pular = st.form_submit_button("Prefiro não dizer", type="secondary", use_container_width=True)

    if pular:
        confirmar_anonimo()

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
        st.markdown(
            f'<div class="cogito-erro">▍ {st.session_state.erro_identificacao}</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.candidatos:
        st.info(
            f"Encontrei {len(st.session_state.candidatos)} clientes com esse nome. "
            "Para confirmar, informe seu cliente_id."
        )
        with st.form("form_desambiguacao"):
            cliente_id = st.text_input("cliente_id")
            enviado_id = st.form_submit_button("Confirmar ID", type="primary")

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

    st.markdown(
        """
        <div class="cogito-footer">
        <span class="tag">Penso, logo prospero.</span>
        <span class="step">Etapa 1 de 3</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def enviar_mensagem(texto: str) -> None:
    st.session_state.mensagens.append({"role": "user", "content": texto})
    st.session_state.mostrar_respostas_rapidas = False
    st.session_state.pergunta_pendente = texto
    st.rerun()


def gerar_resposta() -> None:
    mensagens_modelo = [
        {"role": "system", "content": st.session_state.system_prompt},
        *st.session_state.mensagens,
    ]
    with st.chat_message("assistant", avatar=AVATAR_ASSISTENTE):
        placeholder = st.empty()
        placeholder.markdown(
            '<div class="cogito-pensando">Cogito está pensando'
            '<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></div>',
            unsafe_allow_html=True,
        )
        resposta_completa = ""
        try:
            for chunk in ollama.chat(model=MODEL, messages=mensagens_modelo, stream=True):
                pedaco = chunk["message"]["content"]
                resposta_completa += pedaco
                placeholder.markdown(resposta_completa + "▌")
            placeholder.markdown(resposta_completa)
        except ollama.ResponseError as e:
            resposta_completa = f"Erro do Ollama: {e.error}"
            placeholder.error(resposta_completa)
        except ConnectionError:
            resposta_completa = "Não consegui conectar ao Ollama. Ele ainda está rodando?"
            placeholder.error(resposta_completa)
    st.session_state.mensagens.append({"role": "assistant", "content": resposta_completa})
    st.session_state.pergunta_pendente = None


def tela_conversa() -> None:
    render_header()

    for mensagem in st.session_state.mensagens:
        avatar = AVATAR_ASSISTENTE if mensagem["role"] == "assistant" else None
        with st.chat_message(mensagem["role"], avatar=avatar):
            st.markdown(mensagem["content"])

    if st.session_state.mostrar_respostas_rapidas and not st.session_state.pergunta_pendente:
        cols = st.columns(len(RESPOSTAS_RAPIDAS))
        for col, texto in zip(cols, RESPOSTAS_RAPIDAS):
            with col:
                if st.button(texto, key=f"rapida_{texto}", type="secondary", use_container_width=True):
                    enviar_mensagem(texto)

    if st.session_state.pergunta_pendente:
        gerar_resposta()
        st.rerun()

    pergunta = st.chat_input("Escreva sua resposta...")
    if pergunta:
        enviar_mensagem(pergunta)

    with st.sidebar:
        nome_exibicao = st.session_state.cliente["nome"]
        st.markdown(f"### {nome_exibicao}")
        if not st.session_state.anonimo:
            st.caption(f"cliente_id: {st.session_state.cliente['cliente_id']}")
        st.caption(f"Modelo local: {MODEL}")
        if st.button("Trocar de cliente", type="secondary"):
            st.session_state.cliente = None
            st.session_state.anonimo = False
            st.session_state.mensagens = []
            st.session_state.mostrar_respostas_rapidas = False
            st.session_state.pergunta_pendente = None
            st.rerun()


if st.session_state.cliente is None:
    tela_identificacao()
else:
    tela_conversa()
