from fastapi import FastAPI
from test_service_server.apis.projects_api import router as projects_api_router

# Imported for its side effect: registers ProjectsController as BaseProjectsApi's subclass.
from test_service.adapters.input.rest.controllers.projects import projects_controller  # noqa: F401
from test_service.adapters.input.rest.error_mapping import register_exception_handlers
from test_service.adapters.input.rest.security.identity_middleware import IdentityMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title="Test Service",
        description="Backend implementation for the Test Service OpenAPI contract.",
        version="0.1.0",
    )
    app.add_middleware(IdentityMiddleware)
    register_exception_handlers(app)
    app.include_router(projects_api_router)
    return app


app = create_app()
