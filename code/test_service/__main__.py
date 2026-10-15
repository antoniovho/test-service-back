"""Local command-line entry point for the Test Service."""

import uvicorn


def main() -> None:
    """Run the ASGI application with Uvicorn's local-development defaults."""
    uvicorn.run(
        "test_service.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
