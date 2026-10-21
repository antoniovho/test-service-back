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

The backend reads its local connection settings from `code/.env`.

The official PostgreSQL image executes the complete base schema from `postgres/init/`
in lexical order on the first initialization of the named volume. To recreate the
database from the current schema, remove the volume first:

```bash
docker compose down --volumes
docker compose up --build -d
```

## Applying a migration to an existing local volume

Files under `postgres/migrations/` are deliberately excluded from initial database
creation. Apply the required migration explicitly to an already initialized
`postgres-data` volume. For example, the Viewer version-identity migration can be run
with:

```bash
docker compose exec -T postgres psql -U postgresqldba -d test_service \
  -f /migrations/21_VIEWER_SYNC_RECORD_VERSION_IDENTITY.sql
```

It upgrades `viewer_sync_record` so its uniqueness includes `entity_version`.
Without it, publishing multiple immutable versions of the same logical entity
fails against the obsolete four-column uniqueness constraint.

Do not reuse the local password outside development. Production credentials must
be provided through the platform's secret management mechanism.
