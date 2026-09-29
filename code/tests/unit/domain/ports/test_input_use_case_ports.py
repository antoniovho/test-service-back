"""Structural tests for input port Protocols.

Ensures every use-case Protocol under ``domain.ports.input.use_cases`` exposes a
correctly typed, asynchronous ``execute`` method, matching the generic
``AsyncUseCase[Request, Response]`` contract.
"""

import inspect
import pkgutil
from importlib import import_module
from typing import Protocol

import pytest

from test_service.domain.ports.input import use_cases
from test_service.domain.ports.input.use_case import AsyncUseCase


def _discover_use_case_classes() -> list[type]:
    """Import every module under ``use_cases`` and collect ``*UseCase`` Protocols.

    Returns:
        One class object per discovered ``*UseCase`` Protocol, defined directly
        in (not merely imported into) its module.
    """
    discovered: list[type] = []
    prefix = use_cases.__name__ + "."
    for module_info in pkgutil.walk_packages(use_cases.__path__, prefix=prefix):
        module = import_module(module_info.name)
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and obj.__module__ == module.__name__
                and name.endswith("UseCase")
            ):
                discovered.append(obj)
    return discovered


USE_CASE_CLASSES = _discover_use_case_classes()


def test_when_discovering_use_cases_expect_at_least_one_per_bounded_context():
    module_prefixes = {cls.__module__.split(".")[5] for cls in USE_CASE_CLASSES}

    assert USE_CASE_CLASSES, "no *UseCase Protocols were discovered"
    assert module_prefixes == {
        "projects",
        "authoring",
        "composition",
        "execution",
        "viewer",
    }


@pytest.mark.parametrize("use_case_cls", USE_CASE_CLASSES, ids=lambda cls: cls.__qualname__)
class TestUseCasePortContract:
    def test_when_inspecting_class_expect_it_is_a_protocol(self, use_case_cls: type):
        assert Protocol in use_case_cls.__mro__

    def test_when_inspecting_class_expect_async_use_case_base(self, use_case_cls: type):
        orig_bases = getattr(use_case_cls, "__orig_bases__", ())
        base_origins = [getattr(base, "__origin__", base) for base in orig_bases]

        assert AsyncUseCase in base_origins

    def test_when_inspecting_execute_expect_single_coroutine_method(self, use_case_cls: type):
        assert hasattr(use_case_cls, "execute")
        assert inspect.iscoroutinefunction(use_case_cls.execute)

    def test_when_inspecting_class_expect_non_empty_docstring(self, use_case_cls: type):
        assert use_case_cls.__doc__ is not None
        assert use_case_cls.__doc__.strip()
