# SPEC-NNN — Título

## Status

Proposta.

## Contexto

Descreva o problema atual, quem é afetado e por que o incremento é necessário.

## Objetivo

Declare o resultado observável que esta spec deve produzir.

## Escopo

- Item incluído.

## Fora do escopo

- Item explicitamente excluído.

## Atores

- **Ator:** responsabilidade ou interesse neste incremento.

## Glossário

| Termo | Definição |
| --- | --- |
| Exemplo | Definição não ambígua |

## Hipóteses

- Hipótese que ainda não foi confirmada como fato.

## Pré-condições

- Condição necessária antes do fluxo.

## Pós-condições

- Estado observável após a conclusão do fluxo.

## Fluxo principal

1. O ator inicia o fluxo.
2. O sistema responde.

## Fluxos alternativos e falhas

### FA-001 — Nome do cenário

1. Condição que desvia do fluxo principal.
2. Resposta esperada do sistema.

## Regras de negócio

### RN-001 — Nome da regra

Defina a regra de forma determinística e verificável.

## Requisitos funcionais

### RF-001 — Nome do requisito

Descreva o comportamento obrigatório sem prescrever detalhes desnecessários de implementação.

## Requisitos não funcionais

- Defina limites mensuráveis de segurança, desempenho, resiliência, privacidade ou operação quando aplicáveis.

## Contratos e modelos

Descreva entradas, saídas, estados, erros, compatibilidade e exemplos relevantes.

```json
{
  "example_field": "example_value"
}
```

## Critérios de aceite

### CA-001 — Nome do critério

Dado um contexto, quando uma ação ocorrer, então um resultado observável deve ser produzido.

## Estratégia de testes

- Teste unitário necessário.
- Teste de integração necessário.
- Cenários de sucesso, fronteira e falha.
- Comandos que serão executados manualmente pelo responsável.

O agente não executa testes ou ferramentas de qualidade. O responsável comunica os resultados antes do commit.

## Plano de tarefas didáticas

Cada tarefa deve explicar uma ideia principal, produzir um resultado revisável e
caber preferencialmente em até 300 linhas alteradas, sem ultrapassar 500 sem
aprovação explícita.

| Tarefa | Objetivo e conceito | Requisitos/aceite | Dependências | Arquivos previstos | Verificação focada | Commit proposto |
| --- | --- | --- | --- | --- | --- | --- |
| `SPEC-NNN/T01` | Resultado pequeno e conhecimento principal | `RF-001`, `CA-001` | Nenhuma | Caminhos esperados | Comando ou inspeção manual | `type(scope): description [SPEC-NNN/T01]` |

Regras de execução:

- implementar uma tarefa por vez;
- incluir comportamento e testes relacionados na mesma tarefa quando possível;
- apresentar revisão didática e ordem de leitura do diff;
- criar o commit após a confirmação das verificações;
- aguardar a revisão do commit antes de iniciar a tarefa seguinte.

## Telemetria

- Logs, métricas, traces e eventos esperados.
- Dados que precisam ser mascarados ou não podem ser registrados.

## Segurança e privacidade

- Ameaças relevantes e respectivas mitigações.

## Material de estudo esperado

- Conceitos utilizados.
- Decisões e alternativas.
- Perguntas de revisão.
- Exercício prático.
- Reflexão pós-implementação.

O texto deve estar em português e os exemplos de código em inglês.

## Riscos e mitigações

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Exemplo | Consequência | Tratamento |

## Decisões pendentes

- Decisão que precisa ser tomada antes ou durante o incremento.

## Dependências

- Spec, serviço, biblioteca ou decisão necessária.

## Definition of Done

- Todos os critérios de aceite foram confirmados pelo responsável.
- Todas as tarefas foram verificadas e revisadas individualmente.
- Testes, documentação e material de estudo foram produzidos.
- O material foi disponibilizado sem bloquear o fluxo de entrega.
- Cada commit contém `[SPEC-NNN/TNN]` e respeita o limite de tamanho.

## Mensagens de commit propostas

```text
type(scope): concise task description [SPEC-NNN/T01]
```
