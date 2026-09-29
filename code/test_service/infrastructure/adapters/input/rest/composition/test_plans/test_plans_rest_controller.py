"""Feature controller boundary for Test Plan composition operations."""


class TestPlansRestController:
    """Reserve the Test Plan REST boundary until its use cases are implemented."""

    @staticmethod
    def _not_implemented() -> None:
        raise NotImplementedError("Test Plan composition operations are not implemented yet.")

    async def create(self, *args, **kwargs):
        self._not_implemented()

    async def get(self, *args, **kwargs):
        self._not_implemented()

    async def create_version(self, *args, **kwargs):
        self._not_implemented()

    async def activate(self, *args, **kwargs):
        self._not_implemented()

    async def deprecate(self, *args, **kwargs):
        self._not_implemented()

    async def list(self, *args, **kwargs):
        self._not_implemented()

    async def list_versions(self, *args, **kwargs):
        self._not_implemented()
