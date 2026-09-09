import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import ollama

from dados_cliente import carregar_tudo, montar_contexto_cliente, montar_system_prompt, solicitar_identificacao

MODEL = "llama3.1:8b"

NUM_CTX = 8192


def verificar_ollama_disponivel() -> bool:
    try:
        modelos = {m["model"] for m in ollama.list().get("models", [])}
    except Exception:
        return False
    return any(m == MODEL or m.startswith(MODEL.split(":")[0] + ":") for m in modelos)


def main():
    if not verificar_ollama_disponivel():
        print(
            "Não consegui falar com o Ollama ou o modelo "
            f"'{MODEL}' não está disponível.\n"
            "Confira se o Ollama está rodando e se o modelo foi baixado:\n"
            f"  ollama pull {MODEL}"
        )
        sys.exit(1)

    clientes, perfis, historico, produtos = carregar_tudo()

    cliente = solicitar_identificacao(clientes)
    contexto_cliente = montar_contexto_cliente(cliente["cliente_id"], perfis, historico)
    system_prompt = montar_system_prompt(cliente, contexto_cliente, produtos)

    mensagens: list[dict] = [{"role": "system", "content": system_prompt}]

    print(f"Modelo local: {MODEL} (via Ollama, sem custo de API).")
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
            resposta_completa = ""
            for chunk in ollama.chat(
                model=MODEL, messages=mensagens, stream=True, options={"num_ctx": NUM_CTX}
            ):
                pedaco = chunk["message"]["content"]
                print(pedaco, end="", flush=True)
                resposta_completa += pedaco
        except ollama.ResponseError as e:
            print(f"\nErro do Ollama: {e.error}")
            mensagens.pop()
            continue
        except ConnectionError:
            print("\nNão consegui conectar ao Ollama. Ele ainda está rodando?")
            mensagens.pop()
            continue

        print("\n")
        mensagens.append({"role": "assistant", "content": resposta_completa})


if __name__ == "__main__":
    main()
