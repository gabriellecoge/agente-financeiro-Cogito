# Diretrizes do projeto

## Contexto

Este é um protótipo de educação financeira, não de consultoria de investimentos. Leia [README.md](README.md) e [system-prompt-educador-financeiro.md](system-prompt-educador-financeiro.md) antes de alterar o comportamento dos agentes.

## Arquitetura

- [dados_cliente.py](dados_cliente.py) é a camada compartilhada de carregamento, identificação e isolamento. Alterações nela afetam `agente.py` e `agente_local.py` e exigem atenção especial à privacidade.
- [agente_local.py](agente_local.py) usa Ollama e requer o serviço em execução e o modelo `llama3.1:8b` baixado.
- Os caminhos dos dados são resolvidos relativos ao diretório do módulo; preserve esse comportamento.

## Dados e segurança

- Nunca envie ao modelo registros de outros clientes. A identificação é feita pelo nome completo; `cliente_id` só é pedido para desempatar quando o nome bate com mais de um registro, e nunca aceita um ID fora do grupo de candidatos daquele nome.
- Cliente com nome fora da base (`streamlit_app.py`) não é erro - vira coleta de perfil autodeclarado (patrimônio, renda, objetivo, perfil de risco por faixas) só para aquela sessão, via `dados_cliente.montar_system_prompt_novo_cliente`. Nunca persista esses dados em disco; se for adicionar persistência no futuro, trate como decisão de produto/segurança que precisa ser discutida antes (LGPD, backup, criptografia), não como um detalhe de implementação.
- Não coloque chaves, senhas ou dados reais no código, nos prompts ou no controle de versão. Os arquivos CSV/JSON locais são ignorados pelo Git.
- Não transforme o catálogo em recomendação personalizada, nem trate rentabilidades exemplificativas como garantias ou dados atuais. Isso vale igualmente para perfil oficial (base) e perfil autodeclarado (sessão) - o perfil só calibra a explicação, nunca vira indicação.
- Preserve as mensagens de recusa e as regras de educação financeira descritas no system prompt.

## Gotchas conhecidos

- Regras de cor específicas (`.cogito-*`) competem em especificidade com a regra geral `.stApp h1,h2,h3,h4,p,label,span,div { color: ... }` usada para garantir contraste nos widgets nativos do Streamlit. Qualquer cor customizada nova precisa de `!important`, senão a regra geral vence silenciosamente.
- **O system prompt sozinho passa de 5-6 mil tokens** (base + catálogo de produtos + registro do cliente). O padrão do Ollama (`num_ctx=4096`) é insuficiente e trunca o contexto **silenciosamente, sem erro** - o modelo simplesmente responde como se não tivesse os dados do cliente (foi um bug real, reportado pelo usuário: perguntar sobre os próprios investimentos/renda de um cliente da base oficial retornava "não há informações"). Os dois pontos de chamada (`agente_local.py` e `streamlit_app.py`) passam `options={"num_ctx": NUM_CTX}` (definido em `agente_local.py`, hoje 8192) - se o system prompt crescer muito mais, aumente esse valor e confirme com `resp["prompt_eval_count"]` que o prompt inteiro está sendo avaliado, não só uma fração. Como segunda camada de proteção, `dados_cliente.py` monta o bloco do cliente **depois** do catálogo de produtos (não antes) - se o contexto ainda assim estourar, é o catálogo genérico que deve ser cortado primeiro, nunca o registro da pessoa.

## Execução

```bash
python -m pip install -r requirements.txt
python agente_local.py
```

Não há suíte de testes, lint ou configuração de CI. Ao alterar a lógica compartilhada, faça pelo menos uma verificação manual de identificação correta, rejeição de dados inconsistentes e isolamento do contexto antes de executar um agente.

