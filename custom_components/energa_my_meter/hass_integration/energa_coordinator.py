"""
The implementation of the DataUpdateCoordinator in Home Assistant - an entity that asynchronously loads the data for
multiple types of sensors.
"""
import logging
from datetime import timedelta

from homeassistant.components.recorder.models import StatisticData
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .data_updater import EnergaDataUpdater
from ..const import CONF_SELECTED_MODES
from ..energa.client import EnergaMyMeterClient
from ..energa.data import EnergaMeterReading
from ..energa.stats_modes import EnergaStatsModes

_LOGGER = logging.getLogger(__name__)

STATISTICS_DATA_KEY_NAME = 'stats'
MAIN_DATA_KEY_NAME = 'main'


class EnergaCoordinator(DataUpdateCoordinator):
    """Coordinator class for Energa sensors - all data can be updated all at once"""

    def __init__(
            self,
            hass: HomeAssistant,
            polling_interval: int,
            entry: ConfigEntry,
    ):
        self.entry = entry
        self._skip_stats_update = False
        super().__init__(hass, _LOGGER, name="Energa My Meter", update_interval=timedelta(minutes=polling_interval))

    async def _async_update_data(self) -> dict:
        """Refreshing the data event"""
        hass_data = dict(self.entry.data)
        return await get_instance(self.hass).async_add_executor_job(
            self.refresh_data, hass_data, self.hass, self._skip_stats_update
        )

    def set_stats_skipping(self, should_skip: bool) -> None:
        """Skip stats update"""
        self._skip_stats_update = should_skip

    def get_data(self):
        """Returns the data gathered from Energa"""
        return self.data.get(MAIN_DATA_KEY_NAME, {})

    def get_statistics(self):
        """Returns the statistics about the sensors"""
        return self.data.get(STATISTICS_DATA_KEY_NAME, {})

    def get_specific_statistic(self, mode: EnergaStatsModes, zone: str) -> [StatisticData]:
        """Returns the statistics for a specific zone in a specific mode"""
        return self.data.get(STATISTICS_DATA_KEY_NAME, {}).get(mode.name, {}).get(zone, [])

    def get_meter_readings(self) -> [EnergaMeterReading]:
        """Returns a list of readings for all meters"""
        return self.get_data().meter_readings

    @staticmethod
    def refresh_data(hass_data, hass: HomeAssistant, skip_stats: bool = False) -> dict:
        """Sync task to get the data from Energa My Meter"""
        _LOGGER.info('Refreshing Energa data...')
        energa = EnergaMyMeterClient()
        updater = EnergaDataUpdater(energa, hass_data, hass)
        energa.open_connection(hass_data[CONF_USERNAME], hass_data[CONF_PASSWORD])
        main_data = updater.gather_basic_data()
        statistics = {}

        selected_modes = hass_data[CONF_SELECTED_MODES]
        if not skip_stats:
            for mode in selected_modes:
                statistics[mode] = updater.gather_stats(EnergaStatsModes[mode])

        energa.disconnect()
        return {
            MAIN_DATA_KEY_NAME: main_data,
            STATISTICS_DATA_KEY_NAME: statistics
        }
