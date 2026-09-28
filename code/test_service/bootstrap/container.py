"""Application-wide opyoid injector.

`DomainModule` binds use case ports to their implementations. Outbound ports
(e.g. `ProjectRepositoryPort`) have no persistence adapter bound yet — that
wiring is a separate task. `opyoid.Injector` eagerly builds every registered
binding as soon as it is constructed, so the injector is built lazily on first
use: until a persistence adapter is bound, the first call to `get_injector()`
(made when a controller is instantiated per request) raises
`opyoid.exceptions.NonInjectableTypeError` for any use case that depends on an
unbound port, instead of failing at import/app-startup time.
"""

from opyoid import Injector

from test_service.domain.domain_module import DomainModule

_injector: Injector | None = None


def get_injector() -> Injector:
    """Return the process-wide opyoid injector, building it on first use."""
    global _injector
    if _injector is None:
        _injector = Injector([DomainModule])
    return _injector
