"""Domain IoC module — binds use case ports to their implementations."""

from opyoid import Module  # type: ignore

from test_service.domain.application.services.execution.definition_compiler import (
    DefinitionCompiler,
)
from test_service.domain.application.services.execution.execution_variables_resolver import (
    ExecutionVariablesResolver,
)
from test_service.domain.application.services.resolvers.execution_access_resolver import (
    ExecutionAccessResolver,
)
from test_service.domain.application.services.resolvers.execution_manifest_resolver import (
    ExecutionManifestResolver,
)
from test_service.domain.application.services.resolvers.execution_result_access_resolver import (
    ExecutionResultAccessResolver,
)
from test_service.domain.application.services.resolvers.precondition_reference_resolver import (
    PreconditionReferenceResolver,
)
from test_service.domain.application.services.resolvers.project_resolver import ProjectResolver
from test_service.domain.application.services.resolvers.test_case_snapshot_resolver import (
    TestCaseSnapshotResolver,
)
from test_service.domain.application.services.resolvers.test_set_snapshot_resolver import (
    TestSetSnapshotResolver,
)
from test_service.domain.application.services.viewer_projection_service import (
    ViewerProjectionService,
)
from test_service.domain.application.use_cases.authoring.preconditions.activate_precondition_use_case import (  # noqa: E501
    ActivatePreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.create_precondition_use_case import (  # noqa: E501
    CreatePreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.create_precondition_version_use_case import (  # noqa: E501
    CreatePreconditionVersionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.deprecate_precondition_use_case import (  # noqa: E501
    DeprecatePreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.get_precondition_use_case import (  # noqa: E501
    GetPreconditionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.list_precondition_versions_use_case import (  # noqa: E501
    ListPreconditionVersionsUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.preconditions.list_preconditions_use_case import (  # noqa: E501
    ListPreconditionsUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.activate_test_case_use_case import (  # noqa: E501
    ActivateTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.create_test_case_use_case import (  # noqa: E501
    CreateTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.create_test_case_version_use_case import (  # noqa: E501
    CreateTestCaseVersionUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.deprecate_test_case_use_case import (  # noqa: E501
    DeprecateTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.get_test_case_use_case import (  # noqa: E501
    GetTestCaseUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.list_test_case_versions_use_case import (  # noqa: E501
    ListTestCaseVersionsUseCaseImpl,
)
from test_service.domain.application.use_cases.authoring.test_cases.list_test_cases_use_case import (  # noqa: E501
    ListTestCasesUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_plans.activate_test_plan_use_case import (  # noqa: E501
    ActivateTestPlanUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_plans.create_test_plan_use_case import (  # noqa: E501
    CreateTestPlanUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_plans.create_test_plan_version_use_case import (  # noqa: E501
    CreateTestPlanVersionUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_plans.deprecate_test_plan_use_case import (  # noqa: E501
    DeprecateTestPlanUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_plans.get_test_plan_use_case import (  # noqa: E501
    GetTestPlanUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_plans.list_test_plan_versions_use_case import (  # noqa: E501
    ListTestPlanVersionsUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_plans.list_test_plans_use_case import (  # noqa: E501
    ListTestPlansUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.activate_test_set_use_case import (  # noqa: E501
    ActivateTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.create_test_set_use_case import (  # noqa: E501
    CreateTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.create_test_set_version_use_case import (  # noqa: E501
    CreateTestSetVersionUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.deprecate_test_set_use_case import (  # noqa: E501
    DeprecateTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.get_test_set_use_case import (  # noqa: E501
    GetTestSetUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.list_test_set_versions_use_case import (  # noqa: E501
    ListTestSetVersionsUseCaseImpl,
)
from test_service.domain.application.use_cases.composition.test_sets.list_test_sets_use_case import (  # noqa: E501
    ListTestSetsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.environments.activate_environment_use_case import (  # noqa: E501
    ActivateEnvironmentUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.environments.create_environment_use_case import (  # noqa: E501
    CreateEnvironmentUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.environments.deactivate_environment_use_case import (  # noqa: E501
    DeactivateEnvironmentUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.environments.get_environment_use_case import (  # noqa: E501
    GetEnvironmentUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.environments.list_environments_use_case import (  # noqa: E501
    ListEnvironmentsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.cancel_execution_use_case import (  # noqa: E501
    CancelExecutionUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.get_execution_result_use_case import (  # noqa: E501
    GetExecutionResultUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.get_execution_use_case import (  # noqa: E501
    GetExecutionUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_execution_result_actions_use_case import (  # noqa: E501
    ListExecutionResultActionsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_execution_result_artifacts_use_case import (  # noqa: E501
    ListExecutionResultArtifactsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_execution_results_use_case import (  # noqa: E501
    ListExecutionResultsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.list_executions_use_case import (  # noqa: E501
    ListExecutionsUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.process_next_execution_use_case import (  # noqa: E501
    ProcessNextExecutionUseCaseImpl,
)
from test_service.domain.application.use_cases.execution.executions.schedule_execution_use_case import (  # noqa: E501
    ScheduleExecutionUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.create_project_use_case import (
    CreateProjectUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.delete_project_use_case import (
    DeleteProjectUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.get_project_use_case import (
    GetProjectUseCaseImpl,
)
from test_service.domain.application.use_cases.projects.list_projects_use_case import (
    ListProjectsUseCaseImpl,
)
from test_service.domain.application.use_cases.viewer.check_viewer_drift_use_case import (
    CheckViewerDriftUseCaseImpl,
)
from test_service.domain.application.use_cases.viewer.drift.list_project_viewer_drift_events_use_case import (  # noqa: E501
    ListProjectViewerDriftEventsUseCaseImpl,
)
from test_service.domain.application.use_cases.viewer.drift.list_viewer_drift_events_use_case import (  # noqa: E501
    ListViewerDriftEventsUseCaseImpl,
)
from test_service.domain.application.use_cases.viewer.operations.get_project_viewer_operation_use_case import (  # noqa: E501
    GetProjectViewerOperationUseCaseImpl,
)
from test_service.domain.application.use_cases.viewer.operations.list_project_viewer_operations_use_case import (  # noqa: E501
    ListProjectViewerOperationsUseCaseImpl,
)
from test_service.domain.application.use_cases.viewer.operations.list_viewer_operations_use_case import (  # noqa: E501
    ListViewerOperationsUseCaseImpl,
)
from test_service.domain.application.use_cases.viewer.publish_viewer_projection_use_case import (
    PublishViewerProjectionUseCaseImpl,
)
from test_service.domain.application.use_cases.viewer.sync_records.list_project_viewer_sync_records_use_case import (  # noqa: E501
    ListProjectViewerSyncRecordsUseCaseImpl,
)
from test_service.domain.application.use_cases.viewer.sync_records.list_viewer_sync_records_use_case import (  # noqa: E501
    ListViewerSyncRecordsUseCaseImpl,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.activate_precondition_use_case import (  # noqa: E501
    ActivatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_use_case import (  # noqa: E501
    CreatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.create_precondition_version_use_case import (  # noqa: E501
    CreatePreconditionVersionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.deprecate_precondition_use_case import (  # noqa: E501
    DeprecatePreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.get_precondition_use_case import (  # noqa: E501
    GetPreconditionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.list_precondition_versions_use_case import (  # noqa: E501
    ListPreconditionVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.preconditions.list_preconditions_use_case import (  # noqa: E501
    ListPreconditionsUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.activate_test_case_use_case import (  # noqa: E501
    ActivateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_use_case import (  # noqa: E501
    CreateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.create_test_case_version_use_case import (  # noqa: E501
    CreateTestCaseVersionUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.deprecate_test_case_use_case import (  # noqa: E501
    DeprecateTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.get_test_case_use_case import (  # noqa: E501
    GetTestCaseUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.list_test_case_versions_use_case import (  # noqa: E501
    ListTestCaseVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.authoring.test_cases.list_test_cases_use_case import (  # noqa: E501
    ListTestCasesUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.activate_test_plan_use_case import (  # noqa: E501
    ActivateTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.create_test_plan_use_case import (  # noqa: E501
    CreateTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.create_test_plan_version_use_case import (  # noqa: E501
    CreateTestPlanVersionUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.deprecate_test_plan_use_case import (  # noqa: E501
    DeprecateTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.get_test_plan_use_case import (  # noqa: E501
    GetTestPlanUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.list_test_plan_versions_use_case import (  # noqa: E501
    ListTestPlanVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_plans.list_test_plans_use_case import (  # noqa: E501
    ListTestPlansUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.activate_test_set_use_case import (  # noqa: E501
    ActivateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.create_test_set_use_case import (  # noqa: E501
    CreateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.create_test_set_version_use_case import (  # noqa: E501
    CreateTestSetVersionUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.deprecate_test_set_use_case import (  # noqa: E501
    DeprecateTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.get_test_set_use_case import (
    GetTestSetUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.list_test_set_versions_use_case import (  # noqa: E501
    ListTestSetVersionsUseCase,
)
from test_service.domain.ports.input.use_cases.composition.test_sets.list_test_sets_use_case import (  # noqa: E501
    ListTestSetsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.activate_environment_use_case import (  # noqa: E501
    ActivateEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.create_environment_use_case import (  # noqa: E501
    CreateEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.deactivate_environment_use_case import (  # noqa: E501
    DeactivateEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.get_environment_use_case import (  # noqa: E501
    GetEnvironmentUseCase,
)
from test_service.domain.ports.input.use_cases.execution.environments.list_environments_use_case import (  # noqa: E501
    ListEnvironmentsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.cancel_execution_use_case import (  # noqa: E501
    CancelExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.get_execution_result_use_case import (  # noqa: E501
    GetExecutionResultUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.get_execution_use_case import (  # noqa: E501
    GetExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_result_actions_use_case import (  # noqa: E501
    ListExecutionResultActionsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_result_artifacts_use_case import (  # noqa: E501
    ListExecutionResultArtifactsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_execution_results_use_case import (  # noqa: E501
    ListExecutionResultsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.list_executions_use_case import (  # noqa: E501
    ListExecutionsUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.process_next_execution_use_case import (  # noqa: E501
    ProcessNextExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.execution.executions.schedule_execution_use_case import (  # noqa: E501
    ScheduleExecutionUseCase,
)
from test_service.domain.ports.input.use_cases.projects.create_project_use_case import (
    CreateProjectUseCase,
)
from test_service.domain.ports.input.use_cases.projects.delete_project_use_case import (
    DeleteProjectUseCase,
)
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.domain.ports.input.use_cases.projects.list_projects_use_case import (
    ListProjectsUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.check_viewer_drift_use_case import (
    CheckViewerDriftUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.drift.list_project_viewer_drift_events_use_case import (  # noqa: E501
    ListProjectViewerDriftEventsUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.drift.list_viewer_drift_events_use_case import (  # noqa: E501
    ListViewerDriftEventsUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.operations.get_project_viewer_operation_use_case import (  # noqa: E501
    GetProjectViewerOperationUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.operations.list_project_viewer_operations_use_case import (  # noqa: E501
    ListProjectViewerOperationsUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.operations.list_viewer_operations_use_case import (  # noqa: E501
    ListViewerOperationsUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.publish_viewer_projection_use_case import (
    PublishViewerProjectionUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.sync_records.list_project_viewer_sync_records_use_case import (  # noqa: E501
    ListProjectViewerSyncRecordsUseCase,
)
from test_service.domain.ports.input.use_cases.viewer.sync_records.list_viewer_sync_records_use_case import (  # noqa: E501
    ListViewerSyncRecordsUseCase,
)


class ProjectsModule(Module):
    """Binds Project Catalog use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(ListProjectsUseCase, to_class=ListProjectsUseCaseImpl)
        self.bind(CreateProjectUseCase, to_class=CreateProjectUseCaseImpl)
        self.bind(GetProjectUseCase, to_class=GetProjectUseCaseImpl)
        self.bind(DeleteProjectUseCase, to_class=DeleteProjectUseCaseImpl)


class TestCasesModule(Module):
    """Binds Test Case use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(PreconditionReferenceResolver)
        self.bind(CreateTestCaseUseCase, to_class=CreateTestCaseUseCaseImpl)
        self.bind(CreateTestCaseVersionUseCase, to_class=CreateTestCaseVersionUseCaseImpl)
        self.bind(ActivateTestCaseUseCase, to_class=ActivateTestCaseUseCaseImpl)
        self.bind(DeprecateTestCaseUseCase, to_class=DeprecateTestCaseUseCaseImpl)
        self.bind(GetTestCaseUseCase, to_class=GetTestCaseUseCaseImpl)
        self.bind(ListTestCasesUseCase, to_class=ListTestCasesUseCaseImpl)
        self.bind(ListTestCaseVersionsUseCase, to_class=ListTestCaseVersionsUseCaseImpl)


class PreconditionsModule(Module):
    """Binds Precondition use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(CreatePreconditionUseCase, to_class=CreatePreconditionUseCaseImpl)
        self.bind(CreatePreconditionVersionUseCase, to_class=CreatePreconditionVersionUseCaseImpl)
        self.bind(ActivatePreconditionUseCase, to_class=ActivatePreconditionUseCaseImpl)
        self.bind(DeprecatePreconditionUseCase, to_class=DeprecatePreconditionUseCaseImpl)
        self.bind(GetPreconditionUseCase, to_class=GetPreconditionUseCaseImpl)
        self.bind(ListPreconditionsUseCase, to_class=ListPreconditionsUseCaseImpl)
        self.bind(ListPreconditionVersionsUseCase, to_class=ListPreconditionVersionsUseCaseImpl)


class TestSetsModule(Module):
    """Binds Test Set composition use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(TestCaseSnapshotResolver)
        self.bind(CreateTestSetUseCase, to_class=CreateTestSetUseCaseImpl)
        self.bind(CreateTestSetVersionUseCase, to_class=CreateTestSetVersionUseCaseImpl)
        self.bind(ActivateTestSetUseCase, to_class=ActivateTestSetUseCaseImpl)
        self.bind(DeprecateTestSetUseCase, to_class=DeprecateTestSetUseCaseImpl)
        self.bind(GetTestSetUseCase, to_class=GetTestSetUseCaseImpl)
        self.bind(ListTestSetsUseCase, to_class=ListTestSetsUseCaseImpl)
        self.bind(ListTestSetVersionsUseCase, to_class=ListTestSetVersionsUseCaseImpl)


class TestPlansModule(Module):
    """Binds Test Plan composition use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(TestSetSnapshotResolver)
        self.bind(CreateTestPlanUseCase, to_class=CreateTestPlanUseCaseImpl)
        self.bind(CreateTestPlanVersionUseCase, to_class=CreateTestPlanVersionUseCaseImpl)
        self.bind(ActivateTestPlanUseCase, to_class=ActivateTestPlanUseCaseImpl)
        self.bind(DeprecateTestPlanUseCase, to_class=DeprecateTestPlanUseCaseImpl)
        self.bind(GetTestPlanUseCase, to_class=GetTestPlanUseCaseImpl)
        self.bind(ListTestPlansUseCase, to_class=ListTestPlansUseCaseImpl)
        self.bind(ListTestPlanVersionsUseCase, to_class=ListTestPlanVersionsUseCaseImpl)


class EnvironmentsModule(Module):
    """Binds execution environment use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(CreateEnvironmentUseCase, to_class=CreateEnvironmentUseCaseImpl)
        self.bind(GetEnvironmentUseCase, to_class=GetEnvironmentUseCaseImpl)
        self.bind(ListEnvironmentsUseCase, to_class=ListEnvironmentsUseCaseImpl)
        self.bind(ActivateEnvironmentUseCase, to_class=ActivateEnvironmentUseCaseImpl)
        self.bind(DeactivateEnvironmentUseCase, to_class=DeactivateEnvironmentUseCaseImpl)


class ExecutionsModule(Module):
    """Binds Test Plan execution use case ports to their implementations."""

    def configure(self) -> None:
        self.bind(DefinitionCompiler)
        self.bind(ExecutionVariablesResolver)
        self.bind(ExecutionAccessResolver)
        self.bind(ExecutionResultAccessResolver)
        self.bind(ExecutionManifestResolver)
        self.bind(ScheduleExecutionUseCase, to_class=ScheduleExecutionUseCaseImpl)
        self.bind(GetExecutionUseCase, to_class=GetExecutionUseCaseImpl)
        self.bind(ListExecutionsUseCase, to_class=ListExecutionsUseCaseImpl)
        self.bind(ProcessNextExecutionUseCase, to_class=ProcessNextExecutionUseCaseImpl)
        self.bind(CancelExecutionUseCase, to_class=CancelExecutionUseCaseImpl)
        self.bind(ListExecutionResultsUseCase, to_class=ListExecutionResultsUseCaseImpl)
        self.bind(GetExecutionResultUseCase, to_class=GetExecutionResultUseCaseImpl)
        self.bind(ListExecutionResultActionsUseCase, to_class=ListExecutionResultActionsUseCaseImpl)
        self.bind(
            ListExecutionResultArtifactsUseCase, to_class=ListExecutionResultArtifactsUseCaseImpl
        )


class ViewerModule(Module):
    def configure(self) -> None:
        self.bind(ViewerProjectionService)
        self.bind(PublishViewerProjectionUseCase, to_class=PublishViewerProjectionUseCaseImpl)
        self.bind(CheckViewerDriftUseCase, to_class=CheckViewerDriftUseCaseImpl)
        self.bind(ListViewerSyncRecordsUseCase, to_class=ListViewerSyncRecordsUseCaseImpl)
        self.bind(
            ListProjectViewerSyncRecordsUseCase, to_class=ListProjectViewerSyncRecordsUseCaseImpl
        )
        self.bind(ListViewerDriftEventsUseCase, to_class=ListViewerDriftEventsUseCaseImpl)
        self.bind(ListViewerOperationsUseCase, to_class=ListViewerOperationsUseCaseImpl)
        self.bind(
            ListProjectViewerOperationsUseCase, to_class=ListProjectViewerOperationsUseCaseImpl
        )
        self.bind(GetProjectViewerOperationUseCase, to_class=GetProjectViewerOperationUseCaseImpl)
        self.bind(
            ListProjectViewerDriftEventsUseCase, to_class=ListProjectViewerDriftEventsUseCaseImpl
        )


class DomainModule(Module):
    """Domain modules available in the runnable application composition."""

    def configure(self) -> None:
        self.bind(ProjectResolver)
        self.install(ProjectsModule)
        self.install(TestCasesModule)
        self.install(PreconditionsModule)
        self.install(TestSetsModule)
        self.install(TestPlansModule)
        self.install(EnvironmentsModule)
        self.install(ExecutionsModule)
        self.install(ViewerModule)
