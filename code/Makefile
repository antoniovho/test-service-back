.PHONY: test coverage test-coverage sonar format lint-fix verify super-verify integration ci clean

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

## Ejecuta los tests unitarios y genera el informe JUnit XML.
test:
	uv run pytest -v --junitxml=nosetests.xml

## Ejecuta los tests y genera el informe de cobertura XML.
coverage:
	uv run pytest \
		--cov=. \
		--cov-report=term-missing \
		--cov-report=xml:coverage.xml

## Ejecuta los tests y genera JUnit XML + cobertura XML.
test-coverage:
	uv run pytest -v \
		--cov=. \
		--cov-report=term-missing \
		--cov-report=xml:coverage.xml \
		--junitxml=nosetests.xml

# -----------------------------------------------------------------------------
# Calidad
# -----------------------------------------------------------------------------

## Formatea el código.
format:
	uv run format

## Ejecuta el lint y aplica correcciones.
lint-fix:
	uv run lint-fix

## Ejecuta las verificaciones del proyecto.
verify:
	uv run verify

## Ejecuta todas las verificaciones de calidad.
super-verify:
	uv run format
	uv run lint-fix
	uv run verify

# -----------------------------------------------------------------------------
# Tests de integración
# -----------------------------------------------------------------------------

## Ejecuta los tests de integración.
integration:
	uv run pytest tests/integration/ -v --tb=short

# -----------------------------------------------------------------------------
# SonarQube
# -----------------------------------------------------------------------------

## Ejecuta el análisis de SonarQube.
sonar:
	@test -n "$$SONAR_TOKEN" || (echo "SONAR_TOKEN no está definido"; exit 1)
	uv run pysonar

# -----------------------------------------------------------------------------
# CI
# -----------------------------------------------------------------------------

## Ejecuta el pipeline completo.
ci: clean super-verify test-coverage sonar

# -----------------------------------------------------------------------------
# Limpieza
# -----------------------------------------------------------------------------

## Elimina los ficheros generados durante tests y análisis.
clean:
	@echo "🧹 Limpiando archivos generados..."
	@find . -type f \( \
		-name "coverage.xml" \
		-o -name "nosetests.xml" \
		-o -name ".coverage" \
	\) -delete
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	@echo "✅ Limpieza completada."
