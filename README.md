# ResolveIA

O ResolveIA é uma plataforma multiagente de suporte técnico para uma API fictícia de pagamentos. O sistema será capaz de triar chamados, buscar evidências, propor resoluções fundamentadas e encaminhar casos sensíveis ou incertos para revisão humana.

O projeto é desenvolvido como portfólio técnico usando Specification-Driven Development (SDD). O fluxo atual permite cadastrar e consultar chamados por uma API HTTP com persistência em PostgreSQL.

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
- Docker Desktop com Docker Compose.
- Git.

## Preparação do ambiente

Sincronize o ambiente e as dependências de desenvolvimento:

```bash
uv sync --dev
```

O `uv` cria e gerencia o ambiente virtual automaticamente. Não é necessário ativá-lo para executar os comandos abaixo.

Crie a configuração local, inicie o PostgreSQL na porta `5433` e aplique as migrações:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
uv run alembic upgrade head
```

O volume `resolveia_postgres_data` preserva os dados quando o container ou a API é reiniciado. A aplicação não cria tabelas automaticamente; o Alembic é a fonte de verdade do schema.

## Verificações de qualidade

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
```

Esses comandos são executados automaticamente pela CI em pushes para `main` e em pull requests.

## Executando a API

Inicie o servidor de desenvolvimento:

```bash
uv run uvicorn resolveia.presentation.api.app:app --reload --port 8001
```

A documentação interativa estará disponível em `http://127.0.0.1:8001/docs`.

Cadastre um chamado sintético:

```bash
curl -X POST "http://127.0.0.1:8001/api/v1/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Webhook de pagamento não recebido",
    "description": "O pagamento foi confirmado, mas nosso endpoint não recebeu o webhook.",
    "product": "Payments API",
    "product_version": "v2"
  }'
```

O endpoint retorna `201 Created`, um identificador UUID, o estado inicial `received` e o horário de criação em UTC. Os dados permanecem disponíveis após reiniciar a API enquanto o volume do PostgreSQL for preservado.

Use o valor retornado no cabeçalho `Location` para consultar o chamado:

```bash
curl "http://127.0.0.1:8001/api/v1/tickets/550e8400-e29b-41d4-a716-446655440000"
```

A consulta retorna `200 OK` para um chamado existente, `404 Not Found` para um UUID não armazenado e `422 Unprocessable Entity` para um identificador malformado.

## Estrutura inicial

```text
ResolveIA/
├── alembic/             # migrações do schema relacional
├── .github/workflows/   # integração contínua
├── docs/                # templates e documentação técnica
├── src/resolveia/       # pacote Python
├── tests/               # testes automatizados
├── AGENTS.md            # instruções permanentes do repositório
├── compose.yml           # PostgreSQL local
├── pyproject.toml       # projeto, dependências e ferramentas
└── sdd_guide.md         # processo de desenvolvimento por specs
```

Diretórios serão adicionados somente quando uma spec aprovada introduzir uma necessidade concreta.

## Processo de desenvolvimento

Consulte [sdd_guide.md](sdd_guide.md) para conhecer o ciclo completo. Em resumo:

1. uma spec local é elaborada e discutida;
2. a implementação começa após aprovação explícita;
3. o responsável executa manualmente as verificações;
4. o material de estudo é disponibilizado para revisão independente;
5. um único commit é criado para a spec.

As regras obrigatórias para agentes e colaboradores estão em [AGENTS.md](AGENTS.md).
