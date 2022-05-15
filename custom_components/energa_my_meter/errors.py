"""
Custom component's specific errors/exceptions for Home Assistant integration
"""

from homeassistant.exceptions import HomeAssistantError


class EnergaMyCounterAuthorizationError(HomeAssistantError):
    """Raised when user provided invalid credentials"""


class EnergaWebsiteLoadingError(HomeAssistantError):
    """Raised when there was a general error when loading Energa My Meter website"""


class EnergaNoSuitableCountersFoundError(HomeAssistantError):
    """Raised when after logging into the Energa system there is no smart counter supported"""


class EnergaHistoricalDataGatheringError(HomeAssistantError):
    """Raised when there is an error when getting the historical data from Energa My Meter website"""
