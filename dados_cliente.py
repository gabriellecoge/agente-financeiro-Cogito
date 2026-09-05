"""Lógica compartilhada de identificação e isolamento de cliente.

Usada tanto pelo agente.py (Claude API) quanto pelo agente_local.py (Ollama) -
mantida em um único lugar porque é a parte crítica de segurança/privacidade:
qualquer bug de isolamento aqui afeta os dois agentes ao mesmo tempo.
"""

import csv
import json
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).parent
SYSTEM_PROMPT_PATH = BASE_DIR / "system-prompt-educador-financeiro.md"
PRODUTOS_PATH = BASE_DIR / "produtos_financeiros.json"
PERFIS_PATH = BASE_DIR / "perfil_investidor.json"
CLIENTES_PATH = BASE_DIR / "clientes.csv"
HISTORICO_PATH = BASE_DIR / "historico_atendimentos.csv"

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


def buscar_por_nome(nome: str, clientes: list[dict]) -> list[dict]:
    """Retorna todos os registros cujo nome bate com o informado (normalizado)."""
    nome_norm = normalizar(nome)
    return [registro for registro in clientes if normalizar(registro["nome"]) == nome_norm]


def desambiguar_por_id(candidatos: list[dict]) -> dict | None:
    """Usada só quando dois ou mais clientes têm o mesmo nome.

    O cliente_id aqui serve apenas para escolher ENTRE os candidatos que já
    bateram pelo nome - nunca aceita um cliente_id de fora desse grupo, então
    não dá pra "pular" a etapa do nome só sabendo um ID.
    """
    print(f"\nEncontrei {len(candidatos)} clientes com esse nome. Para confirmar, me diga seu cliente_id.")
    cliente_id = input("cliente_id: ").strip().upper()
    for candidato in candidatos:
        if candidato["cliente_id"].strip().upper() == cliente_id:
            return candidato
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


def montar_system_prompt_anonimo(produtos: list[dict]) -> str:
    """Versão do system prompt sem nenhum dado pessoal de cliente.

    Usada quando a pessoa opta por não se identificar ("Prefiro não dizer"):
    o agente continua funcionando como educador financeiro geral, só que sem
    acesso a perfil, histórico ou cadastro de ninguém.
    """
    base = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    bloco_dados = f"""

## Sem cliente identificado nesta conversa

A pessoa optou por não se identificar. Não há registro de cliente disponível
- responda de forma genérica, sem supor perfil, objetivos ou histórico. Se a
pergunta depender de dados pessoais (ex.: "isso serve pro meu perfil?"),
explique que precisaria da identificação para personalizar, mas continue
ajudando com a explicação geral.

## Catálogo de produtos financeiros (referência pública)

```json
{json.dumps(produtos, ensure_ascii=False, indent=2)}
```
"""
    return base + bloco_dados


def montar_system_prompt_novo_cliente(nome: str, perfil_autodeclarado: dict, produtos: list[dict]) -> str:
    """Versão do system prompt para gente que não está na base (cliente novo).

    Os dados vêm de perguntas feitas na própria conversa (faixas de
    patrimônio/renda, objetivo, perfil de risco) - existem só durante a
    sessão, não são salvos em nenhum arquivo. São marcados explicitamente
    como autodeclarados e não verificados, para o agente não tratar faixas
    aproximadas como números exatos e auditados como os da base oficial.
    """
    base = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    dados = {"nome": nome, **perfil_autodeclarado}
    bloco_dados = f"""

## Cliente novo (não está na base oficial) - dados autodeclarados nesta conversa

Esta pessoa não tem cadastro na base de clientes. As informações abaixo
foram fornecidas por ela mesma no início desta conversa (faixas aproximadas,
não valores exatos) e existem só nesta sessão - não foram salvas em nenhum
arquivo nem verificadas. Trate como direcional, não como dado auditado:

```json
{json.dumps(dados, ensure_ascii=False, indent=2)}
```

Use isso só para calibrar a explicação (igual vale para clientes da base
oficial - ver seção "Como usar perfil + produtos juntos" acima). Campos
marcados como "Não informado" significam que a pessoa preferiu não
responder - não insista, não pressuponha.

## Catálogo de produtos financeiros (referência pública)

```json
{json.dumps(produtos, ensure_ascii=False, indent=2)}
```
"""
    return base + bloco_dados


def solicitar_identificacao(clientes: list[dict]) -> dict:
    """Identifica o cliente pelo nome completo.

    Caso raro: se o nome bater com mais de um cliente (nomes duplicados na
    base), pede o cliente_id só para desempatar entre esses candidatos -
    ver desambiguar_por_id().
    """
    import sys

    print("Antes de começar, preciso confirmar quem está falando comigo.\n")
    for tentativa in range(1, MAX_TENTATIVAS_IDENTIFICACAO + 1):
        nome = input("Nome completo: ").strip()
        candidatos = buscar_por_nome(nome, clientes)

        cliente = None
        if len(candidatos) == 1:
            cliente = candidatos[0]
        elif len(candidatos) > 1:
            cliente = desambiguar_por_id(candidatos)

        if cliente:
            primeiro_nome = cliente["nome"].split()[0]
            print(f"\nIdentificação confirmada. Olá, {primeiro_nome}!\n")
            return cliente

        restantes = MAX_TENTATIVAS_IDENTIFICACAO - tentativa
        if restantes > 0:
            print(
                f"\nNão consegui confirmar esse nome. Confira e tente de novo. "
                f"({restantes} tentativa(s) restante(s))\n"
            )
    print("\nNão foi possível confirmar sua identidade. Encerrando.")
    sys.exit(1)


def carregar_tudo() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Retorna (clientes, perfis, historico, produtos)."""
    clientes = carregar_csv(CLIENTES_PATH)
    perfis = carregar_json(PERFIS_PATH)
    historico = carregar_csv(HISTORICO_PATH)
    produtos = carregar_json(PRODUTOS_PATH)
    return clientes, perfis, historico, produtos
