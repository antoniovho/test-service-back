"""Resolution of an executable manifest from an active Test Plan snapshot."""

from uuid import UUID

from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.model.authoring.definition import Definition
from test_service.domain.model.composition.test_plan import TestPlan
from test_service.domain.model.exceptions.invalid_test_plan_exception import (
    InvalidTestPlanException,
)
from test_service.domain.model.lifecycle import VersionStatus
from test_service.domain.ports.output.persistence.preconditions.precondition_persistence_port import (  # noqa: E501
    PreconditionPersistencePort,
)
from test_service.domain.ports.output.persistence.test_cases.test_case_persistence_port import (  # noqa: E501
    TestCasePersistencePort,
)
from test_service.domain.ports.output.persistence.test_sets.test_set_persistence_port import (
    TestSetPersistencePort,
)
from test_service.domain.ports.output.runners.runner_port import RunnerPort


class ExecutionManifestResolver:
    """Resolve and validate the immutable Test Case manifest accepted for execution."""

    def __init__(
        self,
        test_set_repository: TestSetPersistencePort,
        test_case_repository: TestCasePersistencePort,
        precondition_repository: PreconditionPersistencePort,
        compiler: DefinitionCompiler,
        runner: RunnerPort,
    ) -> None:
        self._test_set_repository = test_set_repository
        self._test_case_repository = test_case_repository
        self._precondition_repository = precondition_repository
        self._compiler = compiler
        self._runner = runner

    async def resolve(self, test_plan: TestPlan, project_key: str) -> tuple[UUID, ...]:
        """Return the effective Test Case snapshots valid for a new execution."""
        identifiers = list(test_plan.test_case_ids)
        for test_set_id in test_plan.test_set_ids:
            test_set = await self._test_set_repository.find_by_id(test_set_id)
            if (
                test_set is None
                or test_set.project_key != project_key
                or test_set.status is not VersionStatus.ACTIVE
            ):
                raise InvalidTestPlanException(
                    f"execution references an unavailable test set '{test_set_id}'"
                )
            identifiers.extend(test_set.items)

        selected = tuple(
            identifier for identifier in identifiers if identifier not in test_plan.exclusions
        )
        for identifier in selected:
            test_case = await self._test_case_repository.find_by_id(identifier)
            if (
                test_case is None
                or test_case.project_key != project_key
                or test_case.status is not VersionStatus.ACTIVE
            ):
                raise InvalidTestPlanException(
                    f"execution references an unavailable test case '{identifier}'"
                )
            self._validate_supported_definition(test_case.identifier, test_case.definition)
            for reference in test_case.preconditions:
                precondition = await self._precondition_repository.find_by_id(reference.identifier)
                if (
                    precondition is None
                    or precondition.project_key != project_key
                    or precondition.status is not VersionStatus.ACTIVE
                ):
                    raise InvalidTestPlanException(
                        f"execution references an unavailable precondition '{reference.identifier}'"
                    )
                self._validate_supported_definition(
                    precondition.identifier, precondition.validation_definition
                )
        return selected

    def _validate_supported_definition(self, identifier: UUID, definition: Definition) -> None:
        compiled = self._compiler.compile(identifier, definition)
        action_types = frozenset(action.action_type for action in compiled.actions)
        if not self._runner.supports(action_types):
            raise InvalidTestPlanException("execution contains actions unsupported by the runner")
