"""
Energa My Meter custom component initialization.
Written using knowledge from docs: https://developers.home-assistant.io/
"""
import logging

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, PlatformNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .common import async_config_entry_by_username
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, CONF_SELECTED_METER_ID, \
    CONF_SELECTED_METER_NUMBER, CONF_SELECTED_ZONES, CONF_SELECTED_MODES, \
    CONF_NUMBER_OF_DAYS_TO_LOAD, PREVIOUS_DAYS_NUMBER_TO_BE_LOADED, CONF_SELECTED_METER_PPE, CONF_SELECTED_METER_NAME
from .energa.errors import EnergaMyMeterAuthorizationError, EnergaWebsiteLoadingError
from .hass_integration.energa_coordinator import EnergaCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: [vol.Any(
    vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_SELECTED_METER_ID): cv.positive_int,
        vol.Required(CONF_SELECTED_METER_NUMBER): cv.positive_int,
        vol.Required(CONF_SELECTED_ZONES): cv.ensure_list(cv.string),
        vol.Optional(CONF_SELECTED_METER_PPE): cv.positive_int,
        vol.Optional(CONF_SELECTED_MODES, default=["ENERGY_CONSUMED"]): cv.ensure_list(cv.string),
        vol.Optional(CONF_NUMBER_OF_DAYS_TO_LOAD, default=PREVIOUS_DAYS_NUMBER_TO_BE_LOADED): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    })
)]}, extra=vol.ALLOW_EXTRA)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the component from YAML configuration."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    for energa_config in config.get(DOMAIN, []):
        already_configured: ConfigEntry = async_config_entry_by_username(hass, energa_config[CONF_USERNAME],
                                                                         energa_config[CONF_SELECTED_METER_NUMBER])
        if already_configured:
            _LOGGER.debug('The config entry is already configured: {%s}. Updating it...', already_configured.title)
            data = {
                CONF_USERNAME: energa_config.get(CONF_USERNAME),
                CONF_PASSWORD: energa_config.get(CONF_PASSWORD),
                CONF_SELECTED_METER_NUMBER: energa_config.get(CONF_SELECTED_METER_NUMBER),
                CONF_SELECTED_METER_ID: energa_config.get(CONF_SELECTED_METER_ID),
                CONF_SELECTED_ZONES: energa_config.get(CONF_SELECTED_ZONES),
                CONF_SELECTED_MODES: energa_config.get(CONF_SELECTED_MODES),
                CONF_SELECTED_METER_PPE: energa_config.get(CONF_SELECTED_METER_PPE),
                CONF_NUMBER_OF_DAYS_TO_LOAD: energa_config.get(CONF_NUMBER_OF_DAYS_TO_LOAD),
            }
            options = {CONF_SCAN_INTERVAL: energa_config.get(CONF_SCAN_INTERVAL)}
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

    polling_interval = entry.options.get(CONF_SCAN_INTERVAL) or DEFAULT_SCAN_INTERVAL

    try:
        coordinator = EnergaCoordinator(hass, polling_interval=polling_interval, entry=entry)
        coordinator.set_stats_skipping(True)
        await coordinator.async_refresh()
        coordinator.set_stats_skipping(False)
    except EnergaWebsiteLoadingError as error:
        _LOGGER.debug("Energa loading error: {%s}", error)
        raise PlatformNotReady from error
    except EnergaMyMeterAuthorizationError as error:
        _LOGGER.warning("Could not log into Energa My Meter: {%s}", error)
        raise ConfigEntryNotReady from error

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass_data["unsub_options_update_listener"] = entry.add_update_listener(options_update_listener)
    hass_data[CONF_SELECTED_METER_NAME] = coordinator.get_data().get('meter_name')
    if not hass_data.get(CONF_SELECTED_METER_PPE):
        hass_data[CONF_SELECTED_METER_PPE] = coordinator.get_data().get('ppe_number')

    hass.data[DOMAIN][entry.entry_id] = hass_data
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    await hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )
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
