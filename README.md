# ResolveIA

O ResolveIA é uma plataforma multiagente de suporte técnico para uma API fictícia de pagamentos. O sistema será capaz de triar chamados, buscar evidências, propor resoluções fundamentadas e encaminhar casos sensíveis ou incertos para revisão humana.

O projeto é desenvolvido como portfólio técnico usando Specification-Driven Development (SDD). A fundação atual contém apenas estrutura, qualidade e documentação do processo; funcionalidades de negócio serão introduzidas por specs posteriores.

## Princípios

- Evidências, citações e rastreabilidade antes de respostas automáticas.
- Controle humano em casos sensíveis, ambíguos ou de baixa confiança.
- Independência de provedor de LLM e de object storage.
- Incrementos pequenos, verificáveis e associados a uma única spec.
- Dados exclusivamente sintéticos para demonstração.
- Monorepo com limites arquiteturais explícitos.

## Pré-requisitos

- Python 3.12.
- `uv` 0.11.15 ou superior, sem alcançar a versão 0.13.
- Git.

## Preparação do ambiente

Sincronize o ambiente e as dependências de desenvolvimento:

```bash
uv sync --dev
```

O `uv` cria e gerencia o ambiente virtual automaticamente. Não é necessário ativá-lo para executar os comandos abaixo.

## Verificações de qualidade

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
```

Esses comandos são executados automaticamente pela CI em pushes para `main` e em pull requests.

## Estrutura inicial

```text
ResolveIA/
├── .github/workflows/   # integração contínua
├── docs/                # templates e documentação técnica
├── src/resolveia/       # pacote Python
├── tests/               # testes automatizados
├── AGENTS.md            # instruções permanentes do repositório
├── pyproject.toml       # projeto, dependências e ferramentas
└── sdd_guide.md         # processo de desenvolvimento por specs
```

Diretórios serão adicionados somente quando uma spec aprovada introduzir uma necessidade concreta.

## Processo de desenvolvimento

Consulte [sdd_guide.md](sdd_guide.md) para conhecer o ciclo completo. Em resumo:

1. uma spec local é elaborada e discutida;
2. a implementação começa após aprovação explícita;
3. o responsável executa manualmente as verificações;
4. o conteúdo é revisado de forma didática;
5. um único commit é criado para a spec.

As regras obrigatórias para agentes e colaboradores estão em [AGENTS.md](AGENTS.md).
