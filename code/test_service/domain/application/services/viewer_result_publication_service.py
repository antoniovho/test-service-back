"""Asynchronously project completed local executions to an external viewer."""

import re
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from test_service.config import ViewerSettings
from test_service.domain.application.queries.pagination import MAX_PAGE_LIMIT, PaginationParams
from test_service.domain.model.exceptions.permanent_viewer_result_publication_exception import (
    PermanentViewerResultPublicationError,
)
from test_service.domain.model.exceptions.retryable_viewer_result_publication_exception import (
    RetryableViewerResultPublicationError,
)
from test_service.domain.model.execution.execution import (
    TERMINAL_EXECUTION_STATUSES,
    Execution,
    ExecutionStatus,
)
from test_service.domain.model.viewer.execution_result_projection import (
    ViewerExecutionResultProjection,
    ViewerTestRunProjection,
)
from test_service.domain.model.viewer.execution_results import (
    ViewerResultPublication,
    ViewerResultPublicationStatus,
)
from test_service.domain.model.viewer.records import SyncStatus, ViewerEntityType
from test_service.domain.ports.output.persistence.environments.environment_persistence_port import (
    EnvironmentPersistencePort,
)
from test_service.domain.ports.output.persistence.executions.execution_persistence_port import (
    ExecutionPersistencePort,
)
from test_service.domain.ports.output.persistence.executions.execution_results_persistence_port import (  # noqa: E501
    ExecutionResultsPersistencePort,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (
    TestCasePersistencePort,
)
from test_service.domain.ports.output.persistence.viewer.viewer_persistence_port import (
    ViewerPersistencePort,
)
from test_service.domain.ports.output.persistence.viewer.viewer_result_persistence_port import (
    ViewerResultPersistencePort,
)
from test_service.domain.ports.output.viewer.viewer_result_publisher_port import (
    ViewerResultPublisherPort,
)

_SENSITIVE_VALUE = re.compile(
    r"(?i)(authorization|bearer|token|secret|api[_-]?key|password)"
    r"(\s*[:=]\s*)(?:bearer\s+)?[^\s,;\"'}]+"
)
_MAX_COMMENT_LENGTH = 1_000


class ViewerResultPublicationService:
    """Persist, resolve and publish execution results without blocking runners."""

    def __init__(
        self,
        executions: ExecutionPersistencePort,
        results: ExecutionResultsPersistencePort,
        environments: EnvironmentPersistencePort,
        test_cases: TestCasePersistencePort,
        viewer_records: ViewerPersistencePort,
        publications: ViewerResultPersistencePort,
        publisher: ViewerResultPublisherPort,
        settings: ViewerSettings,
    ) -> None:
        self._executions = executions
        self._results = results
        self._environments = environments
        self._test_cases = test_cases
        self._viewer_records = viewer_records
        self._publications = publications
        self._publisher = publisher
        self._settings = settings

    async def complete_execution(
        self, execution: Execution, expected_statuses: tuple[ExecutionStatus, ...]
    ) -> Execution | None:
        """Atomically persist a terminal execution and its external publication work."""
        return await self._publications.transition_execution_and_enqueue_result_publication(
            execution, expected_statuses, self._publisher.viewer_type
        )

    async def process_next_publication(self) -> ViewerResultPublication | None:
        """Claim one due result publication and complete, retry or fail it safely."""
        publication = await self._publications.claim_next_result_publication()
        if publication is None:
            return None
        try:
            projection = await self._projection(publication)
            identity = await self._publisher.publish_execution_result(projection)
        except RetryableViewerResultPublicationError as error:
            return await self._retry(publication, error)
        except PermanentViewerResultPublicationError as error:
            return await self._fail_permanently(publication, error)
        except Exception as error:
            return await self._retry(publication, error)
        now = datetime.now(UTC)
        return await self._publications.save_result_publication(
            replace(
                publication,
                status=ViewerResultPublicationStatus.SUCCEEDED,
                external_execution_id=identity.execution_id,
                external_execution_key=identity.execution_key,
                finished_at=now,
                updated_at=now,
                error=None,
            )
        )

    async def _projection(
        self, publication: ViewerResultPublication
    ) -> ViewerExecutionResultProjection:
        """Build a viewer-neutral projection from completed local execution data."""
        execution = await self._executions.find_execution(publication.execution_id)
        if execution is None:
            raise PermanentViewerResultPublicationError(
                f"Local execution '{publication.execution_id}' for Viewer result publication "
                f"'{publication.identifier}' no longer exists."
            )
        if execution.status not in TERMINAL_EXECUTION_STATUSES:
            raise RetryableViewerResultPublicationError(
                f"Local execution '{execution.identifier}' is "
                f"'{execution.status.value}' and has not reached a terminal state "
                f"for Viewer result publication '{publication.identifier}'."
            )
        environment = await self._environments.find_by_id(execution.environment_id)
        if environment is None:
            raise PermanentViewerResultPublicationError(
                f"Environment '{execution.environment_id}' for execution "
                f"'{execution.identifier}' no longer exists."
            )
        results = await self._all_results(execution.identifier)
        test_runs = []
        for result in results:
            test_runs.append(await self._test_run_projection(publication, execution, result))
        return ViewerExecutionResultProjection(
            publication=publication,
            summary=f"Test Service execution {execution.identifier}",
            environment_name=environment.name[:255],
            execution_status=execution.status,
            test_runs=tuple(test_runs),
        )

    async def _all_results(self, execution_id) -> tuple:
        """Load every persisted result for an execution through paginated queries."""
        offset = 0
        collected = []
        while True:
            page = await self._results.find_results_page(
                execution_id, PaginationParams(offset=offset, limit=MAX_PAGE_LIMIT)
            )
            collected.extend(page.items)
            offset += len(page.items)
            if offset >= page.total:
                return tuple(collected)

    async def _test_run_projection(
        self,
        publication: ViewerResultPublication,
        execution: Execution,
        result,
    ) -> ViewerTestRunProjection:
        """Resolve a local result and its synced Test Case into a viewer test run."""
        test_case = await self._test_cases.find_by_id(result.test_case_id)
        if test_case is None:
            raise PermanentViewerResultPublicationError(
                f"Test Case snapshot '{result.test_case_id}' for Test Result "
                f"'{result.identifier}' in execution '{execution.identifier}' no longer exists."
            )
        record = await self._viewer_records.find_sync_record(
            execution.project_key,
            ViewerEntityType.TEST_CASE,
            test_case.logical_key,
            test_case.version,
            publication.viewer_type,
        )
        if (
            record is None
            or record.sync_status is not SyncStatus.SYNCED
            or not record.external_entity_id
        ):
            raise RetryableViewerResultPublicationError(
                f"Viewer Test Case identity is not synchronized for Test Result "
                f"'{result.identifier}', snapshot '{test_case.identifier}' "
                f"('{test_case.logical_key}' version {test_case.version}), project "
                f"'{execution.project_key}', viewer '{publication.viewer_type.value}', "
                f"and publication '{publication.identifier}'."
            )
        return ViewerTestRunProjection(
            test_result_id=result.identifier,
            external_test_id=record.external_entity_id,
            status=result.status,
            started_at=result.started_at,
            finished_at=result.finished_at,
            duration_ms=result.duration_ms,
            comment=self._comment(result.error_code, result.error_message),
        )

    async def _retry(
        self, publication: ViewerResultPublication, error: Exception
    ) -> ViewerResultPublication:
        """Defer a failed publication using bounded exponential backoff."""
        delay = min(
            self._settings.result_retry_backoff_seconds * 2 ** (publication.attempts - 1),
            self._settings.result_retry_max_seconds,
        )
        now = datetime.now(UTC)
        return await self._publications.save_result_publication(
            replace(
                publication,
                status=ViewerResultPublicationStatus.RETRY_WAIT,
                next_attempt_at=now + timedelta(seconds=delay),
                updated_at=now,
                error=self._publication_error(publication, error),
            )
        )

    async def _fail_permanently(
        self, publication: ViewerResultPublication, error: Exception
    ) -> ViewerResultPublication:
        """Mark an unrecoverable publication failure as terminal."""
        now = datetime.now(UTC)
        return await self._publications.save_result_publication(
            replace(
                publication,
                status=ViewerResultPublicationStatus.FAILED_PERMANENT,
                finished_at=now,
                updated_at=now,
                error=self._publication_error(publication, error),
            )
        )

    @staticmethod
    def _comment(error_code: str | None, error_message: str | None) -> str | None:
        """Format and redact optional local error details for viewer publication."""
        values = [value for value in (error_code, error_message) if value]
        if not values:
            return None
        return ViewerResultPublicationService._safe_text(": ".join(values))

    @staticmethod
    def _safe_error(error: Exception) -> str:
        """Return a bounded, redacted representation of an exception."""
        return ViewerResultPublicationService._safe_text(str(error) or type(error).__name__)

    @staticmethod
    def _publication_error(publication: ViewerResultPublication, error: Exception) -> str:
        """Return a redacted failure message with durable publication correlation."""
        return ViewerResultPublicationService._safe_text(
            f"Viewer result publication '{publication.identifier}' for execution "
            f"'{publication.execution_id}' failed: {str(error) or type(error).__name__}"
        )

    @staticmethod
    def _safe_text(value: str) -> str:
        """Redact sensitive key-value pairs and cap viewer-facing text length."""
        return _SENSITIVE_VALUE.sub(r"\1\2[REDACTED]", value)[:_MAX_COMMENT_LENGTH]
