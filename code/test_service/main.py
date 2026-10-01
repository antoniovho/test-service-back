import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from test_service_server.apis.authoring_api import router as authoring_api_router
from test_service_server.apis.composition_api import router as composition_api_router
from test_service_server.apis.execution_api import router as execution_api_router
from test_service_server.apis.projects_api import router as projects_api_router
from test_service_server.apis.viewer_integration_api import router as viewer_integration_api_router

from test_service.bootstrap.container import get_injector
from test_service.domain.application.services.viewer_projection_service import (
    ViewerProjectionService,
)
from test_service.domain.ports.input.use_cases.execution.executions.process_next_execution_use_case import (  # noqa: E501
    ProcessNextExecutionUseCase,
)
from test_service.infrastructure.adapters.input.rest.authoring import (
    authoring_controller,  # noqa: F401
)
from test_service.infrastructure.adapters.input.rest.composition import (
    composition_controller,  # noqa: F401
)
from test_service.infrastructure.adapters.input.rest.exceptions.exception_handler import (
    register_exception_handlers,
)
from test_service.infrastructure.adapters.input.rest.execution import (
    execution_controller,  # noqa: F401
)

# Imported for its side effect: registers ProjectsController as BaseProjectsApi's subclass.
from test_service.infrastructure.adapters.input.rest.projects import (
    projects_controller,  # noqa: F401
)
from test_service.infrastructure.adapters.input.rest.security.identity_middleware import (
    IdentityMiddleware,
)
from test_service.infrastructure.adapters.input.rest.viewer import (
    viewer_integration_controller,  # noqa: F401
)
from test_service.infrastructure.adapters.output.commons.persistence.postgres.postgres_database_configuration import (  # noqa: E501
    PostgresDatabaseConfiguration,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Release database connections when the application stops."""
    projection_service = get_injector().inject(ViewerProjectionService)
    viewer_worker = asyncio.create_task(_process_viewer_operations(projection_service))
    execution_processor = get_injector().inject(ProcessNextExecutionUseCase)
    execution_task = asyncio.create_task(_process_executions(execution_processor))
    try:
        yield
    finally:
        viewer_worker.cancel()
        execution_task.cancel()
        with suppress(asyncio.CancelledError):
            await viewer_worker
        with suppress(asyncio.CancelledError):
            await execution_task
        database_configuration = get_injector().inject(PostgresDatabaseConfiguration)
        await database_configuration.dispose()


async def _process_viewer_operations(service: ViewerProjectionService) -> None:
    """Process persisted Viewer operations without retaining request state."""
    while True:
        operation = await service.process_next_operation()
        if operation is None:
            await asyncio.sleep(0.1)


async def _process_executions(processor: ProcessNextExecutionUseCase) -> None:
    """Claim and execute durable work without retaining HTTP request state."""
    while True:
        execution = await processor.execute(None)
        if execution is None:
            await asyncio.sleep(0.1)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Test Service",
        description="Backend implementation for the Test Service OpenAPI contract.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(IdentityMiddleware)
    register_exception_handlers(app)
    app.include_router(projects_api_router)
    app.include_router(authoring_api_router)
    app.include_router(composition_api_router)
    app.include_router(execution_api_router)
    app.include_router(viewer_integration_api_router)
    return app


app = create_app()
