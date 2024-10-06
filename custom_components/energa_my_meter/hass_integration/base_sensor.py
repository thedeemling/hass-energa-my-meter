"""
Base classes for Energa sensors containing most of the common logic like naming and attributes support.
"""

from homeassistant.components.sensor import ENTITY_ID_FORMAT, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from custom_components.energa_my_meter import DOMAIN
from custom_components.energa_my_meter.energa.const import ENERGA_MY_METER_DATA_URL


class EnergaBaseSensor(SensorEntity):
    """Base class for all Energa sensors containing common logic"""

    def __init__(self, entry: ConfigEntry, name_id: str, name: str):
        super().__init__()

        self._entry: ConfigEntry = entry
        self._device_info = {}
        self._attr_name = name
        self._name_id = name_id
        self._attr_name_id = name_id
        self.entity_id = ENTITY_ID_FORMAT.format(f'energa_{entry["meter_number"]}_{name_id}')

    @property
    def name_id(self) -> str:
        """Returns the name_id of the sensor. It is used for name generation."""
        return self._name_id

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def unique_id(self) -> str:
        return '_'.join([
            DOMAIN,
            str(self._entry['ppe_number']),
            str(self._entry['meter_number']),
            self.name_id
        ])

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this instance."""
        ppe_number = self._entry['ppe_number']
        meter_number = self._entry['meter_number']

        self._device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="Energa S.A.",
            sw_version='1.0.0',
            model='Energa SmartMeter',
            identifiers={(DOMAIN, ppe_number)},
            name=f'Meter {meter_number} (PPE {ppe_number})',
            configuration_url=f'{ENERGA_MY_METER_DATA_URL}?mpc={meter_number}&ppe={ppe_number}',
        )

        return self._device_info

    @callback
    def _update_callback(self):
        """Handle device update."""
        self.async_write_ha_state()


class EnergaBaseCoordinatorSensor(CoordinatorEntity, EnergaBaseSensor):
    """Base class for all sensors that only updated via the coordinator service"""

    def __init__(self, entry: ConfigEntry, name_id: str, coordinator: DataUpdateCoordinator, name: str):
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        EnergaBaseSensor.__init__(self, entry=entry, name_id=name_id, name=name)

    @property
    def native_value(self) -> float | str | None:
        """Returns the value of the sensor from the coordinator updates"""
        return self.coordinator.data.get(self._name_id) \
            if self.coordinator.data and self.coordinator.data.get(self._name_id) else None

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Entity will be disabled if it does not contain any data - perhaps it could not be gathered"""
        return self.coordinator.data is not None and self.coordinator.data.get(self._name_id) is not None

    @property
    def available(self) -> bool:
        """Entity will not be available in GUI if it does not contain any data - perhaps it could not be gathered"""
        return self.coordinator.data is not None and self.coordinator.data.get(self._name_id) is not None

    async def async_added_to_hass(self):
        """When entity is added to HASS."""
        self.async_on_remove(self.coordinator.async_add_listener(self._update_callback))
