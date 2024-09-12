"""
The implementation of the DataUpdateCoordinator in Home Assistant - an entity that asynchronously loads the data for
multiple types of sensors.
"""
import logging
from datetime import timedelta, datetime

from homeassistant.components.recorder.models import StatisticData
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from custom_components.energa_my_meter.const import CONFIG_FLOW_SELECTED_METER_NUMBER, CONFIG_FLOW_SELECTED_METER_ID, \
    DEBUGGING_DATE_FORMAT, MAXIMUM_DAYS_TO_BE_LOADED_AT_ONCE
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
        return await self.hass.async_add_executor_job(self._refresh_data)

    def load_statistics(self, starting_point: datetime, finishing_point: datetime,
                        last_inserted_stat_date: datetime, total_usage: float) -> list:
        """Connects to Energa website, loads statistical data and returns it in a format suitable for Home Assistant"""
        hass_data = dict(self.entry.data)
        statistics = []
        last_statistic_date = starting_point
        current_day = starting_point
        energa: EnergaMyMeterClient = self._create_new_connection()
        _LOGGER.debug(
            'Will load statistics from %s to %s (last loaded stat is %s (%s))...',
            starting_point.strftime(DEBUGGING_DATE_FORMAT),
            finishing_point.strftime(DEBUGGING_DATE_FORMAT),
            last_inserted_stat_date.strftime(DEBUGGING_DATE_FORMAT) if last_inserted_stat_date else None,
            total_usage
        )
        loaded_days = 0
        while current_day.timestamp() <= finishing_point.timestamp() and loaded_days < MAXIMUM_DAYS_TO_BE_LOADED_AT_ONCE:
            _LOGGER.debug('Loading the statistics for the meter %s from %s',
                          hass_data[CONFIG_FLOW_SELECTED_METER_NUMBER],
                          current_day.strftime(DEBUGGING_DATE_FORMAT))
            historical_data: EnergaStatisticsData = energa.get_statistics(
                hass_data[CONFIG_FLOW_SELECTED_METER_ID],
                current_day
            )
            timezone = dt_util.get_time_zone(historical_data.timezone)
            last_updated_compare = last_inserted_stat_date.astimezone(timezone) if last_inserted_stat_date else None

            if len(historical_data.historical_points) == 0:
                _LOGGER.debug('No statistics in %s. Skipping the day...',
                              current_day.strftime(DEBUGGING_DATE_FORMAT))
                current_day = current_day + timedelta(days=1)
            else:
                for point in historical_data.historical_points:
                    statistic, statistic_date, statistic_value, should_save = self._convert_to_statistic(
                        point, timezone, last_updated_compare, total_usage
                    )
                    last_statistic_date = statistic_date
                    if should_save:
                        total_usage += statistic_value
                        statistics.append(statistic)

                current_day = (last_statistic_date
                               .replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
                loaded_days += 1

        energa.disconnect()
        return statistics

    def _create_new_connection(self):
        """Initializes a new Energa instance connection"""
        hass_data = dict(self.entry.data)
        energa = EnergaMyMeterClient()
        energa.open_connection(hass_data[CONF_USERNAME], hass_data[CONF_PASSWORD])
        return energa

    def _refresh_data(self) -> EnergaData:
        """Sync task to get the data from Energa My Meter"""
        _LOGGER.debug('Refreshing Energa data...')

        hass_data = dict(self.entry.data)
        energa = self._create_new_connection()
        result = energa.get_account_main_data(hass_data[CONFIG_FLOW_SELECTED_METER_NUMBER],
                                              hass_data[CONFIG_FLOW_SELECTED_METER_ID])
        energa.disconnect()
        return result

    def _convert_to_statistic(
            self,
            historical_point: dict,
            timezone,
            last_updated_compare: datetime | None,
            current_sum: float
    ) -> (StatisticData, int, float, bool):
        """Converts the data returned by Energa to Home Assistant statistic object"""
        point_ts = int(int(historical_point['timestamp']) / 1000)
        point_value = float(historical_point['value']) if historical_point['value'] else 0
        point_date = datetime.fromtimestamp(timestamp=point_ts, tz=timezone)
        should_save = self._should_historical_point_be_saved(point_date, last_updated_compare)
        return StatisticData(
            start=point_date,
            sum=current_sum + point_value,
            state=point_value
        ), point_date, point_value, should_save

    @staticmethod
    def _should_historical_point_be_saved(point: datetime, last_inserted_stat: datetime):
        """Determines whether the point should be saved in statistics - we should not load them twice"""
        return last_inserted_stat is None or point > last_inserted_stat
