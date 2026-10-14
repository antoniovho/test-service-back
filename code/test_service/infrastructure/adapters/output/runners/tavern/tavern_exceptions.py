"""Expected infrastructure failures emitted by the Tavern runner."""


class TavernResultInvalidError(ValueError):
    """Raised when Tavern's subprocess report is malformed or incomplete."""
