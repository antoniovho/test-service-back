from types import SimpleNamespace
from unittest.mock import MagicMock

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
from test_service.domain.ports.input.use_cases.projects.get_project_use_case import (
    GetProjectUseCase,
)
from test_service.infrastructure.adapters.input.rest.composition.test_plans.test_plans_rest_controller import (  # noqa: E501
    TestPlansRestController,
)


class TestTestPlansRestController:
    def test_when_constructed_expect_all_required_use_cases_injected(self, monkeypatch):
        injector = SimpleNamespace(inject=MagicMock(side_effect=range(8)))
        monkeypatch.setattr(
            "test_service.infrastructure.adapters.input.rest.composition.test_plans."
            "test_plans_rest_controller.get_injector",
            lambda: injector,
        )

        controller = TestPlansRestController()

        assert controller._create == 0
        assert controller._get_project == 7
        assert injector.inject.call_args_list == [
            ((CreateTestPlanUseCase,),),
            ((CreateTestPlanVersionUseCase,),),
            ((GetTestPlanUseCase,),),
            ((ActivateTestPlanUseCase,),),
            ((DeprecateTestPlanUseCase,),),
            ((ListTestPlansUseCase,),),
            ((ListTestPlanVersionsUseCase,),),
            ((GetProjectUseCase,),),
        ]
