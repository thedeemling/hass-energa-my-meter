"""All sensor types configured by the integration in Home Assistant instance"""

import logging
from typing import Callable

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import (
    HomeAssistantType,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN
)
from .entity import EnergaSensorEntity

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

    sensors: list[SensorEntity] = [
        EnergaEnergyUsedSensor(entry=config, coordinator=config['coordinator']),
        EnergaEnergyProducedSensor(entry=config, coordinator=config['coordinator']),
        EnergaTariffSensor(entry=config, coordinator=config['coordinator']),
        EnergaPPEAddressSensor(entry=config, coordinator=config['coordinator']),
        EnergaContractPeriodSensor(entry=config, coordinator=config['coordinator']),
        EnergaClientTypeSensor(entry=config, coordinator=config['coordinator']),
        EnergaSellerSensor(entry=config, coordinator=config['coordinator']),
        EnergaCounterInternalIdSensor(entry=config, coordinator=config['coordinator']),
        EnergaCounterUsedEnergyLastUpdate(entry=config, coordinator=config['coordinator']),
    ]

    async_add_entities(sensors, update_before_add=True)


async def async_setup_platform(
        hass: HomeAssistantType,
        config_entry: ConfigEntry,
        async_add_entities: Callable,
) -> None:
    """Set up the sensor platform."""

    config = hass.data[DOMAIN][config_entry.entry_id]

    if config_entry.options:
        config.update(config_entry.options)

    _LOGGER.info('Setting up platform sensors for Energa My Meter integration {%s}...', config_entry.title)

    sensors: list[SensorEntity] = [
        EnergaEnergyUsedSensor(entry=config, coordinator=config['coordinator']),
        EnergaEnergyProducedSensor(entry=config, coordinator=config['coordinator']),
        EnergaTariffSensor(entry=config, coordinator=config['coordinator']),
        EnergaPPEAddressSensor(entry=config, coordinator=config['coordinator']),
        EnergaContractPeriodSensor(entry=config, coordinator=config['coordinator']),
        EnergaClientTypeSensor(entry=config, coordinator=config['coordinator']),
        EnergaSellerSensor(entry=config, coordinator=config['coordinator']),
        EnergaCounterInternalIdSensor(entry=config, coordinator=config['coordinator']),
        EnergaCounterUsedEnergyLastUpdate(entry=config, coordinator=config['coordinator']),
    ]

    async_add_entities(sensors, update_before_add=True)


class EnergaEnergySensor(EnergaSensorEntity):
    """
    Base class for sensors containing energy values.
    Configures Home Assistant metadata for the Energy dashboard integration
    """
    def __init__(self, entry: ConfigEntry, name_id: str, coordinator: DataUpdateCoordinator, name):
        self._attr_name = name
        self._name_id = name_id
        self._attr_name_id = name_id

        self._attr_device_class = 'energy'
        self._attr_state_class = 'total_increasing'
        self._attr_native_unit_of_measurement = 'kWh'

        super().__init__(entry=entry, coordinator=coordinator)

    @property
    def name_id(self) -> str:
        """Returns the name_id of the sensor. It is used for name generation."""
        return self._name_id

    @property
    def native_value(self) -> float:
        """Returns the value of the sensor from the coordinator updates"""
        return float(self.coordinator.data[self._name_id]) if self.coordinator.data else None

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Entity will be disabled if it does not contain any data - perhaps it could not be gathered"""
        return self.coordinator.data[self._name_id] is not None

    @property
    def available(self) -> bool:
        """Entity will be available in GUI if it does not contain any data - perhaps it could not be gathered"""
        return self.coordinator.data[self._name_id] is not None


class EnergaAdditionalDataSensor(EnergaSensorEntity):
    """Base class for diagnostic type sensors not related with the Energy Dashboard"""
    def __init__(self, entry: ConfigEntry, field_id: str, coordinator: DataUpdateCoordinator, name):
        self._attr_name = name
        self._name_id = field_id
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

        super().__init__(entry=entry, coordinator=coordinator)

    @property
    def name_id(self):
        """Returns the name_id of the sensor. It is used for name generation."""
        return self._name_id

    @property
    def native_value(self):
        """Returns the value of the sensor from the coordinator updates"""
        return self.coordinator.data[self._name_id] if self.coordinator.data else None


class EnergaEnergyUsedSensor(EnergaEnergySensor):
    """Energy used sensor with support for the Energy dashboard"""
    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:lightning-bolt'
        super().__init__(entry=entry, name_id='energy_used', coordinator=coordinator,
                         name=f'Energy used ({entry["meter_number"]})')


class EnergaEnergyProducedSensor(EnergaEnergySensor):
    """Energy produced sensor with support for the Energy dashboard"""
    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:home-battery'
        super().__init__(entry=entry, name_id='energy_produced', coordinator=coordinator,
                         name=f'Energy produced ({entry["meter_number"]})')


class EnergaTariffSensor(EnergaAdditionalDataSensor):
    """Meters currently associated tariff sensor"""
    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:camera-burst'
        super().__init__(entry=entry, field_id='tariff', coordinator=coordinator,
                         name=f'Tariff ({entry["meter_number"]})')


class EnergaPPEAddressSensor(EnergaAdditionalDataSensor):
    """The address of the PPE sensor"""
    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:map-marker'
        super().__init__(entry=entry, field_id='ppe_address', coordinator=coordinator,
                         name=f'PPE address ({entry["meter_number"]})')


class EnergaContractPeriodSensor(EnergaAdditionalDataSensor):
    """The string representation of the user's contract period sensor"""
    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:calendar-range'
        super().__init__(entry=entry, field_id='contract_period', coordinator=coordinator,
                         name=f'Contract period ({entry["meter_number"]})')


class EnergaClientTypeSensor(EnergaAdditionalDataSensor):
    """The client type sensor"""
    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:account-box-multiple'
        super().__init__(entry=entry, field_id='client_type', coordinator=coordinator,
                         name=f'Client type ({entry["meter_number"]})')


class EnergaSellerSensor(EnergaAdditionalDataSensor):
    """The name of the seller sensor"""
    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:account-box-multiple'
        super().__init__(entry=entry, field_id='seller', coordinator=coordinator,
                         name=f'Seller ({entry["meter_number"]})')


class EnergaCounterInternalIdSensor(EnergaAdditionalDataSensor):
    """The meter's internal ID sensor. It is used in internal Energa calls."""
    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:counter'
        super().__init__(entry=entry, field_id='meter_id', coordinator=coordinator,
                         name=f'Counter ID ({entry["meter_number"]})')


class EnergaCounterUsedEnergyLastUpdate(EnergaAdditionalDataSensor):
    """The date of the last update on the Energa website sensor"""
    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:update'
        super().__init__(entry=entry, field_id='energy_used_last_update', coordinator=coordinator,
                         name=f'Last update ({entry["meter_number"]})')
