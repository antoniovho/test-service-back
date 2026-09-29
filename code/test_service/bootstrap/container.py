"""Application-wide opyoid injector.

`DomainModule` binds use case ports to their implementations and
`InfrastructureModule` binds their outbound adapters. `opyoid.Injector` eagerly
builds every registered binding, so the injector is constructed lazily when a
controller first requires it.
"""

from opyoid import Injector

from test_service.domain.domain_module import DomainModule
from test_service.infrastructure.infrastructure_module import InfrastructureModule

_injector: Injector | None = None


def get_injector() -> Injector:
    """Return the process-wide opyoid injector, building it on first use."""
    global _injector
    if _injector is None:
        _injector = Injector([DomainModule, InfrastructureModule])
    return _injector
