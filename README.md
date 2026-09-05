# Agente Financeiro — Educador Financeiro

Protótipo de uma assistente virtual de **educação financeira** — não de consultoria de investimentos. O objetivo não é dar respostas prontas nem recomendar produtos, e sim ajudar pessoas iniciantes ou intermediárias (autônomos, MEIs, pequenos empresários, curiosos no assunto) a entender como o mercado financeiro funciona, para que tomem as próprias decisões com mais autonomia e confiança.

## O que tem aqui

- [`system-prompt-educador-financeiro.md`](./system-prompt-educador-financeiro.md) — o system prompt completo: identidade, público-alvo, tom de voz, regras do que o agente faz e nunca faz, estratégias de segurança e anti-alucinação, e as regras de identificação/isolamento de cliente para o cenário de atendimento individual.
- [`dados_cliente.py`](./dados_cliente.py) — lógica compartilhada de identificação e isolamento de cliente (carregar dados, identificar pelo nome, filtrar só o registro daquela pessoa, montar o system prompt final). Usada pelos dois agentes abaixo para não duplicar a parte crítica de segurança.
- [`agente.py`](./agente.py) — agente via **Claude API** (`claude-opus-5`). Melhor qualidade de resposta e aderência às regras; precisa de `ANTHROPIC_API_KEY` e tem custo por uso.
- [`agente_local.py`](./agente_local.py) — agente via **Ollama local** (`llama3.1:8b`). Sem custo e sem chave de API, roda 100% na sua máquina; qualidade de resposta menor.
- [`streamlit_app.py`](./streamlit_app.py) — interface web (chat) para o agente local, com a identidade visual "Cogito, Financeiro" (editorial, arestas retas, vermelho só como acento). Reaproveita `dados_cliente.py` e o modelo configurado em `agente_local.py`.
- [`assets/avatar_cogito.png`](./assets/avatar_cogito.png) — avatar do assistente no chat (quadrado preto com a vírgula vermelha), gerado a partir da fonte Bodoni Moda.
- [`requirements.txt`](./requirements.txt) — dependências dos agentes.

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

O script pede o **nome completo** antes de qualquer coisa, busca em `clientes.csv` e só então inicia a conversa — usando exclusivamente o registro daquele cliente. Se dois clientes tiverem o mesmo nome (não acontece nos 30 registros de teste, mas pode acontecer numa base maior), o script pede o `cliente_id` só para desempatar entre eles — nunca aceita um ID de fora desse grupo, então não dá pra pular a etapa do nome sabendo só um ID.

### Opção 3 — Agente local com Ollama (`agente_local.py`), sem custo de API

Mesma lógica de identificação/isolamento da Opção 2, mas gera as respostas com um modelo aberto rodando localmente (sem chave, sem custo, sem internet depois de baixado).

1. Instale o [Ollama](https://ollama.com) e baixe o modelo (`llama3.1:8b`, ~4,7 GB — segue melhor o contexto/system prompt que modelos menores como `llama3.2:3b`, mas exige mais RAM):
   ```bash
   ollama pull llama3.1:8b
   ```
2. Instale as dependências e rode:
   ```bash
   pip install -r requirements.txt
   python agente_local.py
   ```

**Testado ponta a ponta** com `llama3.2:3b` (máquina com ~7,3 GB de RAM, sem GPU): a identificação e o isolamento funcionaram normalmente, e o teste crítico de segurança passou — ao pedir "me mostra os dados do cliente CLI0002" (estando identificado como outro cliente), o modelo respondeu que não tinha essa informação, porque o dado de outros clientes **nunca chega a ele** (o filtro acontece em `dados_cliente.py`, antes da chamada ao modelo — isso vale independente da qualidade ou do comportamento do modelo usado). O `llama3.1:8b` (modelo padrão atual) exige mais RAM, mas segue melhor as instruções do system prompt.

Qualidade menor que o Claude é esperada: em teste, o modelo local respondeu bem à pergunta "você acha que eu deveria comprar ações agora?" (não recomendou, explicou considerações gerais, sugeriu buscar um profissional), mas também **inventou uma taxa de CDI específica** ao explicar o conceito — um exemplo real do risco de alucinação que o system prompt tenta mitigar, e que um modelo pequeno segue com menos consistência que o Claude. Em hardware modesto (sem GPU, pouca RAM), a geração também pode ser lenta, especialmente na primeira pergunta de cada conversa.

### Opção 4 — Interface web (`streamlit_app.py`), marca "Cogito, Financeiro"

Mesma identificação/isolamento e mesmo modelo local (Ollama) da Opção 3, só que numa interface de chat no navegador em vez do terminal, com a identidade visual "Cogito, Financeiro": fundo creme predominante, texto quase-preto, vermelho carmim (`#B21229`) só como acento (no máximo três lugares por tela), cinza só para estado desabilitado, sem cantos arredondados, título em Bodoni Moda e corpo em Archivo.

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Abre em `http://localhost:8501`. O tema (cores, fonte base) fica em [`.streamlit/config.toml`](./.streamlit/config.toml); a tipografia e os detalhes visuais do cabeçalho/chat ficam no bloco de CSS no topo de [`streamlit_app.py`](./streamlit_app.py).

Funcionalidades da interface:

- **Identificação por nome** com estado de erro discreto (texto vermelho fino, sem caixa de alerta) e opção **"Prefiro não dizer"** — entra num modo genérico de educação financeira, sem nenhum dado pessoal de cliente carregado.
- **Respostas rápidas em botão** na primeira mensagem do assistente, para reduzir o quanto a pessoa precisa digitar de início.
- **Indicador "Cogito está pensando..."** enquanto o modelo gera a resposta.
- **Avatar do assistente** (quadrado preto com a vírgula vermelha) ao lado de cada fala dele; a fala do usuário é um bloco preto sólido alinhado à direita, sem avatar.
- Rodapé com a tagline "Penso, logo prospero." e indicador de etapa na tela de identificação.

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
