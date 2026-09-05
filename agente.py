"""Agente educador financeiro - protótipo de atendimento individual via Claude API.

Identifica o cliente (nome + cliente_id) e injeta no prompt SOMENTE o registro
dele, filtrado em Python antes de qualquer chamada à API - a separação por
cliente acontece na camada de aplicação, não só via instrução de prompt.

A lógica de identificação/isolamento fica em dados_cliente.py, compartilhada
com agente_local.py (versão Ollama, sem custo de API).
"""

import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import anthropic

from dados_cliente import carregar_tudo, montar_contexto_cliente, montar_system_prompt, solicitar_identificacao

MODEL = "claude-opus-5"


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Defina a variável de ambiente ANTHROPIC_API_KEY antes de rodar o agente.")
        sys.exit(1)

    clientes, perfis, historico, produtos = carregar_tudo()

    cliente = solicitar_identificacao(clientes)
    contexto_cliente = montar_contexto_cliente(cliente["cliente_id"], perfis, historico)
    system_prompt = montar_system_prompt(cliente, contexto_cliente, produtos)

    client = anthropic.Anthropic()
    mensagens: list[dict] = []

    print("Pode perguntar o que quiser sobre investimentos e finanças. Digite 'sair' para encerrar.\n")

    while True:
        try:
            pergunta = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté a próxima!")
            break

        if pergunta.lower() in {"sair", "exit", "quit"}:
            print("Até a próxima!")
            break
        if not pergunta:
            continue

        mensagens.append({"role": "user", "content": pergunta})

        print("Agente: ", end="", flush=True)
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                output_config={"effort": "medium"},
                messages=mensagens,
            ) as stream:
                for texto in stream.text_stream:
                    print(texto, end="", flush=True)
                resposta = stream.get_final_message()
        except anthropic.AuthenticationError:
            print("\nChave da API inválida. Confira ANTHROPIC_API_KEY.")
            break
        except anthropic.RateLimitError:
            print("\nLimite de requisições atingido. Tente novamente em instantes.")
            mensagens.pop()
            continue
        except anthropic.APIConnectionError:
            print("\nErro de conexão. Confira sua internet.")
            mensagens.pop()
            continue
        except anthropic.APIStatusError as e:
            print(f"\nErro da API ({e.status_code}): {e.message}")
            mensagens.pop()
            continue

        print("\n")
        # Mantém o content completo (incl. blocos de thinking) para continuidade correta
        mensagens.append({"role": "assistant", "content": resposta.content})


if __name__ == "__main__":
    main()
