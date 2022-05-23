"""
Common helpers for Energa my Meter integration
"""

from __future__ import annotations

from homeassistant.const import CONF_USERNAME
from homeassistant.core import callback

from .const import DOMAIN


@callback
def async_config_entry_by_username(hass, username):
    """Look up config entry by device id."""
    current_entries = hass.config_entries.async_entries(DOMAIN)
    for entry in current_entries:
        if entry.data[CONF_USERNAME] == username:
            return entry
    return None
