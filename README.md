# Agente Financeiro — Educador Financeiro

Protótipo de uma assistente virtual de **educação financeira** — não de consultoria de investimentos. O objetivo não é dar respostas prontas nem recomendar produtos, e sim ajudar pessoas iniciantes ou intermediárias (autônomos, MEIs, pequenos empresários, curiosos no assunto) a entender como o mercado financeiro funciona, para que tomem as próprias decisões com mais autonomia e confiança.

## O que tem aqui

- [`system-prompt-educador-financeiro.md`](./system-prompt-educador-financeiro.md) — o system prompt completo: identidade, público-alvo, tom de voz, regras do que o agente faz e nunca faz, estratégias de segurança e anti-alucinação, e as regras de identificação/isolamento de cliente para o cenário de atendimento individual.
- [`agente.py`](./agente.py) — implementação em Python (Claude API) do agente: identifica o cliente por nome + `cliente_id`, filtra os dados dele em código e conversa via chat no terminal.
- [`requirements.txt`](./requirements.txt) — dependências do `agente.py`.

## Como usar

### Opção 1 — Claude Project (protótipo rápido, sem código)

1. Crie um **Claude Project** no [claude.ai](https://claude.ai).
2. Cole o conteúdo de `system-prompt-educador-financeiro.md` nas **Custom Instructions** do Project.
3. Suba os arquivos de conhecimento do projeto (catálogo de produtos, perfis de investidor, etc. — não incluídos neste repositório, veja abaixo).

⚠️ Nessa opção, o isolamento por cliente depende só da instrução de prompt (ver aviso de arquitetura abaixo).

### Opção 2 — Agente em Python (`agente.py`), com isolamento real por cliente

Este script implementa a identificação de cliente e filtra os dados **em código**, antes de qualquer chamada à API — só o registro do cliente identificado entra no prompt, os outros 29 nunca chegam ao modelo.

```bash
pip install -r requirements.txt
```

Defina sua chave da API (não peça para o agente digitar por você — configure localmente):

```bash
export ANTHROPIC_API_KEY="sua-chave-aqui"
```

Rode o agente (precisa dos arquivos `clientes.csv`, `perfil_investidor.json`, `historico_atendimentos.csv` e `produtos_financeiros.json` na mesma pasta — eles ficam só localmente, fora do repositório):

```bash
python agente.py
```

O script pede **nome completo + `cliente_id`** antes de qualquer coisa, valida os dois contra `clientes.csv` e só então inicia a conversa — usando exclusivamente o registro daquele cliente.

## Sobre os dados

Este repositório **não inclui** os arquivos de dados usados como base de conhecimento (`produtos_financeiros.json`, `perfil_investidor.json`, `clientes.csv`, `historico_atendimentos.csv`, `transacoes.csv`). Eles contêm dados fictícios de clientes (nome, renda, patrimônio, perfil de risco, histórico de atendimento) gerados para prototipagem, e ficam de fora do repositório para não expor esse formato de dado publicamente — mesmo sendo sintético.

O system prompt já foi desenhado considerando esses arquivos: trata `produtos_financeiros.json` como conteúdo de referência público, e os demais como dado pessoal sujeito a regras de identificação e isolamento por cliente (veja a seção "Identificação e isolamento do cliente" no system prompt).

⚠️ **Nota de arquitetura:** no Claude Project (Opção 1), as regras de isolamento por cliente no system prompt são só um controle de comportamento do modelo — qualquer pessoa com acesso ao projeto enxerga o mesmo conjunto de arquivos de conhecimento com os 30 registros. O `agente.py` (Opção 2) resolve isso na prática: a separação acontece na camada de aplicação (identificação + filtro dos dados em Python, antes da chamada à API) — só o registro do cliente identificado é injetado no prompt daquela conversa.

## Regras principais do agente

- Nunca recomenda comprar, vender ou manter um ativo/produto específico.
- Nunca monta carteira nem sugere alocação para o caso pessoal de alguém.
- Sempre explica o "porquê", não só o "o quê" — o objetivo é formar autonomia, não dependência do agente.
- Admite quando não sabe algo, em vez de inventar dados ou números.
- Não lida com dados sensíveis (CPF, senha, dados bancários) nem com dados de outros clientes da base.
