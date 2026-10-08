import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI

from test_service import main
from test_service.main import create_app


class TestCreateApp:
    def test_when_application_is_created_expect_contract_metadata(self) -> None:
        application = create_app()

        assert application.title == "Test Service"
        assert application.version == "0.1.0"

    async def test_when_lifespan_ends_expect_workers_cancelled_and_database_disposed(
        self, monkeypatch
    ) -> None:
        projection_service = object()
        execution_processor = object()
        database_configuration = MagicMock()
        database_configuration.dispose = AsyncMock()

        class _Injector:
            def inject(self, dependency):
                return {
                    main.ViewerProjectionService: projection_service,
                    main.ProcessNextExecutionUseCase: execution_processor,
                    main.PostgresDatabaseConfiguration: database_configuration,
                }[dependency]

        async def wait_for_cancellation(_):
            await asyncio.Future()

        monkeypatch.setattr(main, "get_injector", _Injector)
        monkeypatch.setattr(main, "_process_viewer_operations", wait_for_cancellation)
        monkeypatch.setattr(main, "_process_executions", wait_for_cancellation)

        async with main.lifespan(FastAPI()):
            pass

        database_configuration.dispose.assert_awaited_once()

    @pytest.mark.parametrize(
        ("worker", "service_method"),
        [
            (main._process_viewer_operations, "process_next_operation"),
            (main._process_executions, "execute"),
        ],
        ids=["viewer", "execution"],
    )
    async def test_when_worker_has_no_work_expect_idle_sleep(
        self, monkeypatch, worker, service_method
    ) -> None:
        service = MagicMock()
        setattr(service, service_method, AsyncMock(return_value=None))

        async def cancel_sleep(_):
            raise asyncio.CancelledError()

        monkeypatch.setattr(main.asyncio, "sleep", cancel_sleep)

        with pytest.raises(asyncio.CancelledError):
            await worker(service)

        getattr(service, service_method).assert_awaited_once()
