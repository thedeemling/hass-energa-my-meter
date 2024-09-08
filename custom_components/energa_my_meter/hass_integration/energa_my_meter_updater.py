import logging
from datetime import timedelta, datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.energa_my_meter.const import CONFIG_FLOW_SELECTED_METER_NUMBER, CONFIG_FLOW_SELECTED_METER_ID
from custom_components.energa_my_meter.energa.client import EnergaData, EnergaMyMeterClient
from custom_components.energa_my_meter.energa.data import EnergaStatisticsData

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
        _LOGGER.debug('Refreshing Energa data...')
        hass_data = dict(self.entry.data)
        energa = await self.create_new_connection()
        return await energa.get_account_main_data(hass_data[CONFIG_FLOW_SELECTED_METER_NUMBER],
                                                  hass_data[CONFIG_FLOW_SELECTED_METER_ID])

    async def load_statistics(self, starting_point: datetime, energa: EnergaMyMeterClient) -> EnergaStatisticsData:
        hass_data = dict(self.entry.data)
        return await energa.get_statistics(hass_data[CONFIG_FLOW_SELECTED_METER_ID], starting_point)

    async def create_new_connection(self):
        hass_data = dict(self.entry.data)
        energa = EnergaMyMeterClient(self.hass)
        await energa.open_connection(hass_data[CONF_USERNAME], hass_data[CONF_PASSWORD])
        return energa
