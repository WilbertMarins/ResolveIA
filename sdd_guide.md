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

## Estados

| Estado | Significado |
| --- | --- |
| Proposta | Em discussão; implementação proibida |
| Aprovada | Escopo autorizado para implementação |
| Implementada | Alterações prontas para verificação manual |
| Verificada | Responsável confirmou os critérios de aceite |
| Concluída | Revisão didática realizada e commit criado |

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
- Responder às dúvidas e incorporar os ajustes.
- Só iniciar a implementação após aprovação explícita.

### 4. Implementação

- Alterar apenas os arquivos necessários ao escopo aprovado.
- Implementar testes automatizados junto com o comportamento.
- Atualizar documentação e contratos afetados.
- Não aproveitar o incremento para refatorações não relacionadas.

### 5. Verificação manual

- O agente informa os comandos correspondentes aos critérios de aceite.
- O responsável executa testes, lint, formatação, tipos e verificações adicionais.
- O responsável comunica os resultados ao agente.
- Falhas são corrigidas antes de avançar.
- O agente não executa esses comandos, conforme decisão do projeto.

### 6. Estudo e revisão

- Criar `study/SPEC-NNN-<slug>.md` em português.
- Explicar os conceitos e as decisões aplicadas.
- Manter todos os exemplos de código em inglês.
- Incluir perguntas, exercício prático e reflexão pós-implementação.
- Conduzir uma revisão didática após a verificação.

### 7. Commit

- Revisar o diff e excluir artefatos fora do escopo.
- Confirmar que arquivos locais continuam ignorados.
- Criar exatamente um commit por spec.
- Usar Conventional Commits em inglês e anexar `[SPEC-NNN]`.
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
- o incremento é pequeno o suficiente para um único commit coerente.

## Definition of Done

Uma spec só pode ser concluída quando:

- foi aprovada antes da implementação;
- todo o escopo foi implementado;
- os testes necessários foram escritos;
- o responsável executou e confirmou as verificações;
- documentação e contratos afetados foram atualizados;
- o material de estudo local foi produzido;
- a revisão didática foi realizada;
- nenhuma alteração fora do escopo entrou no diff;
- um único commit foi criado com o identificador correto.

## Mudanças após a aprovação

Correções que apenas cumprem um requisito já aprovado não exigem nova aprovação. Mudanças que alterem comportamento, escopo, contrato, arquitetura ou critérios de aceite devem ser documentadas na spec e aprovadas antes da continuação.

## Rastreabilidade sem versionar specs

Como as specs preenchidas não são publicadas, a rastreabilidade permanente depende de:

- identificador da spec na mensagem do commit;
- testes que expressem os critérios de aceite;
- documentação pública atualizada;
- ADRs para decisões arquiteturais duradouras;
- commits pequenos e limitados a um único incremento.

Essa escolha reduz a evidência pública do processo SDD. Por isso, mensagens de commit e testes devem ser especialmente claros.
