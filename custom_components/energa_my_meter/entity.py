"""
Base configuration for the Energa My meter sensors
"""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN
from .energa.const import ENERGA_MY_METER_DATA_URL


class EnergaSensorEntity(CoordinatorEntity, SensorEntity):
    """Base class for all Energa My meter sensors"""

    def __init__(
            self,
            entry: ConfigEntry,
            coordinator: DataUpdateCoordinator
    ):
        self._entry: ConfigEntry = entry
        self._counter_data = {}
        self._device_info = {}
        super().__init__(coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def name_id(self) -> str:
        """The name_id parameter to be overwritten by classes"""
        return ''

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
            model='Energa SmartCounter',
            identifiers={(DOMAIN, ppe_number, meter_number)},
            name=f'Meter {meter_number} (PPE {ppe_number})',
            configuration_url=f'{ENERGA_MY_METER_DATA_URL}?mpc={meter_number}&ppe={ppe_number}',
        )

        return self._device_info

    async def async_added_to_hass(self):
        """When entity is added to HASS."""
        self.async_on_remove(self.coordinator.async_add_listener(self._update_callback))

    @callback
    def _update_callback(self):
        """Handle device update."""
        self.async_write_ha_state()
