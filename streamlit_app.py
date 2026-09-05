"""Interface web (Streamlit) do agente educador financeiro - via Ollama local.

Reaproveita a identificação/isolamento de dados_cliente.py e o modelo
configurado em agente_local.py (Ollama, sem custo de API). A lógica de
identificação aqui é uma adaptação da de dados_cliente.solicitar_identificacao
para formulários web em vez de input() de terminal - as regras de isolamento
(nome + cliente_id no mesmo registro) são as mesmas.
"""

import ollama
import streamlit as st

from agente_local import MODEL, verificar_ollama_disponivel
from dados_cliente import buscar_por_nome, carregar_tudo, montar_contexto_cliente, montar_system_prompt

st.set_page_config(page_title="Educador Financeiro", page_icon="🤖", layout="centered")

st.markdown(
    """
    <style>
    .app-header {
        background: linear-gradient(135deg, #E4002B 0%, #7A0019 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 0.75rem;
        margin-bottom: 1.5rem;
    }
    .app-header h1 {
        color: #FFFFFF;
        font-size: 1.5rem;
        margin: 0;
    }
    .app-header p {
        color: #F2D9DD;
        margin: 0.25rem 0 0 0;
        font-size: 0.9rem;
    }
    [data-testid="stChatMessage"] {
        background-color: #1C1C1C;
        border-left: 3px solid #E4002B;
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
        <h1>🤖 Educador Financeiro</h1>
        <p>Assistente virtual de educação financeira - modelo local via Ollama, sem custo de API.</p>
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
