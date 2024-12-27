"""All sensor types configured by the integration in Home Assistant instance"""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_SELECTED_ZONES, CONF_SELECTED_MODES
from .energa.stats_modes import EnergaStatsModes
from .hass_integration.live_sensors import EnergaTariffSensor, \
    EnergaPPEAddressSensor, EnergaContractPeriodSensor, EnergaClientTypeSensor, EnergaSellerSensor, \
    EnergaMeterReadingSensor
from .hass_integration.statistics_sensor import EnergyStatisticsSensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]

    if config_entry.options:
        config.update(config_entry.options)

    _LOGGER.info('Setting up entry sensors for Energa My Meter integration {%s}...', config_entry.title)

    live_sensors = get_live_sensors(config)
    stats_sensors = get_statistics_sensors(config)
    async_add_entities(live_sensors, update_before_add=True)
    async_add_entities(stats_sensors, update_before_add=True)


async def async_setup_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    config = hass.data[DOMAIN][config_entry.entry_id]

    if config_entry.options:
        config.update(config_entry.options)

    _LOGGER.info('Setting up platform sensors for Energa My Meter integration {%s}...', config_entry.title)

    live_sensors = get_live_sensors(config)
    stats_sensors = get_statistics_sensors(config)
    async_add_entities(live_sensors, update_before_add=True)
    async_add_entities(stats_sensors, update_before_add=True)


def get_live_sensors(config: ConfigEntry) -> list[SensorEntity]:
    """
    Prepares the list of live sensors exposed by this integration that should be refreshed via the coordinator
    """
    coordinator = config['coordinator']
    result = [
        EnergaTariffSensor(entry=config, coordinator=coordinator),
        EnergaPPEAddressSensor(entry=config, coordinator=coordinator),
        EnergaContractPeriodSensor(entry=config, coordinator=coordinator),
        EnergaClientTypeSensor(entry=config, coordinator=coordinator),
        EnergaSellerSensor(entry=config, coordinator=coordinator),
    ]
    if coordinator.get_data() and coordinator.get_data().get('meter_readings'):
        _LOGGER.debug('Adding %s meter readings as sensors...', len(coordinator.get_data().get('meter_readings')))
        for reading in coordinator.get_data().get('meter_readings'):
            result.append(
                EnergaMeterReadingSensor(entry=config, coordinator=coordinator, reading_name=reading.meter_name)
            )

    return result


def get_statistics_sensors(config: ConfigEntry) -> list[SensorEntity]:
    """
    Prepares the list of statistics sensors that cannot be refreshed via the coordinator
    """
    result = []
    selected_modes = config.get(CONF_SELECTED_MODES, [])
    selected_zones = config.get(CONF_SELECTED_ZONES, [])

    for zone in selected_zones:
        if EnergaStatsModes.ENERGY_CONSUMED.name in selected_modes:
            result.append(EnergyStatisticsSensor(
                entry=config, zone=zone, mode=EnergaStatsModes.ENERGY_CONSUMED,
                coordinator=config['coordinator'])
            )
        if EnergaStatsModes.ENERGY_PRODUCED.name in selected_modes:
            result.append(EnergyStatisticsSensor(
                entry=config, zone=zone, mode=EnergaStatsModes.ENERGY_PRODUCED,
                coordinator=config['coordinator'])
            )

    return result
