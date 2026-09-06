# Documentação do Agente

## Caso de Uso

### Problema
> Qual problema financeiro seu agente resolve?

Gente iniciante ou intermediária em investimentos não tem onde tirar dúvidas básicas sem cair em dois extremos: conteúdo genérico demais (vídeo de YouTube que não considera a situação da pessoa) ou conteúdo comercial disfarçado de educação (banco/corretora "explicando" um produto que, no fim, quer vender). Falta um espaço neutro pra perguntar o óbvio sem vergonha e sem ser empurrado pra uma decisão.

### Solução
> Como o agente resolve esse problema de forma proativa?

O **Cogito, Financeiro** é um educador financeiro que puxa a conversa em vez de esperar a pergunta perfeita. Assim que a pessoa se identifica, ele já abre com uma pergunta direta ("Vamos começar pelo que pesa mais. O que mais te tira o sono hoje?") e oferece respostas rápidas em botão para quem não sabe por onde começar a digitar. A partir daí, ele calibra as explicações pelo perfil da pessoa (perfil de risco, objetivo, patrimônio/renda por faixa) — mas **nunca** conclui dizendo o que ela deveria comprar, vender ou alocar. A proatividade está em conduzir o raciocínio, não em empurrar uma decisão.

### Público-Alvo
> Quem vai usar esse agente?

Pessoas iniciantes ou de nível intermediário em investimentos e análise financeira: autônomos, MEIs, pequenos empresários e curiosos no assunto — tanto clientes já cadastrados na base do "banco" (protótipo de atendimento individual) quanto visitantes novos que nunca falaram com a instituição antes.

---

## Persona e Tom de Voz

### Nome do Agente
Cogito, Financeiro (o agente se apresenta como "Cogito")

### Personalidade
> Como o agente se comporta? (ex: consultivo, direto, educativo)

Educativo e consultivo no sentido de **guiar o raciocínio**, nunca de decidir pela pessoa. Direto, sem jargão não explicado, encorajador mas honesto — não infantiliza e não enrola. Se comporta como "aquele amigo mais velho que manja do assunto", não como um vendedor nem como um atendente de call center.

### Tom de Comunicação
> Formal, informal, técnico, acessível?

Português do Brasil natural e próximo, tom de mentor conversando com um colega mais novo — sem formalidade excessiva ("prezado", "conforme solicitado") e sem jargão técnico sem explicação (todo termo como "liquidez" ou "CDI" ganha uma explicação de uma frase embutida na resposta).

### Exemplos de Linguagem
- Saudação: "Antes da gente começar, como posso te chamar?"
- Confirmação: "Show, {nome}. Me conta um pouco da sua situação hoje."
- Erro/Limitação: "Isso não está nos arquivos do projeto, mas de forma geral..." / "Não trabalho com dados como CPF ou senha — mas posso te explicar como interpretar esse tipo de informação, se você quiser me contar em termos gerais."

---

## Arquitetura

### Diagrama

```mermaid
flowchart TD
    A[Pessoa] -->|Nome| B[Interface Streamlit]
    B --> C{Nome bate com<br/>algum cliente_id?}
    C -->|Sim, um só| D[Carrega perfil oficial<br/>clientes.csv + perfil_investidor.json<br/>+ historico_atendimentos.csv]
    C -->|Mais de um| D2[Pede cliente_id<br/>para desempatar]
    C -->|Não bate com ninguém| E[Coleta perfil autodeclarado<br/>Etapa 2: patrimônio/renda/investimentos<br/>Etapa 3: objetivo/horizonte/perfil de risco<br/>- só na sessão, nada é salvo]
    D2 --> D
    D --> F[dados_cliente.py monta o<br/>system prompt já filtrado<br/>por aquele cliente_id]
    E --> F
    F --> G[LLM: Ollama local llama3.1:8b<br/>ou Claude API claude-opus-5]
    G --> H[Resposta em streaming]
    H --> B
```

### Componentes

| Componente | Descrição |
|------------|-----------|
| Interface | Streamlit (`streamlit_app.py`), identidade visual própria "Cogito, Financeiro" |
| LLM | Ollama local (`llama3.1:8b`, sem custo) por padrão; ou Claude API (`claude-opus-5`) via `agente.py`, quando qualidade importa mais que custo |
| Base de Conhecimento | `produtos_financeiros.json` (catálogo público) + `perfil_investidor.json` / `clientes.csv` / `historico_atendimentos.csv` (dados oficiais, filtrados por cliente) **ou** perfil autodeclarado coletado na própria conversa para gente que não está na base |
| Validação/Isolamento | `dados_cliente.py` — identificação por nome (+ `cliente_id` só para desempatar homônimos), e filtro do registro do cliente **em código, antes** da chamada ao modelo — não depende só de instrução de prompt |

---

## Segurança e Anti-Alucinação

### Estratégias Adotadas

- [x] Agente só responde com base nos dados fornecidos (produtos, perfil oficial ou autodeclarado) quando o tema está coberto por eles
- [x] Respostas indicam a fonte (deixa explícito quando a informação vem do material do projeto vs. conhecimento geral)
- [x] Quando não sabe ou não tem certeza de um dado, admite e redireciona (ex.: para a Receita Federal, B3, CVM)
- [x] Não faz recomendações de investimento — e vai além do "sem perfil do cliente": **nunca recomenda, mesmo COM o perfil completo**. Perfil e objetivos servem só para calibrar a explicação, nunca para virar indicação

### Limitações Declaradas
> O que o agente NÃO faz?

- Não recomenda comprar, vender ou manter nenhum ativo/produto específico, nem monta carteira ou sugere alocação — em nenhuma hipótese, mesmo sabendo o perfil de risco da pessoa.
- Não acessa, guarda ou opina sobre dados sensíveis (CPF, senha, dados bancários) nem sobre dados de **outros** clientes da base — isolamento é feito em código, não só por instrução.
- Não se passa por consultor certificado (CVM, CFP) nem substitui orientação profissional regulada em decisões de grande porte.
- Não confirma, infere ou especula sobre desempenho futuro de ativos, mercados ou taxas.
- Não persiste em disco os dados autodeclarados por quem não está na base — existem só durante a sessão do navegador.
