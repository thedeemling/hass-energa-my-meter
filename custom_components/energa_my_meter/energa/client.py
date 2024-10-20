"""Energa My Meter integration module - authorization, accessing the data"""

import logging
from datetime import datetime

from .connector import EnergaWebsiteConnector
from .data import EnergaData, EnergaStatisticsData
from .errors import (
    EnergaNoSuitableMetersFoundError,
    EnergaWebsiteLoadingError, EnergaStatisticsCouldNotBeLoadedError,
)
from .scrapper import EnergaWebsiteScrapper
from .stats_modes import EnergaStatsModes

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
        website = self._energa_integration.open_home_page()
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
        stats_data = self._energa_integration.get_historical_consumption_for_day(
            starting_point, meter_id, mode,
            tariff_name
        )
        if stats_data is None or not stats_data['success']:
            raise EnergaStatisticsCouldNotBeLoadedError
        return EnergaStatisticsData(stats_data.get('response'))

    def get_account_main_data(self, meter: int = None, meter_id: int = None) -> EnergaData:
        """Returns all useful data found on the main page of Energa website"""
        website = self._energa_integration.open_home_page()

        meter_number = meter if meter else EnergaWebsiteScrapper.get_meter_number(website)

        if meter_number is None:
            raise EnergaWebsiteLoadingError

        result = {
            'seller': EnergaWebsiteScrapper.get_seller(website),
            'client_type': EnergaWebsiteScrapper.get_client_type(website),
            'contract_period': EnergaWebsiteScrapper.get_contract_period(website),
            'energy_used': EnergaWebsiteScrapper.get_energy_used(website),
            'energy_used_last_update': EnergaWebsiteScrapper.get_energy_used_last_update(website),
            'energy_produced': EnergaWebsiteScrapper.get_energy_produced(website),
            'meter_id': meter_id if meter_id else EnergaWebsiteScrapper.get_meter_id(website, meter_number),
            'ppe_address': EnergaWebsiteScrapper.get_ppe_address(website),
            'ppe_number': EnergaWebsiteScrapper.get_ppe_number(website),
            'tariff': EnergaWebsiteScrapper.get_tariff(website),
            'meter_number': meter_number
        }
        _LOGGER.debug('Got an update from Energa website for the meter nr {%s}: {%s}', meter_number, result)
        return EnergaData(result)
