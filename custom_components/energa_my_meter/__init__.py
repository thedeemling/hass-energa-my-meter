"""
Energa My Meter custom component initialization.
Written using knowledge from docs: https://developers.home-assistant.io/
"""
from datetime import timedelta
import logging

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, PlatformNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import voluptuous as vol

from custom_components.energa_my_meter.common import async_config_entry_by_username
from custom_components.energa_my_meter.const import DEFAULT_SCAN_INTERVAL, DOMAIN
from custom_components.energa_my_meter.energa.client import EnergaData, EnergaMyMeterClient
from custom_components.energa_my_meter.energa.errors import EnergaMyCounterAuthorizationError, EnergaWebsiteLoadingError

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: [vol.Any(
    vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    })
)]}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the component from YAML configuration."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    for energa_config in config.get(DOMAIN, []):
        already_configured: ConfigEntry = async_config_entry_by_username(hass, energa_config[CONF_USERNAME])
        if already_configured:
            _LOGGER.debug('The config entry is already configured: {%s}. Updating it...', already_configured.title)
            data = {CONF_USERNAME: energa_config[CONF_USERNAME], CONF_PASSWORD: energa_config[CONF_PASSWORD]}
            options = {CONF_SCAN_INTERVAL: energa_config[CONF_SCAN_INTERVAL]}
            hass.config_entries.async_update_entry(already_configured, data=data, options=options)
        else:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}, data=energa_config
                )
            )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)

    polling_interval = entry.options.get('scan_interval') or DEFAULT_SCAN_INTERVAL

    try:
        coordinator = EnergaMyCounterUpdater(hass, polling_interval=polling_interval, entry=entry)
        await coordinator.async_refresh()
    except EnergaWebsiteLoadingError as error:
        _LOGGER.debug("Energa loading error: {%s}", error)
        raise PlatformNotReady from error
    except EnergaMyCounterAuthorizationError as error:
        _LOGGER.debug("Could not log into Energa My Meter: {%s}", error)
        raise ConfigEntryNotReady from error

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass_data["unsub_options_update_listener"] = entry.add_update_listener(options_update_listener)
    hass_data['ppe_number'] = coordinator.data['ppe_number']
    hass_data['meter_number'] = coordinator.data['meter_number']

    hass.data[DOMAIN][entry.entry_id] = hass_data
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "sensor"))

    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class EnergaMyCounterUpdater(DataUpdateCoordinator):
    """Coordinator class for Energa sensors - all data can be updated all at once"""

    def __init__(
            self,
            hass: HomeAssistant,
            polling_interval: int,
            entry: ConfigEntry,
    ):
        self.entry = entry
        self.energa = EnergaMyMeterClient(hass)
        super().__init__(hass, _LOGGER, name="Energa My Meter", update_interval=timedelta(minutes=polling_interval))

    async def _async_update_data(self) -> EnergaData:
        """Refreshing the data event"""
        hass_data = dict(self.entry.data)
        return await self.energa.gather_data(hass_data[CONF_USERNAME], hass_data[CONF_PASSWORD])
