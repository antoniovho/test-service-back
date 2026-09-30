# TEST SERVICE
# Prompt maestro de diseño e implementación

## 1. Rol y misión

Actúa como un equipo multidisciplinar de ingeniería de software formado por:

- Arquitecto de software.
- Analista de dominio.
- Especialista en diseño de APIs.
- Ingeniero backend.
- Especialista en persistencia.
- Ingeniero de automatización de pruebas.
- Especialista en integración con Jira/Xray.
- Especialista en seguridad y operación.

Tu misión es **diseñar, construir, probar y documentar desde cero Test Service**, un microservicio empresarial destinado a gestionar definiciones de pruebas de software, organizar su composición, ejecutar pruebas automatizadas y publicar sus representaciones en Jira/Xray.

Test Service es la **fuente de verdad de las definiciones, versiones, composiciones y ejecuciones**.

Jira/Xray es un sistema externo de consulta y visualización. Las modificaciones realizadas directamente en Jira/Xray nunca deben actualizar automáticamente los recursos canónicos de Test Service.

Esta especificación constituye la fuente de requisitos funcionales del producto.

Debes utilizar las tecnologías, herramientas, skills, plataformas y estándares autorizados en tu entorno corporativo.

Las decisiones sobre lenguaje, framework, base de datos, generación de código, gestión de secretos, infraestructura, mensajería, observabilidad y despliegue corresponden a tu arquitectura corporativa.

**No reduzcas el alcance funcional, no omitas reglas de negocio y no sustituyas requisitos por implementaciones provisionales.**

---

## 2. Entregables obligatorios

Construye y entrega:

1. Un contrato OpenAPI 3.x completo, creado desde cero.
2. Una implementación HTTP conforme al contrato.
3. Un modelo de dominio independiente de tecnologías.
4. Casos de uso que implementen todas las operaciones.
5. Un modelo lógico y físico de persistencia.
6. Migraciones o mecanismos equivalentes de evolución de datos.
7. Integración con la identidad y autorización corporativas.
8. Integración con el sistema corporativo de gestión de secretos.
9. Un subsistema extensible de ejecución de pruebas.
10. Un adaptador funcional de ejecución mediante Tavern.
11. Soporte inicial para pruebas HTTP y SSE.
12. Persistencia de ejecuciones, resultados y evidencias.
13. Integración con Jira para validar proyectos.
14. Integración con Jira/Xray para publicar entidades activas.
15. Detección de drift en los recursos publicados.
16. Registros consultables de sincronización y divergencias.
17. Pruebas automatizadas.
18. Observabilidad y configuración operativa.
19. Documentación de uso, operación y evolución del servicio.

El contrato OpenAPI es un entregable del desarrollo, no un archivo preexistente que deba reproducirse.

La implementación debe mantenerse compatible con dicho contrato mediante validaciones automatizadas.

---

## 3. Arquitectura lógica

Separa conceptualmente las siguientes responsabilidades:

### Interfaz de entrada

Recibe solicitudes, valida esquemas, identifica al solicitante, aplica controles de acceso y traduce las operaciones públicas a casos de uso.

### Aplicación

Orquesta los procesos de negocio, coordina transacciones, gestiona operaciones asíncronas y utiliza contratos de dominio e integración.

### Dominio

Contiene las entidades, objetos de valor, invariantes, ciclos de vida, reglas de composición y resultados canónicos.

No debe depender de HTTP, persistencia, Tavern, Jira, Xray ni de productos corporativos.

### Persistencia

Almacena entidades, relaciones, versiones, ejecuciones, resultados, evidencias, sincronizaciones y eventos de drift.

### Runner

Ejecuta pruebas automatizadas mediante motores intercambiables.

### Viewer

Transforma entidades canónicas en representaciones externas, las publica y detecta cambios realizados fuera de Test Service.

### Capacidades transversales

Autenticación, autorización, secretos, auditoría, observabilidad, configuración, resiliencia y gestión de errores.

Las dependencias entre estas responsabilidades deben ser explícitas y permitir pruebas aisladas.

No se impone una estructura concreta de paquetes ni una biblioteca de inyección de dependencias.

---

## 4. Alcance funcional

El microservicio se organiza en cinco áreas de negocio.

| Área | Responsabilidad |
|---|---|
| Projects | Gestión de proyectos vinculados obligatoriamente a Jira |
| Authoring | Preconditions, Test Cases y definiciones ejecutables |
| Composition | Test Sets y Test Plans |
| Execution | Environments, ejecuciones, resultados y evidencias |
| Viewer | Publicación en Xray, sincronizaciones y drift |

Todos los recursos deben poder trazarse hasta su propietario lógico y sus versiones, cuando corresponda.

---

# PARTE I. CONTRATO PÚBLICO

## 5. Diseño del contrato OpenAPI

Crea un contrato OpenAPI 3.x completo.

La API pública utilizará el prefijo:

`/v1`

Convenciones:

- JSON como formato principal.
- Propiedades en `camelCase`.
- UUID para identificadores técnicos de snapshots y operaciones.
- Fechas ISO 8601 con zona horaria explícita.
- Enumeraciones documentadas.
- Validaciones declarativas.
- Esquemas reutilizables.
- Respuestas de error homogéneas.
- Seguridad documentada.
- Identificadores de operación estables.

La versión del documento OpenAPI debe gestionarse como parte del ciclo de vida del nuevo producto.

No debe confundirse con `/v1`, que representa la versión de la interfaz HTTP, ni con `schemaVersion`, que representa la versión de las definiciones ejecutables.

## 6. Seguridad del contrato

La API requiere autenticación mediante identidad corporativa.

El contrato debe expresar un esquema de seguridad compatible con tokens Bearer cuando ese sea el mecanismo expuesto por la plataforma.

La validación de credenciales y la autorización deben implementarse conforme a los estándares corporativos.

La identidad del solicitante se obtiene del contexto autenticado.

Nunca se utiliza un identificador de usuario enviado en el cuerpo de una petición como prueba de identidad.

## 7. Paginación, filtrado y ordenación

Las operaciones de listado utilizarán:

```json
{
  "data": [],
  "pagination": {
    "offset": 0,
    "limit": 20,
    "total": 0
  }
}
```

Reglas:

- `offset` debe ser mayor o igual a cero.
- `limit` debe estar entre 1 y 100.
- `offset` predeterminado: 0.
- `limit` predeterminado: 20.
- `order`: `ASC` o `DESC`.
- Cada recurso define explícitamente sus campos de ordenación.
- La ordenación debe ser estable.
- Los filtros deben documentarse individualmente.
- `total` representa el total de registros que cumplen los filtros antes de aplicar paginación.

No deben exponerse campos internos de persistencia como parámetros públicos salvo que formen parte del modelo funcional.

## 8. Operaciones HTTP obligatorias

### 8.1. Projects

| Método | Ruta | Operación |
|---|---|---|
| GET | `/v1/projects` | Listar proyectos |
| POST | `/v1/projects` | Crear proyecto |
| GET | `/v1/projects/{projectKey}` | Obtener proyecto |
| DELETE | `/v1/projects/{projectKey}` | Eliminar lógicamente proyecto |

La creación debe devolver `201`.

La eliminación correcta debe devolver `204`.

### 8.2. Preconditions

Base:

`/v1/projects/{projectKey}/preconditions`

Operaciones:

- `GET /` — listar.
- `POST /` — crear.
- `GET /{preconditionId}` — obtener snapshot.
- `POST /{preconditionId}/versions` — crear versión.
- `POST /{preconditionId}/activations` — activar.
- `POST /{preconditionId}/deprecations` — deprecar.

Historial:

`GET /v1/projects/{projectKey}/precondition-keys/{preconditionKey}/versions`

### 8.3. Test Cases

Base:

`/v1/projects/{projectKey}/test-cases`

Operaciones:

- `GET /` — listar.
- `POST /` — crear.
- `GET /{testCaseId}` — obtener snapshot.
- `POST /{testCaseId}/versions` — crear versión.
- `POST /{testCaseId}/activations` — activar.
- `POST /{testCaseId}/deprecations` — deprecar.

Historial:

`GET /v1/projects/{projectKey}/test-case-keys/{testKey}/versions`

### 8.4. Test Sets

Base:

`/v1/projects/{projectKey}/test-sets`

Operaciones:

- `GET /` — listar.
- `POST /` — crear.
- `GET /{testSetId}` — obtener snapshot.
- `POST /{testSetId}/versions` — crear versión.
- `POST /{testSetId}/activations` — activar.
- `POST /{testSetId}/deprecations` — deprecar.

Historial:

`GET /v1/projects/{projectKey}/test-set-keys/{setKey}/versions`

### 8.5. Test Plans

Base:

`/v1/projects/{projectKey}/test-plans`

Operaciones:

- `GET /` — listar.
- `POST /` — crear.
- `GET /{testPlanId}` — obtener snapshot.
- `POST /{testPlanId}/versions` — crear versión.
- `POST /{testPlanId}/activations` — activar.
- `POST /{testPlanId}/deprecations` — deprecar.

Historial:

`GET /v1/projects/{projectKey}/test-plan-keys/{planKey}/versions`

### 8.6. Environments

| Método | Ruta | Operación |
|---|---|---|
| GET | `/v1/environments` | Listar |
| POST | `/v1/environments` | Crear |
| GET | `/v1/environments/{environmentId}` | Obtener |
| POST | `/v1/environments/{environmentId}/activations` | Activar |
| POST | `/v1/environments/{environmentId}/deactivations` | Desactivar |

### 8.7. Executions

Base:

`/v1/projects/{projectKey}/executions`

Operaciones:

- `GET /` — listar.
- `POST /` — solicitar ejecución.
- `GET /{executionId}` — consultar estado.
- `POST /{executionId}/cancellations` — solicitar cancelación.
- `GET /{executionId}/results` — listar resultados.
- `GET /{executionId}/results/{testResultId}` — obtener resultado.
- `GET /{executionId}/results/{testResultId}/actions` — listar resultados de acciones.
- `GET /{executionId}/results/{testResultId}/artifacts` — listar evidencias.

La solicitud de ejecución debe devolver `202 Accepted` e identificar la ejecución creada.

La cancelación es una solicitud asíncrona: devolver `202` cuando haya sido aceptada, sin afirmar que el runner ya se ha detenido.

### 8.8. Viewer

Publicación:

`POST /v1/projects/{projectKey}/viewer/publications`

Detección de drift:

`POST /v1/projects/{projectKey}/viewer/drift-checks`

Consulta por proyecto:

- `GET /v1/projects/{projectKey}/viewer/sync-records`
- `GET /v1/projects/{projectKey}/viewer/drift-events`

Consulta global:

- `GET /v1/viewer/sync-records`
- `GET /v1/viewer/drift-events`

Las solicitudes de publicación y comprobación de drift devuelven `202 Accepted`.

Deben proporcionar un identificador de operación y permitir consultar su evolución mediante los registros correspondientes.

No se añadirán endpoints públicos adicionales sin una necesidad funcional explícita y su correspondiente definición OpenAPI.

## 9. Errores HTTP

Utiliza Problem Details conforme a RFC 9457.

Ejemplo:

```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "The requested state transition is not allowed.",
  "instance": "/v1/projects/DEMO/test-cases"
}
```

Contempla:

| HTTP | Significado |
|---|---|
| 400 | Petición mal formada |
| 401 | Identidad no autenticada |
| 403 | Operación no autorizada |
| 404 | Recurso inexistente |
| 409 | Conflicto de negocio o estado |
| 422 | Datos válidos sintácticamente pero incompatibles con las reglas funcionales |
| 500 | Error interno |
| 503 | Dependencia externa necesaria no disponible |

Los errores deben proporcionar mensajes seguros, estables y comprensibles.

No deben contener credenciales, secretos, trazas internas ni respuestas crudas de proveedores externos.

---

# PARTE II. DOMINIO

## 10. Project

Un Project representa el ámbito propietario de los recursos de prueba.

Atributos lógicos:

| Campo | Tipo lógico | Regla |
|---|---|---|
| `key` | Texto | Único, estable, 2 a 20 caracteres |
| `name` | Texto | Obligatorio, no vacío |
| `status` | Enumeración | `ACTIVE`, `DELETED` |
| `createdAt` | Fecha/hora | Obligatorio |
| `createdBy` | Identidad | Obligatorio |
| `deletedAt` | Fecha/hora opcional | Solo tras eliminación |
| `deletedBy` | Identidad opcional | Solo tras eliminación |

### Validación obligatoria con Jira

La `projectKey` interna debe coincidir con la clave del proyecto en Jira.

Antes de crear un Project:

1. Validar los datos de entrada.
2. Verificar que la clave no existe en Test Service.
3. Consultar Jira mediante su API oficial.
4. Confirmar que existe un proyecto con esa misma clave.
5. Confirmar que la identidad técnica utilizada dispone de acceso de lectura.
6. Crear el Project únicamente cuando todas las comprobaciones hayan sido satisfactorias.

Reglas:

- Si Jira confirma inexistencia, rechazar la creación.
- Si Jira confirma acceso denegado, rechazar la creación.
- Si Jira no está disponible, no crear el Project.
- Si la validación no es concluyente, no crear el Project.
- No modificar Jira durante la validación.
- No crear registros internos parciales.
- No reutilizar una clave de proyecto eliminado.
- No eliminar el proyecto de Jira cuando se elimine lógicamente en Test Service.

La eliminación lógica es irreversible.

Los proyectos eliminados conservan sus datos históricos y permiten consultas autorizadas, pero no admiten nuevas definiciones, composiciones, ejecuciones ni publicaciones.

## 11. Modelo de versionado

Los siguientes recursos son versionados:

- Precondition.
- Test Case.
- Test Set.
- Test Plan.

Cada snapshot contiene:

- UUID propio.
- Proyecto propietario.
- Clave funcional.
- Número de versión positivo.
- Estado.
- Creador.
- Fecha de creación.
- Contenido específico.

### Ciclo de vida

`DRAFT -> ACTIVE -> DEPRECATED`

Reglas:

- Los snapshots son inmutables respecto a su contenido funcional.
- Crear una nueva versión genera un nuevo UUID.
- El número de versión aumenta de forma monotónica.
- La unicidad es `(projectKey, businessKey, version)`.
- Una versión `DEPRECATED` no puede reactivarse.
- Las transiciones de estado deben ser atómicas.
- La asignación de versiones debe ser segura ante concurrencia.

### Restricción de referencias

Al crear una nueva composición, solo pueden referenciarse versiones `ACTIVE`.

Esto incluye:

- Preconditions de un Test Case.
- Test Cases de un Test Set.
- Test Sets de un Test Plan.
- Test Cases directos de un Test Plan.

Las referencias deben apuntar a UUID concretos.

No deben resolverse dinámicamente a la última versión disponible.

### Conservación histórica

Si una versión referenciada pasa posteriormente a `DEPRECATED`, las composiciones existentes conservan su referencia.

No deben modificarse retrospectivamente sus snapshots.

Sin embargo, **al iniciar una nueva ejecución se comprueba nuevamente que todos los recursos requeridos están `ACTIVE`**.

Las ejecuciones ya iniciadas conservan sus snapshots y pueden finalizar aunque cambie posteriormente el estado de una versión.

## 12. Definition y acciones

Una Definition representa una secuencia declarativa de operaciones automatizables.

Estructura lógica:

```json
{
  "schemaVersion": "1.0",
  "variables": {
    "baseUrl": "https://service.example.test"
  },
  "actions": [
    {
      "id": "request-1",
      "type": "HTTP_REQUEST",
      "config": {},
      "source": null
    }
  ]
}
```

Reglas:

- `schemaVersion` es obligatorio.
- La versión inicial admitida es `"1.0"`.
- `variables` es un mapa de nombres a valores declarativos.
- `actions` es una secuencia ordenada y no vacía.
- Cada acción tiene identificador único dentro de la definición.
- Cada acción declara un tipo registrado.
- La configuración se valida según el tipo.
- No se permite ejecutar código arbitrario recibido desde la API.

El registro de acciones debe ser extensible y versionable.

Las definiciones deben validarse antes de activarse y antes de programarse para ejecución.

## 13. Precondition

Una Precondition representa una condición previa reutilizable.

Contiene:

- Identidad y versión.
- Nombre.
- Descripción.
- Definition.
- Metadatos.
- Estado y auditoría.

Las Preconditions se ejecutan antes de las acciones principales de los Test Cases que las referencian.

Si una Precondition falla, las acciones principales dependientes no se ejecutan.

## 14. Test Case

Un Test Case representa una prueba automatizada.

Contiene:

- Identidad y versión.
- Nombre.
- Resumen.
- Objetivo.
- Tipo.
- Nivel.
- Prioridad.
- Definition.
- Timeout positivo.
- Metadatos.
- Referencias ordenadas a Preconditions.

### Alcance inicial

Solo se admite:

`AUTOMATED`

No se implementarán Test Cases manuales ni flujos de ejecución manual.

El contrato OpenAPI no debe aceptar `MANUAL` como valor válido en esta entrega.

Las Preconditions referenciadas deben:

- Existir.
- Pertenecer al mismo proyecto.
- Estar `ACTIVE` al crear la versión del Test Case.
- No repetirse dentro de la misma relación.

## 15. Test Set

Un Test Set agrupa versiones concretas de Test Cases.

Contiene:

- Identidad y versión.
- Clave funcional.
- Nombre.
- Descripción.
- Lista ordenada de UUID de Test Cases.
- Estado y auditoría.

Reglas:

- La lista no puede estar vacía.
- No admite referencias duplicadas.
- Todos los Test Cases deben pertenecer al mismo proyecto.
- Todos deben estar `ACTIVE` al crear la versión.
- Debe conservarse el orden.

## 16. Test Plan

Un Test Plan define una composición ejecutable.

Contiene:

- Identidad y versión.
- Clave funcional.
- Nombre.
- Descripción.
- Test Sets incluidos.
- Test Cases directos.
- Exclusiones.
- Timeout.
- Modo de ejecución.
- Paralelismo máximo.
- Estado y auditoría.

Modos:

- `SEQUENTIAL`
- `PARALLEL`

Reglas:

- En modo paralelo, `maxParallelism >= 1`.
- En modo secuencial, `maxParallelism` debe ser nulo.
- No se permiten duplicados dentro de cada colección de referencias.
- No se puede excluir un Test Case incluido directamente.
- Todas las referencias deben existir y pertenecer al proyecto.
- Todas deben estar `ACTIVE` al crear la versión.

### Expansión del plan

La expansión debe ser determinista.

Procedimiento:

1. Resolver los Test Sets referenciados.
2. Obtener sus Test Cases en el orden definido.
3. Incorporar los Test Cases directos.
4. Eliminar duplicados preservando la primera aparición.
5. Aplicar exclusiones.
6. Validar que queda al menos un Test Case ejecutable.
7. Construir la lista efectiva de ejecución.

El resultado debe conservar referencias a versiones concretas.

## 17. Environment

Un Environment es un contexto global reutilizable para ejecutar pruebas.

Contiene:

- UUID.
- Clave funcional única.
- Nombre.
- Descripción.
- Configuración.
- Estado.
- Auditoría.

Estados:

- `ACTIVE`
- `INACTIVE`
- `DEPRECATED`

Reglas:

- Solo un Environment `ACTIVE` puede utilizarse para nuevas ejecuciones.
- Un Environment `DEPRECATED` no puede reactivarse.
- La configuración puede contener valores ordinarios y referencias a secretos.
- No se almacenan valores secretos resueltos como configuración ordinaria.

### Configuración lógica

Cada entrada de configuración debe distinguir entre:

- Valor ordinario.
- Referencia a secreto.

Una referencia a secreto debe ser opaca para el consumidor público.

La infraestructura corporativa determina cómo se representa y resuelve físicamente.

---

# PARTE III. PERSISTENCIA

## 18. Modelo lógico obligatorio

Implementa las siguientes estructuras persistentes o sus equivalentes tecnológicos.

| Entidad lógica | Identificación y contenido | Restricciones principales |
|---|---|---|
| `PROJECT` | Clave, nombre, estado, auditoría | Clave única e irreversible |
| `PRECONDITION_VERSION` | UUID, proyecto, clave, versión, Definition, estado | Unicidad proyecto-clave-versión |
| `TEST_CASE_VERSION` | UUID, proyecto, clave, versión, Definition, atributos, estado | Unicidad proyecto-clave-versión |
| `TEST_CASE_PRECONDITION` | Test Case, Precondition, posición | Referencias únicas y ordenadas |
| `TEST_SET_VERSION` | UUID, proyecto, clave, versión, atributos, estado | Unicidad proyecto-clave-versión |
| `TEST_SET_ITEM` | Test Set, Test Case, posición | Sin duplicados |
| `TEST_PLAN_VERSION` | UUID, proyecto, clave, versión, estrategia, estado | Unicidad proyecto-clave-versión |
| `TEST_PLAN_TEST_SET` | Test Plan, Test Set, posición | Referencia versionada |
| `TEST_PLAN_TEST_CASE` | Test Plan, Test Case, posición | Referencia versionada |
| `TEST_PLAN_EXCLUSION` | Test Plan, Test Case excluido | Sin duplicados |
| `ENVIRONMENT` | UUID, clave, configuración, estado | Clave única |
| `EXECUTION` | UUID, proyecto, plan, entorno, estado, tiempos, runner | Referencias y lifecycle |
| `TEST_RESULT` | UUID, ejecución, Test Case, estado, tiempos | Pertenencia a ejecución |
| `ACTION_RESULT` | UUID, Test Result, acción, estado, duración | Correlación y orden |
| `TEST_RESULT_ARTIFACT` | UUID, resultado, tipo, ubicación, metadatos | Integridad y acceso |
| `VIEWER_SYNC_RECORD` | UUID, proyecto, entidad, versión, viewer, estado, huella | Trazabilidad de publicación |
| `DRIFT_EVENT` | UUID, registro de sincronización, diferencias, estado | Detección y auditoría |

### Requisitos de integridad

Define explícitamente:

- Claves primarias.
- Claves funcionales.
- Claves compuestas.
- Restricciones de unicidad.
- Relaciones y cardinalidades.
- Integridad referencial.
- Orden de relaciones.
- Índices para filtros y consultas.
- Restricciones de estado.
- Campos de auditoría.
- Reglas de eliminación.
- Requisitos de consistencia.

Las entidades históricas deben conservarse.

No deben eliminarse físicamente snapshots que participen en composiciones, ejecuciones o registros de sincronización.

La creación de un agregado y sus relaciones debe ser atómica.

La tecnología de almacenamiento y la materialización física de estas estructuras quedan a cargo de la arquitectura corporativa.

## 19. Auditoría

Los registros de auditoría deben conservar como mínimo:

- Identidad del actor.
- Operación.
- Recurso afectado.
- Identificador del recurso.
- Fecha y hora.
- Identificador de correlación.
- Resultado de la operación.

La auditoría no debe contener secretos ni datos sensibles innecesarios.

---

# PARTE IV. EJECUCIÓN AUTOMATIZADA

## 20. Arquitectura de runners

Test Service debe disponer de un subsistema extensible de ejecución.

Tavern es el primer runner obligatorio.

La incorporación de motores adicionales no debe modificar:

- Los modelos de dominio.
- Los casos de uso de ejecución.
- El contrato OpenAPI.
- El modelo canónico de resultados.
- Las reglas de versionado.
- La persistencia funcional de ejecuciones.

### Contrato lógico del runner

Cada runner debe proporcionar capacidades equivalentes a:

1. Identificación y versión.
2. Declaración de capacidades.
3. Validación de compatibilidad.
4. Preparación del trabajo.
5. Ejecución.
6. Comunicación de progreso.
7. Producción de resultados.
8. Producción de evidencias.
9. Cancelación.
10. Liberación de recursos.

La selección debe realizarse según las capacidades requeridas por las acciones de la Definition.

Si no existe un runner compatible, la solicitud debe rechazarse con un error funcional.

No debe seleccionarse silenciosamente un runner que ignore acciones.

## 21. Tavern: alcance inicial

El adaptador Tavern debe ejecutar pruebas de API HTTP y flujos SSE.

### 21.1. Acciones HTTP

El catálogo inicial debe permitir:

- Métodos HTTP habituales.
- URL y parámetros de consulta.
- Cabeceras.
- Cuerpos de petición.
- Autenticación.
- Timeouts.
- Validación del código HTTP.
- Validación de cabeceras.
- Validación de cuerpo JSON o texto.
- Extracción de valores.
- Reutilización de variables.
- Aserciones sobre respuestas.

### 21.2. Acciones SSE

El catálogo inicial debe permitir:

- Abrir una conexión SSE.
- Configurar cabeceras y autenticación.
- Establecer timeout de conexión.
- Establecer timeout de recepción.
- Recibir eventos de manera incremental.
- Filtrar por tipo de evento.
- Validar contenido de eventos.
- Validar secuencias de eventos.
- Extraer valores de eventos.
- Establecer condiciones de finalización.
- Limitar el número de eventos recibidos.
- Cerrar la conexión correctamente.

### 21.3. Semántica SSE

Las acciones SSE deben contemplar:

- Campos `event`, `data`, `id` y `retry` cuando estén presentes.
- Eventos sin nombre explícito.
- Comentarios y líneas de control.
- Eventos multilínea.
- Finalización normal.
- Desconexión inesperada.
- Timeouts.
- Flujos que no terminan espontáneamente.
- Límites de duración y volumen.
- Cancelación.

La validación debe distinguir entre:

- Evento esperado recibido.
- Evento inesperado.
- Secuencia incorrecta.
- Timeout sin cumplir la condición.
- Error de transporte.
- Cancelación.

Los resultados SSE deben integrarse en el modelo canónico de ActionResult.

### 21.4. Compatibilidad real con Tavern

No presupongas que Tavern proporciona de forma nativa todas las capacidades SSE requeridas.

Implementa las capacidades HTTP mediante sus mecanismos compatibles.

Cuando SSE u otra acción requiera extensiones, utiliza un mecanismo controlado integrado en el adaptador del runner.

Las extensiones deben ser verificables, seguras y compatibles con el modelo de resultados.

No debe afirmarse compatibilidad con una acción sin disponer de pruebas automatizadas que la demuestren.

## 22. Compilador de Definition

Implementa un compilador determinista entre las definiciones canónicas y el formato ejecutable del runner seleccionado.

El compilador debe:

1. Validar `schemaVersion`.
2. Validar los tipos de acción.
3. Validar configuraciones.
4. Resolver referencias a Preconditions.
5. Preservar el orden.
6. Preservar identificadores.
7. Validar variables.
8. Preparar referencias a secretos.
9. Construir la representación ejecutable.
10. Generar información de correlación entre acciones y resultados.

La misma entrada y configuración deben producir una representación funcionalmente equivalente.

El compilador debe rechazar definiciones incompatibles antes de programar el trabajo.

No debe omitir acciones desconocidas.

## 23. Variables y secretos durante la ejecución

Distingue:

- Variables declaradas en Definition.
- Configuración ordinaria de Environment.
- Variables extraídas durante la ejecución.
- Referencias a secretos.

Las variables declaradas en Definition tienen prioridad sobre valores ordinarios homónimos del Environment.

Las variables extraídas durante la ejecución se incorporan al contexto de la ejecución y pueden utilizarse en acciones posteriores.

Una extracción no puede sobrescribir silenciosamente una variable reservada ni una referencia a secreto.

Los secretos se resuelven únicamente en el contexto autorizado de ejecución.

No deben persistirse en:

- Archivos de pruebas compiladas.
- Logs.
- Resultados.
- Evidencias.
- Trazas.
- Mensajes de error.
- Respuestas públicas.

## 24. Preconditions en ejecución

Antes de las acciones principales:

1. Resolver las Preconditions referenciadas.
2. Validar sus versiones.
3. Ejecutarlas en orden.
4. Registrar su resultado.
5. Detener las acciones dependientes cuando una Precondition falle.

Una Precondition fallida produce un Test Case `BLOCKED`.

Debe conservarse la evidencia segura de la causa del bloqueo.

## 25. Creación de Execution

Al solicitar una ejecución:

1. Autenticar y autorizar al solicitante.
2. Validar que el Project está `ACTIVE`.
3. Validar que el Test Plan está `ACTIVE`.
4. Resolver Test Sets y Test Cases.
5. Validar que todos los recursos requeridos están `ACTIVE`.
6. Validar que el Environment está `ACTIVE`.
7. Expandir el Test Plan.
8. Comprobar compatibilidad con un runner.
9. Construir una representación inmutable del trabajo.
10. Persistir la Execution.
11. Programar su ejecución.
12. Devolver `202 Accepted`.

La programación debe tolerar fallos transitorios sin crear ejecuciones duplicadas.

## 26. Modelo de Execution

Una Execution contiene:

- UUID.
- Proyecto.
- Test Plan snapshot.
- Environment.
- Identidad del solicitante.
- Trigger.
- Runner seleccionado.
- Versión del runner.
- Estado.
- Fecha de creación.
- Inicio.
- Finalización.
- Duración.
- Resumen de resultados.

Triggers:

- `MANUAL`
- `API`
- `CI`
- `SCHEDULE`

Estados:

- `CREATED`
- `RUNNING`
- `PASSED`
- `FAILED`
- `PARTIALLY_FAILED`
- `ERROR`
- `CANCELLED`

Transiciones:

- `CREATED -> RUNNING`
- `RUNNING -> PASSED`
- `RUNNING -> FAILED`
- `RUNNING -> PARTIALLY_FAILED`
- `RUNNING -> ERROR`
- `CREATED -> CANCELLED`
- `RUNNING -> CANCELLED`

Los estados terminales no permiten nuevas transiciones.

## 27. Resultados

### TestResult

Cada TestResult representa la ejecución de un Test Case concreto.

Estados:

- `PASSED`
- `FAILED`
- `ERROR`
- `BLOCKED`
- `SKIPPED`

Debe registrar:

- Test Case snapshot.
- Inicio.
- Finalización.
- Duración.
- Estado.
- Error seguro.
- Resultados de acciones.

### ActionResult

Cada ActionResult debe registrar:

- Identificador de acción.
- Posición.
- Estado.
- Inicio.
- Finalización.
- Duración.
- Resultado normalizado.
- Error seguro.
- Referencias a evidencias.

### Artefactos

Tipos:

- `REQUEST`
- `RESPONSE`
- `SSE_TRACE`
- `LOG`
- `OTHER`

El almacenamiento puede utilizar capacidades corporativas de persistencia u objetos.

Debe garantizarse:

- Integridad.
- Acceso autorizado.
- Asociación con ejecución y resultado.
- Redacción de datos sensibles.
- Conservación según políticas corporativas.

## 28. Comunicación interna con runners

Define un protocolo interno autenticado para comunicar:

- Inicio de ejecución.
- Inicio de Test Case.
- Resultado de Precondition.
- Inicio y resultado de acción.
- Evidencias.
- Finalización de Test Case.
- Finalización de Execution.
- Errores.
- Confirmación de cancelación.

Cada evento debe incluir:

- `executionId`.
- `eventId` único.
- Tipo de evento.
- Identificador del runner.
- Marca temporal.
- Identificadores de Test Case y acción cuando corresponda.
- Estado.
- Datos seguros del resultado.

El procesamiento debe ser idempotente.

Los eventos duplicados no pueden duplicar resultados.

Los eventos tardíos no pueden modificar una Execution terminal.

La tecnología del canal interno se decide conforme a la infraestructura corporativa.

## 29. Cancelación

La cancelación es una operación idempotente.

Debe:

1. Validar la existencia de la Execution.
2. Verificar su estado.
3. Registrar la solicitud.
4. Propagarla al runner.
5. Interrumpir el trabajo pendiente.
6. Conservar resultados ya producidos.
7. Confirmar el estado terminal cuando la cancelación sea efectiva.

Una ejecución terminal no debe reiniciarse ni cambiar de resultado.

---

# PARTE V. VIEWER JIRA/XRAY

## 30. Principio de integración

Test Service mantiene el estado canónico.

Jira/Xray almacena representaciones externas para consulta y visualización.

La integración es saliente.

Las modificaciones externas pueden detectarse y auditarse, pero nunca aplicarse automáticamente al dominio.

## 31. Recursos publicables

Publica los snapshots `ACTIVE` de:

- Preconditions.
- Test Cases.
- Test Sets.
- Test Plans.

El adaptador debe mapear los atributos y relaciones gestionados por Test Service a los modelos compatibles con Jira/Xray.

Debe utilizar APIs oficiales y mecanismos de autenticación autorizados.

No debe suponer que un payload canónico interno puede enviarse directamente a cualquier endpoint remoto.

## 32. Publicación

La publicación de un proyecto debe:

1. Validar el Project.
2. Seleccionar las entidades activas.
3. Resolver dependencias.
4. Ordenar la publicación.
5. Mapear cada entidad.
6. Crear o actualizar el recurso externo.
7. Conservar los identificadores remotos.
8. Registrar el resultado.
9. Continuar con entidades independientes cuando otras fallen.
10. Reintentar exclusivamente las operaciones pendientes o fallidas.

El orden debe permitir crear primero los recursos necesarios para establecer relaciones posteriores.

Las operaciones deben ser idempotentes.

No deben producir duplicados externos cuando se repita una solicitud.

## 33. Publicaciones parciales

Una publicación puede finalizar con:

- Todas las entidades sincronizadas.
- Algunas entidades sincronizadas y otras fallidas.
- Todas las entidades fallidas.

Los éxitos deben conservarse.

No se ejecutará una reversión global de publicaciones correctas.

Los reintentos deben actuar exclusivamente sobre entidades fallidas o pendientes.

Una entidad dependiente no debe publicarse como completa si sus dependencias necesarias no están disponibles.

Debe distinguirse entre:

- Error propio de la entidad.
- Bloqueo por dependencia fallida.
- Error transitorio del proveedor.
- Error permanente de validación.

Las operaciones repetidas deben reutilizar la correspondencia de identificadores internos y externos.

## 34. ViewerSyncRecord

Cada intento relevante de publicación debe quedar registrado.

Atributos lógicos:

- UUID.
- Identificador de operación.
- Proyecto.
- Tipo de entidad.
- Clave funcional.
- UUID de versión.
- Viewer.
- Identificador externo.
- Clave externa.
- Estado.
- Inicio.
- Finalización.
- Error seguro.
- Huella o snapshot normalizado de los atributos publicados correctamente.

Estados:

- `PENDING`
- `SYNCED`
- `ERROR`
- `DRIFT_DETECTED`

El sistema debe poder distinguir el historial de intentos del último estado publicado correctamente.

## 35. Detección de drift

El drift se calcula **contra la última proyección publicada correctamente**.

No debe calcularse contra la versión canónica más reciente si esta todavía no ha sido publicada.

### Algoritmo funcional

1. Obtener el último ViewerSyncRecord satisfactorio de la entidad.
2. Recuperar la representación o huella del contenido publicado.
3. Consultar el recurso remoto.
4. Normalizar sus atributos y relaciones.
5. Comparar únicamente los campos gestionados por Test Service.
6. Detectar diferencias.
7. Registrar los eventos correspondientes.
8. Evitar duplicados de una divergencia persistente.

### Tipos de drift

- `MODIFIED`: cambió un atributo o relación gestionada.
- `DELETED`: el recurso externo fue eliminado.
- `MISSING`: el recurso esperado no puede localizarse.

Un fallo de autenticación, timeout o indisponibilidad de Jira/Xray no debe clasificarse automáticamente como eliminación.

Debe registrarse como error de comprobación.

### Campos comparados

La comparación debe incluir, cuando sean representables en Xray:

- Nombre.
- Descripción.
- Contenido funcional publicado.
- Metadatos gestionados.
- Relaciones entre Preconditions, Test Cases, Test Sets y Test Plans.
- Identificadores y correspondencias de recursos.

No deben compararse campos administrados exclusivamente por Jira/Xray.

La normalización debe evitar falsos positivos derivados de diferencias irrelevantes de formato.

## 36. DriftEvent

Cada divergencia debe conservar:

- UUID.
- Proyecto.
- Viewer.
- Entidad afectada.
- Versión publicada.
- Registro de sincronización de referencia.
- Tipo de divergencia.
- Atributos afectados.
- Valor esperado seguro.
- Valor observado seguro.
- Fecha de detección.
- Estado de notificación.

Estados de notificación:

- `PENDING`
- `SENT`
- `ERROR`

Los detalles deben excluir secretos y datos sensibles.

La detección repetida de una divergencia no modificada no debe crear eventos duplicados indefinidamente.

Cuando la divergencia desaparezca y reaparezca, debe poder registrarse como una nueva ocurrencia.

## 37. Consultas de Viewer

Permite consultar:

- Registros globales de sincronización.
- Registros por proyecto.
- Eventos globales de drift.
- Eventos por proyecto.

Admite paginación, ordenación y filtros relevantes.

Las consultas no deben contactar obligatoriamente con Jira/Xray: deben poder responderse a partir de los registros persistidos.

---

# PARTE VI. SEGURIDAD Y OPERACIÓN

## 38. Autorización

Implementa permisos lógicos para:

- Lectura de proyectos.
- Administración de proyectos.
- Gestión de Preconditions.
- Gestión de Test Cases.
- Gestión de composiciones.
- Administración de Environments.
- Solicitud y cancelación de ejecuciones.
- Consulta de resultados.
- Publicación Viewer.
- Comprobación de drift.
- Consulta de registros.

Los permisos sobre recursos de proyecto deben respetar su ámbito.

Los Environments y listados globales requieren autorización específica.

La asignación concreta de permisos a identidades o roles corporativos corresponde a la plataforma de seguridad.

## 39. Gestión de secretos

Los secretos deben almacenarse y resolverse mediante los mecanismos corporativos autorizados.

El dominio almacena referencias, no valores sensibles.

Debe evitarse su exposición en:

- APIs.
- Logs.
- Mensajes.
- Artefactos.
- Trazas.
- Configuración persistente ordinaria.
- Errores.

La resolución debe realizarse en el contexto autorizado y durante el periodo mínimo necesario.

## 40. Concurrencia y consistencia

Garantiza:

- Unicidad de claves.
- Incremento atómico de versiones.
- Integridad de relaciones.
- Transiciones de estado válidas.
- Idempotencia de operaciones externas.
- Procesamiento idempotente de eventos.
- Consistencia de resultados.
- Recuperación de trabajos interrumpidos.
- Ausencia de duplicados en publicaciones.

Las llamadas externas no deben mantener abiertas transacciones de persistencia prolongadas.

## 41. Resiliencia

Implementa:

- Timeouts configurables.
- Reintentos acotados.
- Distinción entre errores transitorios y permanentes.
- Protección frente a saturación.
- Control de concurrencia.
- Recuperación de operaciones pendientes.
- Correlación entre solicitudes y trabajos.
- Registro de fallos seguros.

Los reintentos no deben duplicar efectos funcionales.

## 42. Observabilidad

Proporciona:

- Logs estructurados.
- Métricas.
- Trazas.
- Identificadores de correlación.
- Estado de integraciones.
- Estado de runners.
- Métricas de ejecución.
- Métricas de publicación.
- Métricas de drift.

No incluyas secretos ni datos sensibles en la telemetría.

Los objetivos cuantitativos de rendimiento, disponibilidad, capacidad y retención se parametrizarán conforme a las políticas corporativas.

---

# PARTE VII. PRUEBAS Y ACEPTACIÓN

## 43. Estrategia de pruebas

Implementa pruebas automatizadas para:

### Contrato

- Validación del OpenAPI.
- Compatibilidad entre contrato e implementación.
- Esquemas de petición y respuesta.
- Errores Problem Details.
- Paginación.
- Seguridad.

### Dominio

- Unicidad de claves.
- Creación de versiones.
- Inmutabilidad.
- Transiciones de estado.
- Referencias `ACTIVE`.
- Conservación histórica.
- Expansión de Test Plans.

### Projects y Jira

- Proyecto existente en Jira.
- Proyecto inexistente.
- Acceso denegado.
- Jira no disponible.
- Validación no concluyente.
- Eliminación lógica.
- Rechazo de operaciones sobre proyectos eliminados.

### Runner

- Compilación correcta.
- Acción desconocida.
- Configuración inválida.
- Runner incompatible.
- Preconditions.
- Variables.
- Secretos.
- HTTP.
- Aserciones.
- Extracción de variables.
- SSE.
- Timeouts.
- Ejecución secuencial.
- Ejecución paralela.
- Cancelación.
- Eventos duplicados.
- Resultados tardíos.
- Recuperación tras fallo.

### Viewer

- Publicación correcta.
- Publicación idempotente.
- Publicación parcial.
- Reintento de entidades fallidas.
- Dependencia no disponible.
- Correspondencia de identificadores.
- Drift por modificación.
- Drift por eliminación.
- Recurso remoto no localizable.
- Fallo de comunicación.
- Ausencia de falsos positivos.
- No modificación del dominio.
- Consulta de registros.

## 44. Criterios de aceptación funcional

La implementación debe demostrar que:

1. Un Project solo se crea si existe una clave idéntica y accesible en Jira.
2. Un proyecto eliminado conserva su historial y rechaza nuevas operaciones de escritura.
3. Los snapshots versionados no pueden modificarse.
4. No pueden crearse nuevas referencias a versiones no activas.
5. Las referencias históricas se conservan.
6. No pueden iniciarse ejecuciones con recursos requeridos no activos.
7. Solo se admiten Test Cases automatizados.
8. Tavern ejecuta pruebas HTTP compatibles.
9. El adaptador Tavern soporta validación de SSE.
10. Las acciones producen resultados correlacionados.
11. Las Preconditions bloquean correctamente las acciones dependientes.
12. Los secretos no se filtran.
13. Los resultados se conservan después de una cancelación.
14. Puede incorporarse un segundo runner sin modificar el contrato público.
15. Jira/Xray refleja los recursos publicados correctamente.
16. Los fallos parciales no revierten publicaciones exitosas.
17. Los reintentos no duplican recursos externos.
18. El drift se compara con la última publicación exitosa.
19. Los cambios externos no modifican el dominio.
20. Los registros de sincronización y drift pueden consultarse de forma paginada.
21. El contrato OpenAPI coincide con la implementación.
22. Las pruebas automatizadas verifican todos los comportamientos anteriores.

---

# PARTE VIII. PLAN DE IMPLEMENTACIÓN

## 45. Fases

### Fase 1. Fundamentos y contrato

- Diseño del OpenAPI.
- Arquitectura lógica.
- Seguridad.
- Errores.
- Modelo de dominio.
- Persistencia inicial.

### Fase 2. Projects y Authoring

- Validación Jira.
- Projects.
- Definitions.
- Preconditions.
- Test Cases.
- Versionado.
- Activación y deprecación.

### Fase 3. Composition

- Test Sets.
- Test Plans.
- Relaciones.
- Expansión determinista.
- Integridad de referencias.

### Fase 4. Execution

- Environments.
- Referencias a secretos.
- Modelo de Execution.
- Contrato extensible de runners.
- Adaptador Tavern.
- Acciones HTTP.
- Acciones SSE.
- Resultados.
- Evidencias.
- Cancelación.

### Fase 5. Viewer

- Integración Xray.
- Mapeo de entidades.
- Publicación.
- Manejo de errores parciales.
- Registros de sincronización.
- Detección de drift.
- Consultas de auditoría.

### Fase 6. Endurecimiento

- Resiliencia.
- Concurrencia.
- Observabilidad.
- Seguridad integral.
- Pruebas de contrato.
- Pruebas de extremo a extremo.
- Documentación operativa.

Cada fase debe finalizar con entregables funcionales, pruebas y criterios de aceptación verificables.

## 46. Instrucciones finales de ejecución

Construye Test Service como un producto nuevo y completo.

Comienza diseñando el modelo de dominio y el contrato OpenAPI.

A continuación implementa los casos de uso, la persistencia, los adaptadores y las integraciones.

Mantén correspondencia verificable entre:

- Requisitos funcionales.
- Modelos de dominio.
- Operaciones HTTP.
- Entidades persistentes.
- Casos de uso.
- Pruebas automatizadas.

No introduzcas dependencias tecnológicas en el dominio.

No sustituyas la implementación real de Tavern, Jira o Xray por simulaciones en los entornos de ejecución productivos.

Utiliza dobles de prueba únicamente para pruebas automatizadas y entornos de desarrollo controlados.

Aplica las políticas corporativas de infraestructura, identidad, seguridad, persistencia, operación y despliegue.

**El resultado debe ser un microservicio funcional, verificable, extensible y preparado para operar conforme a los estándares de la empresa.**
