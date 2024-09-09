"""Energa My Meter integration module - authorization, accessing the data"""

import logging
from datetime import datetime

from custom_components.energa_my_meter.energa.connector import EnergaWebsiteConnector
from custom_components.energa_my_meter.energa.data import EnergaData, EnergaStatisticsData
from custom_components.energa_my_meter.energa.errors import (
    EnergaNoSuitableMetersFoundError,
    EnergaWebsiteLoadingError, EnergaStatisticsCouldNotBeLoadedError, EnergaConnectionNotOpenedError,
)
from custom_components.energa_my_meter.energa.scrapper import EnergaWebsiteScrapper

_LOGGER = logging.getLogger(__name__)


class EnergaMyMeterClient:
    """Base logic of gathering the data from the Energa website - the order of requests and scraping the data"""

    def __init__(self):
        self._energa_integration = None

    def open_connection(self, username: str, password: str):
        """Opens a new connection to the Energa website. This should be done as rarely as possible"""
        _LOGGER.debug("Opening a new connection to the Energa website...")
        self._energa_integration = EnergaWebsiteConnector()
        self._energa_integration.authenticate(username, password)
        _LOGGER.debug("Logged successfully to Energa website")

    def get_meters(self):
        """Returns the list of meters found on the website for the specified user"""
        if self._energa_integration is None:
            raise EnergaConnectionNotOpenedError("Open the connection first")

        website = self._energa_integration.open_home_page()
        meters_list = EnergaWebsiteScrapper.get_meters(website)
        if len(meters_list) == 0:
            raise EnergaNoSuitableMetersFoundError

        return meters_list

    def get_statistics(self, meter_id: int, starting_point: datetime) -> EnergaStatisticsData:
        """
        Returns the historical energy usage for the specified DAY resolution.
        The starting point should have 00:00:00 hour timestamp.
        """
        if self._energa_integration is None:
            raise EnergaConnectionNotOpenedError("Open the connection first")

        stats_data = self._energa_integration.get_historical_consumption_for_day(starting_point, meter_id, 'A+')
        if stats_data is None or not stats_data['success']:
            raise EnergaStatisticsCouldNotBeLoadedError
        return EnergaStatisticsData(stats_data.get('response'))

    def get_account_main_data(self, meter: int = None, meter_id: int = None) -> EnergaData:
        """Returns all useful data found on the main page of Energa website"""
        if self._energa_integration is None:
            raise EnergaConnectionNotOpenedError("Open the connection first")

        website = self._energa_integration.open_home_page()

        meter_number = meter if meter else EnergaWebsiteScrapper.get_meter_number(website)

        if not meter_number:
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
