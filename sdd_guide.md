# Guia de Specification-Driven Development

## Objetivo

O ResolveIA utiliza Specification-Driven Development (SDD) para transformar decisões de produto e arquitetura em incrementos pequenos, verificáveis e didáticos. A spec define o contrato do trabalho antes do código; a implementação demonstra que esse contrato foi atendido.

## Artefatos

| Artefato | Local | Versionado | Finalidade |
| --- | --- | --- | --- |
| Instruções permanentes | `AGENTS.md` | Sim | Regras obrigatórias para todo o repositório |
| Guia SDD | `sdd_guide.md` | Sim | Processo e Definition of Done |
| Template | `docs/spec_template.md` | Sim | Estrutura comum das specs |
| Spec preenchida | `docs/specs/` | Não | Contrato local de um incremento |
| Material de estudo | `study/` | Não | Consolidação didática de cada incremento |
| ADR | `docs/adr/` | Sim | Decisão arquitetural duradoura |

## Identificação

As specs recebem identificadores sequenciais com três dígitos:

```text
SPEC-000-foundation.md
SPEC-001-create-ticket.md
SPEC-002-query-ticket.md
```

O identificador deve aparecer na mensagem do commit, mesmo que a spec preenchida permaneça local.

As tarefas de uma spec usam o identificador composto `SPEC-NNN/TNN`:

```text
SPEC-007/T01 — definir o contrato de chunk
SPEC-007/T02 — persistir chunks
SPEC-007/T03 — integrar o processamento ao worker
```

A spec continua sendo a unidade de escopo e produto. A tarefa é a unidade de
implementação, estudo, verificação e commit.

## Estados

| Estado | Significado |
| --- | --- |
| Proposta | Em discussão; implementação proibida |
| Aprovada | Escopo autorizado para implementação |
| Implementada | Alterações prontas para verificação manual |
| Verificada | Responsável confirmou os critérios de aceite |
| Concluída | Material disponibilizado e commit criado |

Se uma mudança material for necessária durante a implementação, a spec volta para Proposta e precisa de nova aprovação.

## Ciclo de uma spec

### 1. Descoberta

- Ler o contexto existente e o estado do repositório.
- Identificar problema, atores, restrições, riscos e decisões pendentes.
- Separar fatos, hipóteses e perguntas.
- Escolher o menor incremento que entregue um resultado demonstrável.

### 2. Especificação

- Criar o arquivo local usando `docs/spec_template.md`.
- Escrever requisitos e critérios de aceite observáveis.
- Declarar explicitamente o que está fora do escopo.
- Descrever estratégia de testes, telemetria e riscos proporcionais ao incremento.
- Evitar decisões técnicas que não sejam necessárias para o comportamento especificado.

### 3. Aprovação

- Apresentar a spec ao responsável pelo projeto.
- Apresentar o plano ordenado de tarefas didáticas, com dependências e resultado
  observável de cada tarefa.
- Responder às dúvidas e incorporar os ajustes.
- Só iniciar a implementação após aprovação explícita da spec e do plano.

### 4. Implementação

- Selecionar apenas a próxima tarefa aprovada e anunciar seu objetivo didático.
- Alterar apenas os arquivos necessários à tarefa corrente.
- Implementar os testes diretamente relacionados junto com o comportamento.
- Atualizar documentação e contratos afetados pela tarefa.
- Não iniciar trabalho de tarefas posteriores para completar antecipadamente a
  spec.
- Não aproveitar a tarefa para refatorações não relacionadas.

### 5. Verificação manual

- O agente informa primeiro as verificações focadas da tarefa e depois, quando
  necessário, as verificações de regressão da spec.
- O responsável executa testes, lint, formatação, tipos e verificações adicionais.
- O responsável comunica os resultados ao agente.
- Falhas são corrigidas antes de avançar.
- O agente não executa esses comandos, conforme decisão do projeto.

### 6. Revisão didática da tarefa

- Explicar o que mudou e por que a solução foi escolhida.
- Sugerir uma ordem curta para leitura do diff: contrato, regra, adaptador e teste.
- Relacionar as alterações aos requisitos e critérios de aceite da spec.
- Destacar uma ou duas perguntas para orientar a revisão manual.
- Criar o commit somente após a confirmação das verificações.
- Informar hash, linhas alteradas e conceito central do commit.
- Aguardar a revisão ou autorização explícita antes da próxima tarefa.

### 7. Material de estudo

- Criar `study/SPEC-NNN-<slug>.md` em português.
- Explicar os conceitos e as decisões aplicadas.
- Manter todos os exemplos de código em inglês.
- Incluir perguntas, exercício prático e reflexão pós-implementação.
- Disponibilizar o material sem aguardar leitura, respostas ou revisão didática.
- O responsável conduz os estudos no próprio ritmo; essa atividade não bloqueia commit ou spec seguinte.

### 8. Commit

- Revisar o diff e excluir artefatos fora do escopo.
- Confirmar que arquivos locais continuam ignorados.
- Criar preferencialmente um commit por tarefa didática.
- Buscar até 300 linhas adicionadas e removidas por commit e não ultrapassar 500
  linhas sem aprovação explícita.
- Se uma tarefa não couber no limite, voltar ao plano e dividi-la antes de seguir.
- Usar Conventional Commits em inglês e anexar `[SPEC-NNN/TNN]` ao commit.
- O responsável inspeciona o commit e realiza o push.

## Critérios de qualidade de uma spec

Uma spec está pronta para aprovação quando:

- o problema e o resultado esperado estão claros;
- o escopo e o fora do escopo são explícitos;
- termos importantes não são ambíguos;
- decisões e hipóteses estão identificadas;
- cada requisito pode ser relacionado a pelo menos um critério de aceite;
- os critérios descrevem resultados observáveis, não detalhes acidentais;
- a estratégia de testes contempla fluxos principal, alternativos e falhas relevantes;
- riscos e decisões pendentes estão registrados;
- existe um plano ordenado de tarefas didáticas;
- cada tarefa possui objetivo, conceito, dependências, arquivos previstos,
  verificação focada e commit proposto;
- cada tarefa cabe em um commit coerente dentro dos limites de tamanho.

## Definition of Done

Uma spec só pode ser concluída quando:

- foi aprovada antes da implementação;
- todo o escopo foi implementado;
- os testes necessários foram escritos;
- o responsável executou e confirmou as verificações;
- documentação e contratos afetados foram atualizados;
- o material de estudo local foi produzido;
- o material de estudo local foi disponibilizado para estudo independente;
- nenhuma alteração fora do escopo entrou no diff;
- todas as tarefas foram revisadas pelo responsável;
- todos os commits foram criados com os identificadores de spec e tarefa corretos;
- cada commit contém preferencialmente até 300 linhas alteradas e, salvo aprovação
  explícita, no máximo 500 linhas adicionadas e removidas.

## Mudanças após a aprovação

Correções que apenas cumprem um requisito já aprovado não exigem nova aprovação. Mudanças que alterem comportamento, escopo, contrato, arquitetura ou critérios de aceite devem ser documentadas na spec e aprovadas antes da continuação.

## Rastreabilidade sem versionar specs

Como as specs preenchidas não são publicadas, a rastreabilidade permanente depende de:

- identificadores da spec e da tarefa na mensagem do commit;
- testes que expressem os critérios de aceite;
- documentação pública atualizada;
- ADRs para decisões arquiteturais duradouras;
- commits pequenos, coesos e limitados a uma única tarefa.

Essa escolha reduz a evidência pública do processo SDD. Por isso, mensagens de commit e testes devem ser especialmente claros.
