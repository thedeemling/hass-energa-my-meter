"""
A special type of sensor that allows to overwrite states for statistics in the past.
As Energa does not report live data, but updates it at most once a day, simply downloading the current meter value
will not create a proper statistics.
"""
import logging
from datetime import datetime, timedelta

from homeassistant.components.recorder.models import StatisticMetaData, StatisticData
from homeassistant.components.recorder.statistics import get_last_statistics, async_import_statistics
from homeassistant.components.sensor import SensorStateClass, ENTITY_ID_FORMAT, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, EntityCategory
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from custom_components.energa_my_meter.const import PREVIOUS_DAYS_NUMBER_TO_BE_LOADED
from custom_components.energa_my_meter.energa.data import EnergaStatisticsData
from custom_components.energa_my_meter.hass_integration.energa_entity import EnergaSensorEntity

_LOGGER = logging.getLogger(__name__)
DEBUGGING_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'


class EnergyConsumedStatisticsSensor(EnergaSensorEntity):
    """
    Representation of Energa statistics sensor.
    This sensor cannot have any current state (will always be shown as unavailable)
    and exists only to keep track of statistics.
    """

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry, coordinator)
        self._state = None
        self._updatets = None

        self._attr_name = 'Energy used'
        self._name_id = 'energy_consumed_stats'

        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = SensorDeviceClass.ENERGY

        self._attr_extra_state_attributes = {}
        self._attr_icon = 'mdi:meter-electric-outline'
        self._attr_precision = 5
        self.entity_id = f'sensor.energa_{entry["meter_number"]}_energy_consumed_stats'
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unit_of_measurement = self._attr_native_unit_of_measurement
        self.entity_id = ENTITY_ID_FORMAT.format(f'energa_{entry["meter_number"]}_{self._name_id}')
        self._available: bool = True

    @staticmethod
    def statistics(s: str) -> str:
        """Statistics method"""
        return f'{s}_statistics'

    async def async_update(self):
        """Update statistics data."""
        # We need to force having None as a current state due to Home Assistant limitations
        # If the state is set, we will not be able to update statistics in the past
        self._state = None
        self._updatets = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        last_inserted_stat = await get_instance(self.hass).async_add_executor_job(
            get_last_statistics,
            self.hass,
            1,
            self.entity_id,
            True,
            {"sum", "state"},
        )

        last_inserted_stat_date = self._get_last_processed_date(last_inserted_stat)
        starting_point = self._find_starting_point(last_inserted_stat_date)
        finishing_point = self._find_finishing_point()
        total_usage = self._get_total_usage(last_inserted_stat)

        if starting_point is None:
            _LOGGER.debug('Could not calculate starting point - probably nothing to do. Skipping statistics update.')
            return

        statistics = await get_instance(self.hass).async_add_executor_job(
            self.get_statistics,
            starting_point,
            finishing_point,
            last_inserted_stat_date,
            total_usage
        )
        await self._async_store_statistics(statistics)

    def get_statistics(
            self, starting_point: datetime, finishing_point: datetime,
            last_inserted_stat_date: datetime, total_usage: float
    ) -> list:
        """Generates Energa statistics to be imported into Home Assistant"""
        statistics = []
        last_statistic_date = starting_point
        energa = self.coordinator.create_new_connection()
        _LOGGER.debug(
            'Will load statistics from %s to %s (last loaded stat is %s (%s))...',
            starting_point.strftime(DEBUGGING_DATE_FORMAT),
            finishing_point.strftime(DEBUGGING_DATE_FORMAT),
            last_inserted_stat_date.strftime(DEBUGGING_DATE_FORMAT) if last_inserted_stat_date else None,
            total_usage
        )
        while starting_point.timestamp() < finishing_point.timestamp():
            _LOGGER.debug('Loading the statistics for the meter %s from %s', self._entry["meter_number"],
                          starting_point.strftime(DEBUGGING_DATE_FORMAT))
            historical_data: EnergaStatisticsData = self.coordinator.load_statistics(starting_point, energa)
            timezone = dt_util.get_time_zone(historical_data.timezone)
            last_updated_compare = last_inserted_stat_date.astimezone(timezone) if last_inserted_stat_date else None

            for point in historical_data.historical_points:
                point_ts = int(int(point['timestamp']) / 1000)
                point_value = float(point['value'])
                point_date = datetime.fromtimestamp(timestamp=point_ts, tz=timezone)
                last_statistic_date = datetime.fromtimestamp(timestamp=point_ts, tz=timezone)
                if self._should_historical_point_be_saved(point_ts, last_updated_compare):
                    total_usage += point_value
                    statistics.append(StatisticData(start=point_date, sum=total_usage, state=point_value))

            starting_point = last_statistic_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        return statistics

    @staticmethod
    def _find_starting_point(last_processed):
        """
        Calculates the starting point for the Energa statistics.
        It always needs to start with "00:00:00" hour.
        Determines whether the last processed day has finished with the last hour (23:00:00)
        - it means that we can start the next day.
        """
        if last_processed is not None:
            if last_processed.hour == 23:
                starting_point = (last_processed + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                starting_point = last_processed.replace(hour=0, minute=0, second=0, microsecond=0)
            _LOGGER.debug('Last processed timestamp is %s. Next starting point should be %s', last_processed,
                          starting_point)
        else:
            days_ago = PREVIOUS_DAYS_NUMBER_TO_BE_LOADED
            starting_point = (datetime.now() - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0,
                                                                                 microsecond=0)
            _LOGGER.debug(
                'Could not get last inserted statistics, will automatically gather the data from %s days ago (%s)...',
                days_ago, starting_point.strftime(DEBUGGING_DATE_FORMAT))
        return starting_point

    @staticmethod
    def _find_finishing_point():
        """
        The date that is considered stopping point for the gathering statistics logic.
        """
        return datetime.now(tz=dt_util.UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    def _get_last_processed_date(self, last_inserted_stat):
        """Returns the date of the last processed statistic - or None, if it's not available"""
        last_processed = None
        if self._is_last_inserted_stat_valid(last_inserted_stat):
            last_processed = last_inserted_stat[self.entity_id][0]["end"]
            if isinstance(last_processed, (int, float)):
                last_processed = dt_util.utc_from_timestamp(last_processed)
            if isinstance(last_processed, str):
                last_processed = dt_util.parse_datetime(last_processed)
        return last_processed

    def _get_total_usage(self, last_inserted_stat):
        """Returns the last saved total usage - or, if it's not available, starts from 0"""
        return float(last_inserted_stat[self.entity_id][0]["sum"]) if self._is_last_inserted_stat_valid(
            last_inserted_stat) else 0.0

    def _is_last_inserted_stat_valid(self, last_inserted_stat):
        """Determines whether the last saved state is valid & usable by the integration"""
        return len(last_inserted_stat) == 1 and len(last_inserted_stat[self.entity_id]) == 1 and \
            "sum" in last_inserted_stat[self.entity_id][0] and "end" in last_inserted_stat[self.entity_id][0]

    @staticmethod
    def _should_historical_point_be_saved(point: int, last_inserted_stat: datetime):
        """Determines whether the point should be saved in statistics - we should not load them twice"""
        return (last_inserted_stat is None
                or int(last_inserted_stat.timestamp()) < point)

    async def _async_store_statistics(self, statistics: list):
        """Saves the gathered statistics in Home Assistant"""
        metadata = StatisticMetaData(
            source="recorder",
            statistic_id=self.entity_id,
            name=self.name,
            unit_of_measurement=self._attr_unit_of_measurement,
            has_mean=False,
            has_sum=True,
        )
        if len(statistics) > 0:
            _LOGGER.debug('Saving the statistics: Metadata => %s, Statistics => %s', metadata, statistics)
            async_import_statistics(self.hass, metadata, statistics)
        else:
            _LOGGER.debug('No new statistics to save.')
