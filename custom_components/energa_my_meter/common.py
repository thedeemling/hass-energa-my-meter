"""
Common helpers for Energa my Meter integration
"""

from __future__ import annotations

import re

import unicodedata
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.const import CONF_USERNAME
from homeassistant.core import callback

from .const import DOMAIN, CONF_SELECTED_METER_NUMBER
from .energa.stats_modes import EnergaStatsModes


@callback
def async_config_entry_by_username(hass, username, meter_number):
    """Look up config entry by device id."""
    current_entries = hass.config_entries.async_entries(DOMAIN)
    for entry in current_entries:
        if entry.data.get(CONF_USERNAME) == username and entry.data.get(CONF_SELECTED_METER_NUMBER) == meter_number:
            return entry
    return None


def normalize_entity_string(string: str) -> str:
    """Ensures the string contain characters valid for Home Assistant"""
    normalized: str = unicodedata.normalize('NFKD', string.lower().replace("ł", "l").replace(':', ''))
    slug = re.sub("[^a-z0-9]", "_", normalized)  # remove any invalid character
    slug = re.sub("_+", "_", slug)  # remove any duplicated_
    slug = re.sub("_+$", "", slug)  # remove any finishing _
    return slug


def get_zone_display_name(zone: str) -> str:
    """Normalizes zone name to be displayed in Home Assistant"""
    return zone.replace(":", "")


def generate_entity_name(meter_number: str | int, name_suffix: str) -> str:
    """Returns the entity name for the component"""
    return ENTITY_ID_FORMAT.format(f'{DOMAIN}_{meter_number}_{name_suffix}')


def generate_stats_base_entity_name(mode: EnergaStatsModes, zone: str) -> str:
    """Returns the entity name for the statistics sensor"""
    if mode == EnergaStatsModes.ENERGY_CONSUMED:
        stat_name = 'consumed'
    elif mode == EnergaStatsModes.ENERGY_PRODUCED:
        stat_name = 'produced'
    else:
        stat_name = 'summary'
    normalized_zone = normalize_entity_string(zone)
    return f'{stat_name}_{normalized_zone}'


def generate_stats_display_name(mode: EnergaStatsModes, zone: str) -> str:
    """Returns the display name for the statistics sensor"""
    if mode == EnergaStatsModes.ENERGY_CONSUMED:
        stat_name = 'Energy consumed'
    elif mode == EnergaStatsModes.ENERGY_PRODUCED:
        stat_name = 'Energy produced'
    else:
        stat_name = 'Energy summary'
    normalized_zone = get_zone_display_name(zone)
    return f'{stat_name} - {normalized_zone}'
