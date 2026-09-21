# Test Service Backend

Python/FastAPI backend for the Test Service API contract maintained in
`../app-devtools/apis/test-service/rest/openapi-rest.yml`.

The contract is the public interface. Domain behavior is implemented in layers
following the backend implementation guide: domain, application ports, and
inbound/outbound adapters.

## Development

```bash
cd code
asdf install
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run uvicorn test_service.main:app --reload
```
