"""Expected infrastructure failures emitted by the Xray Viewer adapter."""


class XrayProviderError(Exception):
    """Base class for expected failures while communicating with Xray."""


class XrayAuthenticationError(XrayProviderError):
    """Xray authentication did not produce a usable access token."""


class XrayProtocolError(XrayProviderError):
    """Xray returned a response outside the supported provider contract."""


class XrayTransportError(XrayProviderError):
    """Xray could not be reached or returned an unsuccessful HTTP response."""
