.PHONY: format lint-fix verify superverify integration

format:
	uv run format

lint-fix:
	uv run lint-fix

verify:
	uv run verify

integration:
	uv run pytest tests/integration/ -v --tb=short

super-verify:
	uv run format
	uv run lint-fix
	uv run verify
