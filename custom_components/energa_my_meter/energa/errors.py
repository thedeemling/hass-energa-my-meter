"""Module with exceptions that can occur when using Energa My Meter integration"""


class EnergaMyMeterAuthorizationError(Exception):
    """Raised when user provided invalid credentials"""


class EnergaWebsiteLoadingError(Exception):
    """Raised when there was a general error when loading Energa My Meter website"""


class EnergaNoSuitableMetersFoundError(Exception):
    """Raised when after logging into the Energa system there is no smart meter supported"""


class EnergaStatisticsCouldNotBeLoadedError(Exception):
    """Raised when Energa statistics endpoint could not return any data"""


class EnergaConnectionNotOpenedError(Exception):
    """Raised when the connection to the Energa website was not opened"""
