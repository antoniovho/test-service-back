"""Persistence and external-boundary contracts used by application services."""

from collections.abc import Mapping
from typing import Protocol
from uuid import UUID

from test_service.domain.commons.pagination import Page, PaginationParams
from test_service.domain.model.authoring.precondition import Precondition
from test_service.domain.model.authoring.test_case import TestCase
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.composition.test_set import TestSet
from test_service.domain.model.execution.environment import Environment, SecretReference
from test_service.domain.model.execution.execution import (
    ActionResult,
    Execution,
    TestResult,
    TestResultArtifact,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.model.projects.project import Project
from test_service.domain.model.viewer.records import DriftEvent, ViewerSyncRecord


class ProjectRepositoryPort(Protocol):
    """Persistence contract for Project Catalog entries."""

    async def save(self, project: Project) -> Project:
        """Persist a project.

        Args:
            project: Project to persist.

        Returns:
            Persisted project.
        """
        ...

    async def find_by_key(self, key: str) -> Project | None:
        """Find a project by its stable key.

        Args:
            key: Stable project key.

        Returns:
            The project, or ``None`` when absent.
        """
        ...

    async def find_page(self, pagination: PaginationParams) -> Page[Project]:
        """Find a page of projects.

        Args:
            pagination: Page and ordering parameters.

        Returns:
            Matching project page.
        """
        ...


class VersionedRepositoryPort[Snapshot](Protocol):
    """Persistence contract for immutable versioned snapshots."""

    async def save(self, snapshot: Snapshot) -> Snapshot:
        """Persist a new or transitioned snapshot.

        Args:
            snapshot: Snapshot to persist.

        Returns:
            Persisted snapshot.
        """
        ...

    async def find_by_id(self, identifier: UUID) -> Snapshot | None:
        """Find a snapshot by UUID.

        Args:
            identifier: Snapshot UUID.

        Returns:
            Snapshot, or ``None`` when absent.
        """
        ...


class TestCaseRepositoryPort(VersionedRepositoryPort[TestCase], Protocol):
    """Persistence contract for TestCase snapshots."""

    async def find_page(
        self,
        project_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestCase]:
        """Find a page of TestCase snapshots owned by one project.

        Args:
            project_key: Owning project key.
            pagination: Page and ordering parameters.
            status: Optional lifecycle status filter.

        Returns:
            Matching TestCase snapshot page.
        """
        ...

    async def find_versions(self, identifier: UUID, pagination: PaginationParams) -> Page[TestCase]:
        """Find a page of every snapshot sharing the test key of one snapshot.

        Args:
            identifier: UUID of any snapshot version of the test case.
            pagination: Page parameters.

        Returns:
            Matching TestCase snapshot version page, ordered by version.
        """
        ...


class PreconditionRepositoryPort(VersionedRepositoryPort[Precondition], Protocol):
    """Persistence contract for Precondition snapshots."""

    async def find_page(
        self,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[Precondition]:
        """Find a page of Precondition snapshots.

        Args:
            pagination: Page and ordering parameters.
            status: Optional lifecycle status filter.

        Returns:
            Matching Precondition snapshot page.
        """
        ...

    async def find_versions(
        self, identifier: UUID, pagination: PaginationParams
    ) -> Page[Precondition]:
        """Find a page of every snapshot sharing the precondition key of one snapshot.

        Args:
            identifier: UUID of any snapshot version of the precondition.
            pagination: Page parameters.

        Returns:
            Matching Precondition snapshot version page, ordered by version.
        """
        ...


class TestSetRepositoryPort(VersionedRepositoryPort[TestSet], Protocol):
    """Persistence contract for TestSet snapshots."""

    async def find_page(
        self,
        project_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestSet]:
        """Find a page of TestSet snapshots owned by one project.

        Args:
            project_key: Owning project key.
            pagination: Page and ordering parameters.
            status: Optional lifecycle status filter.

        Returns:
            Matching TestSet snapshot page.
        """
        ...


class TestPlanRepositoryPort(VersionedRepositoryPort[TestPlan], Protocol):
    """Persistence contract for TestPlan snapshots."""

    async def find_page(
        self,
        project_key: str,
        pagination: PaginationParams,
        status: VersionStatus | None = None,
    ) -> Page[TestPlan]:
        """Find a page of TestPlan snapshots owned by one project.

        Args:
            project_key: Owning project key.
            pagination: Page and ordering parameters.
            status: Optional lifecycle status filter.

        Returns:
            Matching TestPlan snapshot page.
        """
        ...


class EnvironmentRepositoryPort(Protocol):
    """Persistence contract for execution environments."""

    async def save(self, environment: Environment) -> Environment:
        """Persist an environment.

        Args:
            environment: Environment to persist.

        Returns:
            Persisted environment.
        """
        ...

    async def find_by_id(self, identifier: UUID) -> Environment | None:
        """Find an environment by UUID.

        Args:
            identifier: Environment UUID.

        Returns:
            Environment, or ``None`` when absent.
        """
        ...

    async def find_page(self, pagination: PaginationParams) -> Page[Environment]:
        """Find a page of environments.

        Args:
            pagination: Page parameters.

        Returns:
            Matching environment page.
        """
        ...


class ExecutionRepositoryPort(Protocol):
    """Persistence contract for executions and their immutable history."""

    async def save_execution(self, execution: Execution) -> Execution:
        """Persist an execution.

        Args:
            execution: Execution to persist.

        Returns:
            Persisted execution.
        """
        ...

    async def find_execution(self, identifier: UUID) -> Execution | None:
        """Find an execution by UUID.

        Args:
            identifier: Execution UUID.

        Returns:
            Execution, or ``None`` when absent.
        """
        ...

    async def find_page(self, project_key: str, pagination: PaginationParams) -> Page[Execution]:
        """Find a page of executions owned by one project.

        Args:
            project_key: Owning project key.
            pagination: Page parameters.

        Returns:
            Matching execution page.
        """
        ...


class ExecutionResultsPort(Protocol):
    """Read contract for immutable execution result details."""

    async def find_result(self, identifier: UUID) -> TestResult | None:
        """Find a test result by UUID.

        Args:
            identifier: Test result UUID.

        Returns:
            Test result, or ``None`` when absent.
        """
        ...

    async def find_results_page(
        self, execution_id: UUID, pagination: PaginationParams
    ) -> Page[TestResult]:
        """Find a page of test results belonging to an execution.

        Args:
            execution_id: Owning execution UUID.
            pagination: Page parameters.

        Returns:
            Matching test result page.
        """
        ...

    async def find_actions_page(
        self, test_result_id: UUID, pagination: PaginationParams
    ) -> Page[ActionResult]:
        """Find a page of action results belonging to a test result.

        Args:
            test_result_id: Owning test result UUID.
            pagination: Page parameters.

        Returns:
            Matching action result page.
        """
        ...

    async def find_artifacts_page(
        self, test_result_id: UUID, pagination: PaginationParams
    ) -> Page[TestResultArtifact]:
        """Find a page of artifacts belonging to a test result.

        Args:
            test_result_id: Owning test result UUID.
            pagination: Page parameters.

        Returns:
            Matching artifact page.
        """
        ...


class JiraProjectValidatorPort(Protocol):
    """Read-only external contract for Jira project validation."""

    async def is_active(self, project_key: str) -> bool:
        """Check whether a Jira project exists and is active.

        Args:
            project_key: Stable Jira project key.

        Returns:
            ``True`` when Jira recognizes an active project.
        """
        ...


class ExecutionSchedulerPort(Protocol):
    """External contract that schedules and cancels validated executions."""

    async def schedule(self, execution_id: UUID) -> None:
        """Schedule an accepted execution.

        Args:
            execution_id: UUID of the execution to schedule.

        Returns:
            ``None``.
        """
        ...

    async def cancel(self, execution_id: UUID) -> None:
        """Request cancellation of a scheduled or running execution.

        Args:
            execution_id: UUID of the execution to cancel.

        Returns:
            ``None``.
        """
        ...


class ActionDefinitionValidatorPort(Protocol):
    """Read-only external contract that validates actions against the Action Registry."""

    async def validate(self, action_type: str, configuration: Mapping[str, object]) -> None:
        """Validate an action type and its configuration against the Action Registry.

        Args:
            action_type: Action Registry type declared by the action.
            configuration: Action-specific configuration to validate.

        Returns:
            ``None``.

        Raises:
            InvalidActionException: If the Action Registry rejects the type or configuration.
        """
        ...


class SecretResolverPort(Protocol):
    """External contract that resolves secret references at the point of use.

    Resolved values must never be persisted or returned by the domain; only the
    SecretReference is stored in Environment.configuration.
    """

    async def resolve(self, reference: SecretReference) -> str:
        """Resolve a secret reference to its current value.

        Args:
            reference: Provider and lookup key identifying the secret.

        Returns:
            The resolved secret value.
        """
        ...


class ViewerRepositoryPort(Protocol):
    """Persistence contract for Viewer synchronization state."""

    async def save_sync_record(self, record: ViewerSyncRecord) -> ViewerSyncRecord:
        """Persist a synchronization record.

        Args:
            record: Record to persist.

        Returns:
            Persisted synchronization record.
        """
        ...

    async def save_drift_event(self, event: DriftEvent) -> DriftEvent:
        """Persist a drift event.

        Args:
            event: Event to persist.

        Returns:
            Persisted drift event.
        """
        ...

    async def find_sync_records_page(self, pagination: PaginationParams) -> Page[ViewerSyncRecord]:
        """Find a page of Viewer synchronization records across all projects.

        Args:
            pagination: Page parameters.

        Returns:
            Matching synchronization record page.
        """
        ...

    async def find_sync_records_page_by_project(
        self, project_key: str, pagination: PaginationParams
    ) -> Page[ViewerSyncRecord]:
        """Find a page of Viewer synchronization records owned by one project.

        Args:
            project_key: Owning project key.
            pagination: Page parameters.

        Returns:
            Matching synchronization record page.
        """
        ...

    async def find_drift_events_page(self, pagination: PaginationParams) -> Page[DriftEvent]:
        """Find a page of Viewer drift events across all projects.

        Args:
            pagination: Page parameters.

        Returns:
            Matching drift event page.
        """
        ...

    async def find_drift_events_page_by_project(
        self, project_key: str, pagination: PaginationParams
    ) -> Page[DriftEvent]:
        """Find a page of Viewer drift events owned by one project.

        Args:
            project_key: Owning project key.
            pagination: Page parameters.

        Returns:
            Matching drift event page.
        """
        ...


class ViewerPublisherPort(Protocol):
    """External contract that publishes canonical projections to the external Viewer."""

    async def publish(self, record: ViewerSyncRecord) -> None:
        """Asynchronously publish one canonical projection to the external Viewer.

        Args:
            record: Synchronization record describing the projection to publish.

        Returns:
            ``None``.
        """
        ...


class ViewerDriftDetectorPort(Protocol):
    """External contract that checks the external Viewer for drift."""

    async def check_drift(self, record: ViewerSyncRecord) -> None:
        """Asynchronously check one Viewer projection for drift from the canonical version.

        Args:
            record: Synchronization record describing the projection to check.

        Returns:
            ``None``.
        """
        ...
