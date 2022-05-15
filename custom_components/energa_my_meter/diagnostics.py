"""
Adding support for the Home Assistant's diagnostics feature
"""

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

TO_REDACT = {CONF_USERNAME, CONF_PASSWORD}


async def async_get_config_entry_diagnostics(
        hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    return _async_get_diagnostics(hass, entry)


async def async_get_device_diagnostics(
        hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict:
    """Return diagnostics for a device entry."""
    return _async_get_diagnostics(hass, entry, device)


@callback
# pylint: disable=unused-argument
def _async_get_diagnostics(
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: DeviceEntry = None,
) -> dict:
    """Return diagnostics for a config or a device entry."""
    diagnostics = {"entry": async_redact_data(entry.as_dict(), TO_REDACT)}

    if device:
        diagnostics['device'] = device

    return diagnostics
