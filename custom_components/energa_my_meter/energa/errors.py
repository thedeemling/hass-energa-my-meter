"""Module with exceptions that can occur when using Energa My Meter integration"""


class EnergaMyCounterAuthorizationError(Exception):
    """Raised when user provided invalid credentials"""


class EnergaWebsiteLoadingError(Exception):
    """Raised when there was a general error when loading Energa My Meter website"""


class EnergaNoSuitableCountersFoundError(Exception):
    """Raised when after logging into the Energa system there is no smart counter supported"""
