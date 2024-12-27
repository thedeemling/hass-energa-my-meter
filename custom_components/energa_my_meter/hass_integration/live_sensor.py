"""Module containing the base logic for all live sensors"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.energa_my_meter import EnergaCoordinator
from custom_components.energa_my_meter.energa.data import EnergaData
from custom_components.energa_my_meter.hass_integration.base_sensor import EnergaBaseSensor


class EnergaLiveSensor(CoordinatorEntity, EnergaBaseSensor):
    """Base class for all sensors that only updated via the coordinator service"""

    def __init__(self, entry: ConfigEntry, name_id: str, coordinator: EnergaCoordinator, name: str):
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        EnergaBaseSensor.__init__(self, entry=entry, name_id=name_id, name=name)

    def _get_data_from_coordinator(self, prop_key: str, def_value=None):
        """A simple wrapper to avoid null errors when getting the data from the coordinator"""
        data: EnergaData = self.coordinator.get_data()
        return data.get(prop_key, def_value)

    @property
    def native_value(self) -> float | str | None:
        """Returns the value of the sensor from the coordinator updates"""
        return self._get_data_from_coordinator(self._name_id)

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Entity will be disabled if it does not contain any data - perhaps it could not be gathered"""
        return self._get_data_from_coordinator(self._name_id) is not None

    @property
    def available(self) -> bool:
        """Entity will not be available in GUI if it does not contain any data - perhaps it could not be gathered"""
        return self._get_data_from_coordinator(self._name_id) is not None

    async def async_added_to_hass(self):
        """When entity is added to HASS."""
        self.async_on_remove(self.coordinator.async_add_listener(self._update_callback))
