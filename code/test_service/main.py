from fastapi import FastAPI


def create_app() -> FastAPI:
    return FastAPI(
        title="Test Service",
        description="Backend implementation for the Test Service OpenAPI contract.",
        version="0.1.0",
    )


app = create_app()
