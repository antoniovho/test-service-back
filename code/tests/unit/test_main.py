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


class TestWorkerSupervision:
    @pytest.fixture
    def sleeps(self, monkeypatch) -> list[float]:
        delays: list[float] = []

        async def record_sleep(delay):
            delays.append(delay)

        monkeypatch.setattr(main.asyncio, "sleep", record_sleep)
        return delays

    @pytest.mark.parametrize(
        ("worker", "service_method"),
        [
            (main._process_viewer_operations, "process_next_operation"),
            (main._process_executions, "execute"),
        ],
        ids=["viewer", "execution"],
    )
    async def test_when_worker_step_fails_once_expect_error_logged_and_processing_resumed(
        self, sleeps, caplog, worker, service_method
    ) -> None:
        service = MagicMock()
        method = AsyncMock(side_effect=[RuntimeError("database down"), asyncio.CancelledError()])
        setattr(service, service_method, method)

        with pytest.raises(asyncio.CancelledError):
            await worker(service)

        assert method.await_count == 2
        assert sleeps == [1.0]
        assert "failed 1 consecutive time(s)" in caplog.text
        assert isinstance(caplog.records[-1].exc_info[1], RuntimeError)

    async def test_when_step_keeps_failing_expect_exponential_backoff_capped(self, sleeps) -> None:
        step = AsyncMock(side_effect=[RuntimeError()] * 7 + [asyncio.CancelledError()])

        with pytest.raises(asyncio.CancelledError):
            await main._supervise("worker", step)

        assert sleeps == [1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 30.0]

    async def test_when_step_succeeds_after_failures_expect_backoff_reset(self, sleeps) -> None:
        step = AsyncMock(
            side_effect=[
                RuntimeError(),
                RuntimeError(),
                object(),
                RuntimeError(),
                asyncio.CancelledError(),
            ]
        )

        with pytest.raises(asyncio.CancelledError):
            await main._supervise("worker", step)

        assert sleeps == [1.0, 2.0, 1.0]

    async def test_when_step_processes_work_expect_next_step_without_sleeping(self, sleeps) -> None:
        step = AsyncMock(side_effect=[object(), object(), asyncio.CancelledError()])

        with pytest.raises(asyncio.CancelledError):
            await main._supervise("worker", step)

        assert step.await_count == 3
        assert sleeps == []

    async def test_when_worker_is_cancelled_during_step_expect_cancellation_propagated_unlogged(
        self, caplog
    ) -> None:
        started = asyncio.Event()

        async def step():
            started.set()
            await asyncio.Future()

        task = asyncio.create_task(main._supervise("worker", step))
        await started.wait()

        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task
        assert caplog.records == []
