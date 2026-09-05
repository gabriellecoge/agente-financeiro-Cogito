# Agente Financeiro — Educador Financeiro (Claude Project)

Protótipo de uma assistente virtual de **educação financeira** — não de consultoria de investimentos. O objetivo não é dar respostas prontas nem recomendar produtos, e sim ajudar pessoas iniciantes ou intermediárias (autônomos, MEIs, pequenos empresários, curiosos no assunto) a entender como o mercado financeiro funciona, para que tomem as próprias decisões com mais autonomia e confiança.

## O que tem aqui

- [`system-prompt-educador-financeiro.md`](./system-prompt-educador-financeiro.md) — o system prompt completo: identidade, público-alvo, tom de voz, regras do que o agente faz e nunca faz, estratégias de segurança e anti-alucinação, e as regras de identificação/isolamento de cliente para o cenário de atendimento individual.

## Como usar

1. Crie um **Claude Project** no [claude.ai](https://claude.ai).
2. Cole o conteúdo de `system-prompt-educador-financeiro.md` nas **Custom Instructions** do Project.
3. Suba os arquivos de conhecimento do projeto (catálogo de produtos, perfis de investidor, etc. — não incluídos neste repositório, veja abaixo).

## Sobre os dados

Este repositório **não inclui** os arquivos de dados usados como base de conhecimento (`produtos_financeiros.json`, `perfil_investidor.json`, `clientes.csv`, `historico_atendimentos.csv`, `transacoes.csv`). Eles contêm dados fictícios de clientes (nome, renda, patrimônio, perfil de risco, histórico de atendimento) gerados para prototipagem, e ficam de fora do repositório para não expor esse formato de dado publicamente — mesmo sendo sintético.

O system prompt já foi desenhado considerando esses arquivos: trata `produtos_financeiros.json` como conteúdo de referência público, e os demais como dado pessoal sujeito a regras de identificação e isolamento por cliente (veja a seção "Identificação e isolamento do cliente" no system prompt).

⚠️ **Nota de arquitetura:** as regras de isolamento por cliente no system prompt são um controle de comportamento do modelo, não um controle de acesso real. Um Claude Project expõe o mesmo conjunto de arquivos de conhecimento para qualquer pessoa com acesso ao projeto. Para um produto real com múltiplos clientes, a separação de dados por cliente precisa acontecer na camada de aplicação (autenticação + injeção apenas do registro daquele cliente via API), não só via instrução de prompt.

## Regras principais do agente

- Nunca recomenda comprar, vender ou manter um ativo/produto específico.
- Nunca monta carteira nem sugere alocação para o caso pessoal de alguém.
- Sempre explica o "porquê", não só o "o quê" — o objetivo é formar autonomia, não dependência do agente.
- Admite quando não sabe algo, em vez de inventar dados ou números.
- Não lida com dados sensíveis (CPF, senha, dados bancários) nem com dados de outros clientes da base.
