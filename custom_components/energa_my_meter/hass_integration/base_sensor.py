"""
Base classes for Energa sensors containing most of the common logic like naming and attributes support.
"""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from ..common import generate_entity_name
from ..const import DOMAIN, CONF_SELECTED_METER_NUMBER, CONF_PPE_NUMBER, CONF_METER_NUMBER
from ..energa.const import ENERGA_MY_METER_DATA_URL


class EnergaBaseSensor(SensorEntity):
    """Base class for all Energa sensors containing common logic"""

    def __init__(self, entry: ConfigEntry, name_id: str, name: str):
        super().__init__()

        self._entry: ConfigEntry = entry
        self._device_info = {}
        self._attr_name = name
        self._name_id = name_id
        self.entity_id = generate_entity_name(entry[CONF_SELECTED_METER_NUMBER], name_id)

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
            str(self._entry[CONF_PPE_NUMBER]),
            str(self._entry[CONF_METER_NUMBER]),
            self._name_id
        ])

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this instance."""
        ppe_number = self._entry[CONF_PPE_NUMBER]
        meter_number = self._entry[CONF_METER_NUMBER]

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
