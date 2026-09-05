"""Agente educador financeiro - protótipo de atendimento individual via Claude API.

Identifica o cliente (nome + cliente_id) e injeta no prompt SOMENTE o registro
dele, filtrado em Python antes de qualquer chamada à API - a separação por
cliente acontece na camada de aplicação, não só via instrução de prompt.
"""

import csv
import json
import os
import sys
import unicodedata
from pathlib import Path

import anthropic

BASE_DIR = Path(__file__).parent
SYSTEM_PROMPT_PATH = BASE_DIR / "system-prompt-educador-financeiro.md"
PRODUTOS_PATH = BASE_DIR / "produtos_financeiros.json"
PERFIS_PATH = BASE_DIR / "perfil_investidor.json"
CLIENTES_PATH = BASE_DIR / "clientes.csv"
HISTORICO_PATH = BASE_DIR / "historico_atendimentos.csv"

MODEL = "claude-opus-5"
MAX_TENTATIVAS_IDENTIFICACAO = 3


def normalizar(texto: str) -> str:
    """Remove acentos e normaliza espaços/caixa para comparar nomes com segurança."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acento.lower().split())


def carregar_json(caminho: Path) -> list[dict]:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def carregar_csv(caminho: Path) -> list[dict]:
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def identificar_cliente(nome: str, cliente_id: str, clientes: list[dict]) -> dict | None:
    """Só confirma a identidade se nome E cliente_id baterem com o mesmo registro.

    Se o cliente_id existir mas o nome não bater (ou vice-versa), retorna None
    sem indicar qual dos dois campos falhou - evita virar um oráculo de
    tentativa-e-erro para descobrir dados de outra pessoa.
    """
    cliente_id_norm = cliente_id.strip().upper()
    nome_norm = normalizar(nome)
    for registro in clientes:
        if registro["cliente_id"].strip().upper() == cliente_id_norm:
            if normalizar(registro["nome"]) == nome_norm:
                return registro
            return None
    return None


def montar_contexto_cliente(cliente_id: str, perfis: list[dict], historico: list[dict]) -> dict:
    """Filtra perfil e histórico para conter só os dados do cliente identificado."""
    perfil = next((p for p in perfis if p["cliente_id"] == cliente_id), None)
    atendimentos = [a for a in historico if a["cliente_id"] == cliente_id]
    return {"perfil_investidor": perfil, "historico_atendimentos": atendimentos}


def montar_system_prompt(cliente: dict, contexto_cliente: dict, produtos: list[dict]) -> str:
    base = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    dados_cliente = {"cadastro": cliente, **contexto_cliente}
    bloco_dados = f"""

## Registro do cliente identificado nesta conversa

Estes são os ÚNICOS dados de cliente disponíveis nesta conversa (já filtrados
por aplicação - não existe acesso a outros `cliente_id` a partir daqui):

```json
{json.dumps(dados_cliente, ensure_ascii=False, indent=2)}
```

## Catálogo de produtos financeiros (referência pública)

```json
{json.dumps(produtos, ensure_ascii=False, indent=2)}
```
"""
    return base + bloco_dados


def solicitar_identificacao(clientes: list[dict]) -> dict:
    print("Antes de começar, preciso confirmar quem está falando comigo.\n")
    for tentativa in range(1, MAX_TENTATIVAS_IDENTIFICACAO + 1):
        nome = input("Nome completo: ").strip()
        cliente_id = input("cliente_id: ").strip()
        cliente = identificar_cliente(nome, cliente_id, clientes)
        if cliente:
            primeiro_nome = cliente["nome"].split()[0]
            print(f"\nIdentificação confirmada. Olá, {primeiro_nome}!\n")
            return cliente
        restantes = MAX_TENTATIVAS_IDENTIFICACAO - tentativa
        if restantes > 0:
            print(
                f"\nNão consegui confirmar esses dados. Confira e tente de novo. "
                f"({restantes} tentativa(s) restante(s))\n"
            )
    print("\nNão foi possível confirmar sua identidade. Encerrando.")
    sys.exit(1)


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Defina a variável de ambiente ANTHROPIC_API_KEY antes de rodar o agente.")
        sys.exit(1)

    clientes = carregar_csv(CLIENTES_PATH)
    perfis = carregar_json(PERFIS_PATH)
    historico = carregar_csv(HISTORICO_PATH)
    produtos = carregar_json(PRODUTOS_PATH)

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
