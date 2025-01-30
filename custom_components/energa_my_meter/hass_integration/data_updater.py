"""Contains logic of connecting to Energa and getting the data Home Assistant uses"""
import logging
from datetime import datetime, timedelta

from homeassistant.components.recorder.models import StatisticData
from homeassistant.components.recorder.statistics import get_last_statistics
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ..common import generate_entity_name, generate_stats_base_entity_name
from ..const import CONF_NUMBER_OF_DAYS_TO_LOAD, DEBUGGING_DATE_FORMAT, CONF_SELECTED_ZONES, \
    MAXIMUM_DAYS_TO_BE_LOADED_AT_ONCE, CONF_SELECTED_METER_PPE
from ..const import CONF_SELECTED_METER_NUMBER, CONF_SELECTED_METER_ID
from ..energa.client import EnergaMyMeterClient
from ..energa.data import EnergaData, EnergaStatisticsData, EnergaHistoricalPoint
from ..energa.errors import EnergaClientError
from ..energa.stats_modes import EnergaStatsModes

_LOGGER = logging.getLogger(__name__)


class EnergaDataUpdater:
    """Manages updating the data from Energa into Home Assistant"""

    def __init__(self, client: EnergaMyMeterClient, hass_data: dict, hass: HomeAssistant):
        self.client = client
        self.data = hass_data
        self.hass = hass

    def gather_basic_data(self) -> EnergaData:
        """Refreshes main information available on the account"""
        return self.client.get_account_main_data(
            self.data.get(CONF_SELECTED_METER_ID),
            self.data.get(CONF_SELECTED_METER_PPE)
        )

    def gather_stats(self, mode: EnergaStatsModes) -> dict:
        """Refreshes the statistics (per hour) from Energa for a specified mode"""
        zones = self.data[CONF_SELECTED_ZONES]

        if len(zones) == 0:
            _LOGGER.debug("The user wants no statistics sensors. Skipping updates...")
            return {}

        _LOGGER.info("Updating the statistics data for mode %s and zones [%s]...", mode.name, ", ".join(zones))
        previous_results, statistics, last_inserted_stat_date = self._get_previous_execution(
            zones, mode
        )
        starting_point = self._find_starting_point(last_inserted_stat_date)
        finishing_point = self._find_finishing_point()

        current_day = starting_point
        _LOGGER.debug(
            'Loading statistics from Energa for %s from %s to %s (last loaded stat is %s)...',
            mode.name,
            starting_point.strftime(DEBUGGING_DATE_FORMAT),
            finishing_point.strftime(DEBUGGING_DATE_FORMAT),
            last_inserted_stat_date.strftime(DEBUGGING_DATE_FORMAT) if last_inserted_stat_date else None
        )

        loaded_days = 0
        estimates = []
        try:
            while (current_day.timestamp() <= finishing_point.timestamp()
                   and loaded_days < MAXIMUM_DAYS_TO_BE_LOADED_AT_ONCE):
                _LOGGER.debug(
                    'Loading the statistics for the meter %s from %s for mode %s',
                    self.data[CONF_SELECTED_METER_NUMBER],
                    current_day.strftime(DEBUGGING_DATE_FORMAT),
                    mode.name
                )
                historical_data: EnergaStatisticsData = self.client.get_statistics(
                    self.data[CONF_SELECTED_METER_ID],
                    current_day,
                    mode
                )
                loaded_days += 1
                stats_timezone = dt_util.get_time_zone(historical_data.timezone)

                if len(historical_data.historical_points) == 0:
                    _LOGGER.debug('No statistics in %s. Skipping the day...',
                                  current_day.strftime(DEBUGGING_DATE_FORMAT))
                    current_day = current_day + timedelta(days=1)
                    continue

                for point in historical_data.historical_points:
                    point_date = point.get_date(tz=stats_timezone)

                    current_day = point_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

                    # If this point is already saved, let's just skip that to avoid duplicate entries
                    if (last_inserted_stat_date is not None
                            and point_date <= last_inserted_stat_date.astimezone(stats_timezone)):
                        continue

                    if point.is_estimated:
                        _LOGGER.debug(
                            'Energa returned an estimate on %s - we should skip that until we will get a real data.',
                            point.get_date(tz=stats_timezone).strftime(DEBUGGING_DATE_FORMAT)
                        )
                        estimates.append(point)
                        continue

                    if len(estimates) > 0:
                        _LOGGER.debug(
                            "Found a new normal-value point. Loading %s previously skipped estimates...",
                            len(estimates)
                        )
                        for estimate in estimates:
                            estimate_date = estimate.get_date(tz=stats_timezone)
                            self._process_point_as_statistic(
                                estimate, estimate_date, historical_data.zones, previous_results, statistics
                            )
                        estimates = []

                    self._process_point_as_statistic(
                        point, point_date, historical_data.zones, previous_results, statistics
                    )
        except EnergaClientError as error:
            _LOGGER.error("There was an error when getting the statistics: %s.", error)

        if len(estimates) > 0:
            _LOGGER.debug(
                "Skipping processing %s estimates, because they were not followed by the real data: [%s]",
                len(estimates), estimates
            )

        # Only do this for the data packages that are in the past
        if (starting_point + timedelta(days=MAXIMUM_DAYS_TO_BE_LOADED_AT_ONCE)
                < dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)):
            for zone in zones:
                if len(statistics[zone]) == 0:
                    point_dt = (
                            starting_point + timedelta(days=max(MAXIMUM_DAYS_TO_BE_LOADED_AT_ONCE - 1, 1))
                    ).replace(hour=0, minute=0, second=0, microsecond=0)

                    _LOGGER.info(
                        "No statistics found in the period of %s + %s days for zone '%s'. " +
                        "Adding a simple statistic at the %s, so we won't repeat...",
                        starting_point.strftime(DEBUGGING_DATE_FORMAT),
                        MAXIMUM_DAYS_TO_BE_LOADED_AT_ONCE,
                        zone,
                        point_dt.strftime(DEBUGGING_DATE_FORMAT)
                    )
                    statistics[zone].append(
                        StatisticData(
                            start=point_dt,
                            sum=previous_results.get(zone, 0),
                            state=0
                        ))

        return statistics

    @staticmethod
    def _process_point_as_statistic(
            point: EnergaHistoricalPoint, point_date: datetime, zones: [str], previous_results, statistics
    ):
        """Processes the point as a new statistic to save"""
        for zone in zones:
            point_value = point.get_value_for_zone(zone)
            current_sum = previous_results.get(zone, 0) + point_value
            statistic = StatisticData(start=point_date, sum=current_sum, state=point_value)
            previous_results[zone] = current_sum
            statistics[zone].append(statistic)

    def _get_previous_execution(self, zones: [str], mode: EnergaStatsModes):
        """Returns the context of the last processed execution"""
        main_zone = zones[0]
        _LOGGER.debug("Getting previous executions for [%s]...", ", ".join(zones))
        previous_stats = {}
        previous_results = {}
        statistics = {}
        for zone in zones:
            stat_name = generate_entity_name(self.data[CONF_SELECTED_METER_NUMBER],
                                             generate_stats_base_entity_name(mode, zone))
            previous_stat = get_last_statistics(self.hass, 1, stat_name, True, {"sum", "state"})
            if len(previous_stat) == 1 and len(previous_stat[stat_name]) == 1 and \
                    "sum" in previous_stat[stat_name][0] and "end" in previous_stat[stat_name][0]:
                stat_entry = previous_stat[stat_name][0]
                previous_stats[zone] = stat_entry
                previous_results[zone] = stat_entry.get('sum', 0.0)
            else:
                previous_results[zone] = 0
            statistics[zone] = []
        last_inserted_stat_date = self._get_last_processed_date(previous_stats.get(main_zone, None))
        return previous_results, statistics, last_inserted_stat_date

    @staticmethod
    def _find_finishing_point():
        """
        The date that is considered stopping point for the gathering statistics logic.
        """
        return dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)

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
            days_ago = self.data[CONF_NUMBER_OF_DAYS_TO_LOAD]
            starting_point = (dt_util.now() - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0,
                                                                                microsecond=0)
            _LOGGER.debug(
                'Could not get last inserted statistics, will automatically gather the data from %s days ago (%s)...',
                days_ago, starting_point.strftime(DEBUGGING_DATE_FORMAT))
        return starting_point

    @staticmethod
    def _get_last_processed_date(last_inserted_stat):
        """Returns the date of the last processed statistic - or None, if it's not available"""
        last_processed = None
        if last_inserted_stat is not None:
            last_processed = last_inserted_stat["start"]
            if isinstance(last_processed, (int, float)):
                last_processed = dt_util.utc_from_timestamp(last_processed)
            if isinstance(last_processed, str):
                last_processed = dt_util.parse_datetime(last_processed)
        return last_processed
