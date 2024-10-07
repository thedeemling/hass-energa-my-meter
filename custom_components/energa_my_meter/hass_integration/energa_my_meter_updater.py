"""
The implementation of the DataUpdateCoordinator in Home Assistant - an entity that asynchronously loads the data for
multiple types of sensors.
"""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..const import CONFIG_FLOW_SELECTED_METER_NUMBER, CONFIG_FLOW_SELECTED_METER_ID
from ..energa.client import EnergaData, EnergaMyMeterClient

_LOGGER = logging.getLogger(__name__)


class EnergaMyMeterUpdater(DataUpdateCoordinator):
    """Coordinator class for Energa sensors - all data can be updated all at once"""

    def __init__(
            self,
            hass: HomeAssistant,
            polling_interval: int,
            entry: ConfigEntry,
    ):
        self.entry = entry
        super().__init__(hass, _LOGGER, name="Energa My Meter", update_interval=timedelta(minutes=polling_interval))

    async def _async_update_data(self) -> EnergaData:
        """Refreshing the data event"""
        hass_data = dict(self.entry.data)
        return await self.hass.async_add_executor_job(self._refresh_data, hass_data)

    def get_data(self):
        """Returns the data gathered from Energa"""
        return self.data

    @staticmethod
    def _refresh_data(hass_data) -> EnergaData:
        """Sync task to get the data from Energa My Meter"""
        _LOGGER.debug('Refreshing Energa data...')
        energa = EnergaMyMeterClient()
        energa.open_connection(hass_data[CONF_USERNAME], hass_data[CONF_PASSWORD])
        result = energa.get_account_main_data(hass_data[CONFIG_FLOW_SELECTED_METER_NUMBER],
                                              hass_data[CONFIG_FLOW_SELECTED_METER_ID])
        energa.disconnect()
        return result
