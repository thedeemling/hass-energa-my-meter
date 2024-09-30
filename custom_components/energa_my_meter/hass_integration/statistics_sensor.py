"""
A special type of sensor that allows to overwrite states for statistics in the past.
As Energa does not report live data, but updates it at most once a day, simply downloading the current meter value
will not create a proper statistics.
"""
import logging
from datetime import timedelta

from homeassistant.components.recorder.models import StatisticMetaData
from homeassistant.components.recorder.statistics import get_last_statistics, async_import_statistics
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, EntityCategory, CONF_SCAN_INTERVAL
from homeassistant.helpers.recorder import get_instance
from homeassistant.util import dt as dt_util

from custom_components.energa_my_meter.const import DEBUGGING_DATE_FORMAT, \
    CONFIG_FLOW_NUMBER_OF_DAYS_TO_LOAD, DEFAULT_SCAN_INTERVAL
from custom_components.energa_my_meter.energa.errors import EnergaClientError
from custom_components.energa_my_meter.hass_integration.base_sensor import EnergaBaseSensor
from custom_components.energa_my_meter.hass_integration.statistics_converter import EnergaUsageStatistics

_LOGGER = logging.getLogger(__name__)


class EnergyConsumedStatisticsSensor(EnergaBaseSensor):
    """
    Representation of Energa statistics sensor.
    This sensor cannot have any current state (will always be shown as unavailable)
    and exists only to keep track of statistics.
    """

    def __init__(self, entry: ConfigEntry):
        super().__init__(
            entry=entry,
            name_id='energy_consumed_stats',
            name='Energy used',
            icon='mdi:meter-electric-outline'
        )
        self._state = None
        self._update_ts = None
        self._next_update_ts = None

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_extra_state_attributes = {}
        self._attr_precision = 5
        self.entity_id = f'sensor.energa_{entry["meter_number"]}_energy_consumed_stats'
        self._available = True
        self._converter: EnergaUsageStatistics = EnergaUsageStatistics(entry)

    @staticmethod
    def statistics(s: str) -> str:
        """Statistics method"""
        return f'{s}_statistics'

    def _should_poll(self) -> bool:
        return self._next_update_ts is None or dt_util.parse_datetime(self._next_update_ts) < dt_util.now()

    async def async_update(self):
        """Update statistics data."""
        # We do not want to update the sensor too much. The method 'should_poll' is cached in Home Assistant
        if not self._should_poll():
            return

        # We need to force having None as a current state due to Home Assistant limitations
        # If the state is set, we will not be able to update statistics in the past
        self._state = None
        self._set_update_attributes()

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

        try:
            statistics = await get_instance(self.hass).async_add_executor_job(
                self._converter.load_statistics,
                starting_point,
                finishing_point,
                last_inserted_stat_date,
                total_usage
            )
            if len(statistics) > 0:
                await self._async_store_statistics(statistics)
                _LOGGER.debug('%s statistics added. Next update: %s', len(statistics), self._next_update_ts)
            else:
                _LOGGER.debug('No new statistics to save. Next update: %s', self._next_update_ts)
        except EnergaClientError as e:
            self._available = False
            _LOGGER.error("Could not get statistics for the Energa sensor: %s", e)

    def _find_starting_point(self, last_processed):
        """
        Calculates the starting point for the Energa statistics.
        It always needs to start with "00:00:00" hour.
        Determines whether the last processed day has finished with the last hour (23:00:00)
        - it means that we can start the next day.
        """
        if last_processed is not None:
            next_to_process = dt_util.as_local(last_processed) + timedelta(hours=1)
            starting_point = next_to_process.replace(hour=0, minute=0, second=0, microsecond=0)
            _LOGGER.debug(
                'Last processed timestamp is %s. Next starting point should be %s',
                dt_util.as_local(last_processed),
                starting_point
            )
        else:
            days_ago = self._entry[CONFIG_FLOW_NUMBER_OF_DAYS_TO_LOAD]
            starting_point = (dt_util.now() - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0,
                                                                                microsecond=0)
            _LOGGER.debug(
                'Could not get last inserted statistics, will automatically gather the data from %s days ago (%s)...',
                days_ago, starting_point.strftime(DEBUGGING_DATE_FORMAT))
        return starting_point

    def _set_update_attributes(self):
        this_update = dt_util.now()
        self._update_ts = this_update.strftime(DEBUGGING_DATE_FORMAT)
        scan_interval = self._entry.get(CONF_SCAN_INTERVAL) or DEFAULT_SCAN_INTERVAL
        self._next_update_ts = (this_update + timedelta(minutes=scan_interval)).strftime(DEBUGGING_DATE_FORMAT)

    @staticmethod
    def _find_finishing_point():
        """
        The date that is considered stopping point for the gathering statistics logic.
        """
        return dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def _get_last_processed_date(self, last_inserted_stat):
        """Returns the date of the last processed statistic - or None, if it's not available"""
        last_processed = None
        if self._is_last_inserted_stat_valid(last_inserted_stat):
            last_processed = last_inserted_stat[self.entity_id][0]["start"]
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
        _LOGGER.debug(
            'Saving %s statistics: Metadata => %s, Statistics => %s',
            len(statistics), metadata, statistics
        )
        async_import_statistics(self.hass, metadata, statistics)
