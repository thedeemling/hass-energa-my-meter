"""
Base classes for Energa sensors containing most of the common logic like naming and attributes support.
"""
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass, ENTITY_ID_FORMAT
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfEnergy
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.energa_my_meter.hass_integration.energa_entity import EnergaSensorEntity


class EnergaEnergyBaseSensor(EnergaSensorEntity):
    """
    Base class for sensors containing energy values.
    Configures Home Assistant metadata for the Energy dashboard integration
    """

    def __init__(self, entry: ConfigEntry, name_id: str, coordinator: DataUpdateCoordinator, name):
        super().__init__(entry=entry, coordinator=coordinator)

        self._attr_name = name
        self._name_id = name_id
        self._attr_name_id = name_id
        self.entity_id = ENTITY_ID_FORMAT.format(f'energa_{entry["meter_number"]}_{name_id}')

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    @property
    def name_id(self) -> str:
        """Returns the name_id of the sensor. It is used for name generation."""
        return self._name_id

    @property
    def native_value(self) -> float:
        """Returns the value of the sensor from the coordinator updates"""
        value = self.coordinator.data[self._name_id] if self.coordinator.data else None
        return float(value) if value else None

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Entity will be disabled if it does not contain any data - perhaps it could not be gathered"""
        return self.coordinator.data[self._name_id] is not None

    @property
    def available(self) -> bool:
        """Entity will be available in GUI if it does not contain any data - perhaps it could not be gathered"""
        return self.coordinator.data[self._name_id] is not None


class EnergaAdditionalDataBaseSensor(EnergaSensorEntity):
    """Base class for diagnostic type sensors not related with the Energy Dashboard"""

    def __init__(self, entry: ConfigEntry, name_id: str, coordinator: DataUpdateCoordinator, name):
        super().__init__(entry=entry, coordinator=coordinator)

        self._attr_name = name
        self._name_id = name_id
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self.entity_id = f'sensor.energa_{entry["meter_number"]}_{name_id}'

    @property
    def native_value(self):
        """Returns the value of the sensor from the coordinator updates"""
        return self.coordinator.data[self._name_id] if self.coordinator.data else None
