"""Module with exceptions that can occur when using Energa My Meter integration"""


class EnergaClientError(Exception):
    """Base class for exceptions in this module."""


class EnergaMyMeterCaptchaRequirementError(EnergaClientError):
    """Raised when the user is supposed to confirm his login with captcha"""


class EnergaMyMeterWebsiteError(EnergaClientError):
    """Raised when the website is suffering from an error"""


class EnergaMyMeterAuthorizationError(EnergaClientError):
    """Raised when user provided invalid credentials"""


class EnergaWebsiteLoadingError(EnergaClientError):
    """Raised when there was a general error when loading Energa My Meter website"""


class EnergaNoSuitableMetersFoundError(EnergaClientError):
    """Raised when after logging into the Energa system there is no smart meter supported"""


class EnergaStatisticsCouldNotBeLoadedError(EnergaClientError):
    """Raised when Energa statistics endpoint could not return any data"""


class EnergaConnectionNotOpenedError(EnergaClientError):
    """Raised when the connection to the Energa website was not opened"""
