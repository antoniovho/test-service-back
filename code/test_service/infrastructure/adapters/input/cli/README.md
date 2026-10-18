# Importación del corpus

`CorpusImporter` carga definiciones de precondiciones y casos de prueba desde
documentos JSON de corpus. Es una adaptación de entrada: convierte el formato
del corpus en comandos de authoring y los persiste usando los mismos casos de
uso que la API REST.

El comando asociado es `test_service.import_corpus`. Debe ejecutarse desde el
directorio `code/`, con la base de datos disponible y con un proyecto activo
creado previamente.

## Importar una selección

Usa `--file` una vez por documento. El importador procesa primero las
precondiciones aunque se indiquen después en la línea de comandos.

```bash
uv run python -m test_service.import_corpus \
  --project-key KAN \
  --requested-by corpus-import \
  --file ../data/preconditions/LITELLM_PROXY_READY.json \
  --file ../data/test_cases/GW-SMK-001.json \
  --dry-run
```

`--dry-run` valida los documentos, comprueba las referencias y calcula el
resultado, pero no crea versiones. Cuando el resultado sea el esperado,
ejecuta el mismo comando sin esa opción.

Un caso que no requiere precondiciones se puede importar por sí solo:

```bash
uv run python -m test_service.import_corpus \
  --project-key KAN \
  --requested-by corpus-import \
  --file ../data/test_cases/GW-SMK-002.json
```

## Importar un directorio entero

`--directory` importa recursivamente todos los archivos `*.json` del
directorio indicado:

```bash
uv run python -m test_service.import_corpus \
  --project-key KAN \
  --requested-by corpus-import \
  --directory ../data \
  --dry-run
```

No se pueden combinar `--directory` y `--file`.

## Reglas y resultado

Los documentos deben cumplir el contrato
[`contracts/corpus/test-corpus-1.2.0.schema.json`](../../../../../contracts/corpus/test-corpus-1.2.0.schema.json).
Los documentos de tipo `precondition` se crean antes que los `test-case`, y
las referencias `preconditionReferences` declaran explícitamente la clave y versión de precondición
persistida, sin seleccionar implícitamente la versión más alta:

```json
"preconditionReferences": [
  {
    "preconditionKey": "LITELLM_PROXY_READY",
    "version": 1
  }
]
```

La operación es idempotente por clave lógica dentro del proyecto: si ya existe
una versión para una precondición o caso de prueba, se omite y se informa en
el resultado JSON. Un ejemplo de salida es:

```json
{
  "created_preconditions": 1,
  "created_test_cases": 1,
  "skipped_preconditions": 0,
  "skipped_test_cases": 0
}
```

El importador no ejecuta los casos. Para ejecutarlos después hay que crear la
composición y la ejecución mediante la API; las URLs como
`http://localhost:4000` se resuelven desde el entorno donde se ejecute el
runner.
