# Test Service PostgreSQL Development Environment

This Compose package runs PostgreSQL with an initialization schema aligned with
the current Test Service OpenAPI contract. It is intended for local development
only and does not run the FastAPI application.

## Start

```bash
docker compose up --build -d
docker compose ps
```

PostgreSQL is available at `localhost:55434` with the following local-only
credentials:

```text
Database: test_service
User:     postgresqldba
Password: admin
```

The official PostgreSQL image executes the files in `postgres/init/` in lexical order on
the first initialization of the named volume. To recreate the database from the
current scripts, remove the volume first:

```bash
docker compose down --volumes
docker compose up --build -d
```

Do not reuse the local password outside development. Production credentials must
be provided through the platform's secret management mechanism.
