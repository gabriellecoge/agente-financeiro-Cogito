# Base de Conhecimento

## Dados Utilizados

| Arquivo | Formato | Utilização no Agente |
|---------|---------|---------------------|
| `clientes.csv` | CSV | Identificação (nome + `cliente_id`) e dados cadastrais (idade, cidade, profissão, renda) do cliente oficial |
| `perfil_investidor.json` | JSON | Perfil de risco, objetivo, horizonte e patrimônio do cliente oficial — usado só para **calibrar a explicação**, nunca para recomendar |
| `historico_atendimentos.csv` | CSV | Histórico de atendimentos anteriores do cliente oficial — contexto de conversa, não usado para decisão |
| `produtos_financeiros.json` | JSON | Catálogo de produtos (tipo, risco, liquidez, rentabilidade estimada, taxas, perfil indicado) — conteúdo de referência **público**, igual para todo mundo |
| `transacoes.csv` | CSV | Disponível na base mockada, mas **não utilizado** nesta versão — decisão de escopo para manter o protótipo focado em perfil/objetivo em vez de análise granular de gastos. Fica como próximo passo natural (ex.: "em que você mais gasta") |

> Diferente do dataset de exemplo do desafio, aqui `clientes.csv`, `perfil_investidor.json` e `historico_atendimentos.csv` já vieram como arquivos separados por natureza (cadastro / perfil / histórico) em vez de um único "perfil do cliente" — o que ajudou a pensar o isolamento por `cliente_id` como um filtro explícito em código, não como "tudo num JSON só".

---

## Adaptações nos Dados

> Você modificou ou expandiu os dados mockados? Descreva aqui.

A principal adaptação não foi nos arquivos em si, mas na **origem do perfil**: o desafio original assume que todo cliente já está na base mockada. Na prática, isso trava qualquer pessoa nova. Então o agente ganhou um segundo caminho — quando o nome informado não bate com nenhum `cliente_id`, ele conduz uma coleta curta de perfil **na própria conversa** (faixas aproximadas de patrimônio, renda, investimentos atuais, objetivo, horizonte e perfil de risco), com opção de pular qualquer campo ("Prefiro não dizer" → "Não informado"). Esse perfil autodeclarado:

- Existe só na sessão do navegador — não é salvo em nenhum arquivo, ao contrário dos dados oficiais em CSV/JSON.
- É marcado explicitamente no prompt como "autodeclarado e não verificado" (faixas, não números exatos), para o agente não tratar como dado auditado.
- Segue exatamente as mesmas regras de "nunca recomendar" que o perfil oficial — a origem do dado não muda a regra.

---

## Estratégia de Integração

### Como os dados são carregados?
> Descreva como seu agente acessa a base de conhecimento.

`clientes.csv`, `perfil_investidor.json`, `historico_atendimentos.csv` e `produtos_financeiros.json` são lidos do disco uma vez no início da sessão Streamlit (`dados_cliente.carregar_tudo()`, com `@st.cache_data` para não reler a cada interação). A partir daí, tudo acontece em memória.

### Como os dados são usados no prompt?
> Os dados vão no system prompt? São consultados dinamicamente?

Vão no **system prompt**, montado uma única vez logo depois da identificação (não a cada mensagem). O ponto central: antes de montar o prompt, o código já **filtra** `perfil_investidor` e `historico_atendimentos` pelo `cliente_id` daquela pessoa (`montar_contexto_cliente`) — o modelo nunca recebe a base inteira, só o registro de quem está conversando. `produtos_financeiros.json` entra inteiro, por ser referência pública. Como a API do modelo é sem estado, esse mesmo system prompt é reenviado a cada turno junto com o histórico da conversa.

---

## Exemplo de Contexto Montado

> Mostre um exemplo de como os dados são formatados para o agente.

```json
{
  "cadastro": {
    "cliente_id": "CLI0001",
    "nome": "Ana Beatriz Souza",
    "idade": "50",
    "cidade": "Florianópolis/SC",
    "profissao": "Empresário(a)",
    "renda_mensal": "17402.49"
  },
  "perfil_investidor": {
    "perfil_risco": "Conservador",
    "objetivo_principal": "Aposentadoria",
    "horizonte_investimento": "Curto Prazo (até 1 ano)",
    "tolerancia_a_perdas": "Baixa",
    "aceita_produtos_alta_volatilidade": false
  },
  "historico_atendimentos": [
    { "motivo": "Dúvida sobre Investimentos", "assunto": "Como investir em Tesouro Direto" }
  ]
}
```

Para quem não está na base, o formato é parecido, mas rotulado como autodeclarado:

```json
{
  "nome": "Gabriela Nova",
  "patrimonio_total_aproximado": "R$ 50 mil a R$ 200 mil",
  "renda_mensal_aproximada": "R$ 5 mil a R$ 10 mil",
  "investimentos_atuais": "Não informado",
  "objetivo_principal": "Reserva de Emergência",
  "horizonte_investimento": "Médio Prazo (1 a 5 anos)",
  "perfil_risco_autoavaliado": "Moderado"
}
```
