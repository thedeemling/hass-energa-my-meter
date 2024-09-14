"""All sensor types configured by the integration in Home Assistant instance"""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hass_integration.live_sensors import EnergaEnergyUsedSensor, EnergaEnergyProducedSensor, EnergaTariffSensor, \
    EnergaPPEAddressSensor, EnergaContractPeriodSensor, EnergaClientTypeSensor, EnergaSellerSensor, \
    EnergaMeterInternalIdSensor, EnergaMeterUsedEnergyLastUpdate
from .hass_integration.statistics_sensor import EnergyConsumedStatisticsSensor

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
    return [
        EnergaEnergyUsedSensor(entry=config, coordinator=config['coordinator']),
        EnergaEnergyProducedSensor(entry=config, coordinator=config['coordinator']),
        EnergaTariffSensor(entry=config, coordinator=config['coordinator']),
        EnergaPPEAddressSensor(entry=config, coordinator=config['coordinator']),
        EnergaContractPeriodSensor(entry=config, coordinator=config['coordinator']),
        EnergaClientTypeSensor(entry=config, coordinator=config['coordinator']),
        EnergaSellerSensor(entry=config, coordinator=config['coordinator']),
        EnergaMeterInternalIdSensor(entry=config, coordinator=config['coordinator']),
        EnergaMeterUsedEnergyLastUpdate(entry=config, coordinator=config['coordinator'])
    ]


def get_statistics_sensors(config: ConfigEntry) -> list[SensorEntity]:
    """
    Prepares the list of statistics sensors that cannot be refreshed via the coordinator
    """
    return [
        EnergyConsumedStatisticsSensor(entry=config),
    ]
