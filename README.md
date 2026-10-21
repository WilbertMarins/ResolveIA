# ResolveIA

O ResolveIA é uma plataforma multiagente de suporte técnico para uma API fictícia de pagamentos. O sistema será capaz de triar chamados, buscar evidências, propor resoluções fundamentadas e encaminhar casos sensíveis ou incertos para revisão humana.

O projeto é desenvolvido como portfólio técnico usando Specification-Driven Development (SDD). O fluxo atual permite cadastrar e consultar chamados e ingerir documentos técnicos de forma assíncrona, com PostgreSQL, SeaweedFS, RabbitMQ e workers Celery.

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

Crie a configuração local, inicie PostgreSQL, SeaweedFS e RabbitMQ, aplique as migrações e crie o bucket local:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres seaweedfs rabbitmq
uv run alembic upgrade head
uv run python -m resolveia.infrastructure.storage.bootstrap
docker compose up -d --build extraction-worker outbox-dispatcher
```

Por padrão, PostgreSQL usa a porta `5433`, SeaweedFS usa `8333`, RabbitMQ usa `5673` e sua interface de gerenciamento fica em `http://127.0.0.1:15673`. Os volumes nomeados preservam os dados quando os containers são reiniciados. A aplicação não cria tabelas nem buckets automaticamente: o Alembic é a fonte de verdade do schema e o comando de bootstrap prepara explicitamente o bucket.

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

## Base de conhecimento

Envie um documento técnico sintético em Markdown, texto UTF-8 ou PDF:

```bash
curl -X POST "http://127.0.0.1:8001/api/v1/knowledge/documents" \
  -F "file=@payments-api.md;type=text/markdown" \
  -F "product=payments-api" \
  -F "product_version=2.4" \
  -F "document_version=2026.10" \
  -F "document_type=runbook" \
  -F "language=pt-BR" \
  -F "valid_until=2027-10-31"
```

O arquivo pode ter no máximo 10 MiB. A API valida extensão, tipo declarado e conteúdo mínimo, calcula o SHA-256, armazena o original e retorna `201 Created` com o estado `pending_ingestion`. Na mesma transação que conclui o upload, uma outbox registra o trabalho. O dispatcher o publica no RabbitMQ e o worker extrai texto normalizado, mantendo uma unidade para Markdown/texto e uma por página textual de PDF. Chunks, embeddings e OCR continuam fora do escopo.

Consulte o estado usando o UUID retornado pelo upload:

```bash
curl "http://127.0.0.1:8001/api/v1/knowledge/documents/d39a3706-fd8e-4c93-b550-221e3b7d8a91"
```

A consulta apresenta `pending_ingestion`, `processing`, `extracted` ou `ingestion_failed`. Quando concluída, inclui somente quantidades de segmentos e caracteres e o horário da extração. Conteúdo, bucket, chave, lease e tentativas não são expostos.

Para executar os processos fora do Compose durante o desenvolvimento:

```bash
uv run celery --app=resolveia.infrastructure.messaging.celery_app:celery_app worker --loglevel=INFO --queues=knowledge-extraction
uv run python -m resolveia.infrastructure.messaging.dispatcher
```

## Health checks

Os endpoints operacionais não usam o prefixo versionado da API:

```bash
curl "http://127.0.0.1:8001/health/live"
curl "http://127.0.0.1:8001/health/ready"
```

- `/health/live` confirma que o processo consegue responder HTTP e não consulta dependências.
- `/health/ready` verifica PostgreSQL e o bucket do object storage e retorna `503` quando qualquer dependência obrigatória não está disponível dentro de seu timeout. RabbitMQ não participa da readiness da API porque a outbox aceita o trabalho enquanto o broker está indisponível.

Os timeouts podem ser alterados por `DATABASE_HEALTH_TIMEOUT_SECONDS`, `OBJECT_STORAGE_HEALTH_TIMEOUT_SECONDS` e `OBJECT_STORAGE_OPERATION_TIMEOUT_SECONDS`. As respostas não expõem URLs, credenciais, bucket, chaves ou mensagens internas dos provedores.

## Estrutura inicial

```text
ResolveIA/
├── alembic/             # migrações do schema relacional
├── .github/workflows/   # integração contínua
├── docs/                # templates e documentação técnica
├── src/resolveia/       # pacote Python
├── tests/               # testes automatizados
├── AGENTS.md            # instruções permanentes do repositório
├── compose.yml           # infraestrutura e processos assíncronos locais
├── Dockerfile            # imagem compartilhada por worker e dispatcher
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
5. commits pequenos e coesos são criados para a spec.

As regras obrigatórias para agentes e colaboradores estão em [AGENTS.md](AGENTS.md).
