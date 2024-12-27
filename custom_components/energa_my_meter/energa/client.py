"""Energa My Meter integration module - authorization, accessing the data"""

import logging
from datetime import datetime

from .connector import EnergaWebsiteConnector
from .data import EnergaData, EnergaStatisticsData
from .errors import (
    EnergaNoSuitableMetersFoundError,
    EnergaWebsiteLoadingError,
)
from .scrapper import EnergaWebsiteScrapper
from .stats_modes import EnergaStatsModes, EnergaStatsTypes

_LOGGER = logging.getLogger(__name__)


class EnergaMyMeterClient:
    """Base logic of gathering the data from the Energa website - the order of requests and scraping the data"""

    def __init__(self):
        self._energa_integration: EnergaWebsiteConnector = EnergaWebsiteConnector()

    def open_connection(self, username: str, password: str):
        """Opens a new connection to the Energa website. This should be done as rarely as possible"""
        _LOGGER.debug("Opening a new connection to the Energa website...")
        self._energa_integration.authenticate(username, password)

    def disconnect(self):
        """Disconnects from the Energa website"""
        _LOGGER.debug('Closing the connection to the Energa website...')
        self._energa_integration.disconnect()

    def get_meters(self):
        """Returns the list of meters found on the website for the specified user"""
        website = self._energa_integration.open_account_page()
        meters_list = EnergaWebsiteScrapper.get_meters(website)
        if len(meters_list) == 0:
            raise EnergaNoSuitableMetersFoundError
        return meters_list

    def get_supported_zones(self, meter_id: int, date: datetime,
                            tariff_name: str | None = None) -> [str]:
        """Returns the list of supported zones found on the website for the specified user"""
        starting_point = date.replace(hour=0, minute=0, second=0, microsecond=0)
        stats = self.get_statistics(meter_id, starting_point, EnergaStatsModes.ENERGY_PRODUCED, tariff_name)
        return stats.zones

    def get_statistics(
            self, meter_id: int, starting_point: datetime, mode: EnergaStatsModes,
            tariff_name: str | None = None
    ) -> EnergaStatisticsData:
        """
        Returns the historical energy usage for the specified DAY resolution.
        The starting point should have 00:00:00 hour timestamp.
        """
        return self._energa_integration.get_historical_consumption_for_day(
            starting_point, meter_id, mode,
            tariff_name
        )

    def get_first_statistics_date(self, meter_id: int) -> datetime | None:
        """Returns the first statistics returned by Energa for the specific meter"""
        _LOGGER.debug('Finding the first statistic for the meter %s...', meter_id)
        start_of_current_year = datetime.now().replace(month=1, day=1)
        first_found_month = self._energa_integration.get_first_historical_consumption_for_type(
            start_of_current_year, meter_id, EnergaStatsModes.ENERGY_CONSUMED, EnergaStatsTypes.YEAR)
        if not first_found_month:
            _LOGGER.debug('No statistics at all found for meter %s', meter_id)
            return None
        first_day_in_month = first_found_month.replace(day=1)
        first_found_day = self._energa_integration.get_first_historical_consumption_for_type(
            first_day_in_month, meter_id, EnergaStatsModes.ENERGY_CONSUMED, EnergaStatsTypes.MONTH
        )
        if not first_found_day:
            _LOGGER.warning(
                'Something went wrong when getting the first day for meter %s from month %s',
                meter_id, first_day_in_month.strftime('%Y/%m/%d')
            )
            return None
        _LOGGER.debug('The first found day statistic for the meter %s is %s', meter_id,
                      first_found_day.strftime('%Y/%m/%dT%H:%M:%S'))
        return first_found_day

    def get_account_main_data(self, meter_id: int | None = None, ppe: int | None = None) -> EnergaData:
        """Returns all useful data found on the main page of Energa website"""
        _LOGGER.debug("Getting account main data for meter (id: %s, ppe: %s)", meter_id, ppe)
        website = self._energa_integration.open_home_page(meter_id, ppe)

        page_ppe = EnergaWebsiteScrapper.get_ppe_number(website)
        ppe_number = ppe if ppe else page_ppe

        if str(page_ppe) != str(ppe_number):
            _LOGGER.warning(
                ("The configuration does not match the returned data"
                 + " (wanted ppe: %s, got: %s)"), ppe_number, page_ppe,
            )

        if ppe_number is None:
            raise EnergaWebsiteLoadingError

        result = EnergaData({
            'seller': EnergaWebsiteScrapper.get_seller(website),
            'client_type': EnergaWebsiteScrapper.get_client_type(website),
            'contract_period': EnergaWebsiteScrapper.get_contract_period(website),
            'ppe_address': EnergaWebsiteScrapper.get_ppe_address(website),
            'ppe_number': ppe_number,
            'tariff': EnergaWebsiteScrapper.get_tariff(website),
            'meter_name': EnergaWebsiteScrapper.get_meter_name(website),
            'meter_readings': EnergaWebsiteScrapper.get_meter_readings(website),
        })
        _LOGGER.debug('Got an update from Energa website for the meter nr {%s}: %s', meter_id, result)
        return result
