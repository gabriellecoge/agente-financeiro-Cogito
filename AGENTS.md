# Diretrizes do projeto

## Contexto

Este é um protótipo de educação financeira, não de consultoria de investimentos. Leia [README.md](README.md) e [system-prompt-educador-financeiro.md](system-prompt-educador-financeiro.md) antes de alterar o comportamento dos agentes.

## Arquitetura

- [dados_cliente.py](dados_cliente.py) é a camada compartilhada de carregamento, identificação e isolamento. Alterações nela afetam `agente.py` e `agente_local.py` e exigem atenção especial à privacidade.
- [agente.py](agente.py) usa a API da Anthropic e requer `ANTHROPIC_API_KEY` configurada no ambiente.
- [agente_local.py](agente_local.py) usa Ollama e requer o serviço em execução e o modelo `llama3.1:8b` baixado.
- Os caminhos dos dados são resolvidos relativos ao diretório do módulo; preserve esse comportamento.

## Dados e segurança

- Nunca envie ao modelo registros de outros clientes. A identificação é feita pelo nome completo; `cliente_id` só é pedido para desempatar quando o nome bate com mais de um registro, e nunca aceita um ID fora do grupo de candidatos daquele nome.
- Não coloque chaves, senhas ou dados reais no código, nos prompts ou no controle de versão. Os arquivos CSV/JSON locais são ignorados pelo Git.
- Não transforme o catálogo em recomendação personalizada, nem trate rentabilidades exemplificativas como garantias ou dados atuais.
- Preserve as mensagens de recusa e as regras de educação financeira descritas no system prompt.

## Execução

```bash
python -m pip install -r requirements.txt
python agente_local.py
```

Para usar Claude, configure `ANTHROPIC_API_KEY` no ambiente e execute `python agente.py`. No PowerShell, a configuração temporária pode ser feita com `$env:ANTHROPIC_API_KEY = "sua-chave"`; nunca peça ou registre a chave em arquivos do projeto.

Não há suíte de testes, lint ou configuração de CI. Ao alterar a lógica compartilhada, faça pelo menos uma verificação manual de identificação correta, rejeição de dados inconsistentes e isolamento do contexto antes de executar um agente.

## Estilo

- Mantenha código e documentação em português do Brasil, seguindo os nomes e padrões já usados.
- Prefira mudanças pequenas e compatíveis com as interfaces existentes.
- Atualize o README quando mudar comandos, dependências ou o fluxo de uso.
