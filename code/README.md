# Test Service Backend

Implementacion FastAPI del Test Service. El paquete de aplicacion vive en
`test_service/`; el punto de entrada ASGI es `test_service.main:app`.

## Requisitos

- Python `3.12.12`.
- uv `0.10.6`.

Las versiones estan fijadas en `.tool-versions`. Si usas asdf, instalalas con:

```bash
asdf install
```

## Preparar El Entorno

Desde este directorio, instala las dependencias de desarrollo bloqueadas:

```bash
uv sync --extra dev --locked
```

## Ejecutar El Servicio

```bash
uv run uvicorn test_service.main:app --reload
```

El servidor queda disponible en `http://127.0.0.1:8000`; la documentacion
interactiva de FastAPI se sirve en `http://127.0.0.1:8000/docs`.

## Pruebas Y Calidad

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Contrato Y Codigo Generado

El contrato OpenAPI consumido y el generador estan declarados en
`pyproject.toml`, bajo `[tool.openapi-contracts]`. El backend fija:

- la Release inmutable del contrato y su SHA-256;
- la Release inmutable de `openapi-contract-toolkit`;
- el wrapper y la version de OpenAPI Generator;
- el directorio y paquete del servidor generado.

La guia para sincronizar contratos, actualizar versiones y generar servidores
o clientes se mantiene en el README de
`openapi-contract-toolkit`. No edites manualmente el contrato descargado ni el
codigo situado en `test_service/generated/`.

El script `scripts/generate_openapi.sh` es heredado y no debe usarse para nuevo
desarrollo. La interfaz vigente es el toolkit configurado en `pyproject.toml`.
