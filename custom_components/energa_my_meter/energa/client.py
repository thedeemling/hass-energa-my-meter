"""Energa My Meter integration module - authorization, accessing the data"""

from datetime import datetime
import logging
import urllib

from homeassistant.core import HomeAssistant
import lxml.html
from mechanize import Browser, HTTPError

from custom_components.energa_my_meter.energa.const import ENERGA_MY_METER_DATA_URL, ENERGA_REQUESTS_TIMEOUT
from custom_components.energa_my_meter.energa.errors import (
    EnergaMyCounterAuthorizationError,
    EnergaNoSuitableCountersFoundError,
    EnergaWebsiteLoadingError,
)
from custom_components.energa_my_meter.energa.scrapper import EnergaMyCounterScrapper

_LOGGER = logging.getLogger(__name__)


class EnergaData:
    """Representation of the data gathered from the Energa website"""

    def __init__(self, data: dict):
        self._data: dict = data

    @property
    def meter_number(self) -> int:
        """Returns the number of the meter - known to the client from the contract"""
        return self._data['meter_number']

    @property
    def seller(self) -> str:
        """Returns the name of the contract seller"""
        return self._data['seller']

    @property
    def client_type(self) -> str:
        """Returns the type of the client"""
        return self._data['client_type']

    @property
    def contract_period(self) -> str:
        """Returns the period of the contract in the string representation"""
        return self._data['contract_period']

    @property
    def energy_used(self) -> int:
        """Returns the incremental value of the meter"""
        return self._data['energy_used']

    @property
    def energy_used_last_update(self) -> datetime:
        """Returns the information when was the last time Energa updated the value of the meter"""
        return self._data['energy_used_last_update']

    @property
    def energy_produced(self) -> int:
        """Returns the incremental value of the information how much the meter registered produced energy"""
        return self._data['energy_produced']

    @property
    def meter_id(self) -> int:
        """Returns the internal ID of the meter (used in the Energa website calls)"""
        return self._data['meter_id']

    @property
    def ppe_address(self) -> str:
        """Returns address of the registered PPE related to the meter"""
        return self._data['ppe_address']

    @property
    def ppe_number(self) -> int:
        """Returns number of the registered PPE related to the meter"""
        return self._data['ppe_number']

    @property
    def tariff(self) -> str:
        """Returns the name of the tariff related to the meter"""
        return self._data['tariff']

    def __getitem__(self, items):
        return self._data.__getitem__(items)


class EnergaMyMeterClient:
    """Base logic of gathering the data from the Energa website - the order of requests and scraping the data"""

    def __init__(self, hass: HomeAssistant):
        self._hass: HomeAssistant = hass

    async def get_meters(self, username: str, password: str):
        """Returns the list of counters found on the website for the specified user"""
        website = await self._login(username, password)

        counters_list = EnergaMyCounterScrapper.get_meters(website)

        if len(counters_list) == 0:
            raise EnergaNoSuitableCountersFoundError

        return counters_list

    async def gather_data(self, username: str, password: str) -> EnergaData:
        """Returns all useful data found on the main page of Energa website"""

        website = await self._login(username, password)

        _LOGGER.debug(
            'Logged successful into the Energa My Meter website {%s}. Gathering data...', ENERGA_MY_METER_DATA_URL)

        meter_number = EnergaMyCounterScrapper.get_meter_number(website)

        if not meter_number:
            raise EnergaWebsiteLoadingError

        result = {
            'seller': EnergaMyCounterScrapper.get_seller(website),
            'client_type': EnergaMyCounterScrapper.get_client_type(website),
            'contract_period': EnergaMyCounterScrapper.get_contract_period(website),
            'energy_used': EnergaMyCounterScrapper.get_energy_used(website),
            'energy_used_last_update': EnergaMyCounterScrapper.get_energy_used_last_update(website),
            'energy_produced': EnergaMyCounterScrapper.get_energy_produced(website),
            'meter_id': EnergaMyCounterScrapper.get_meter_id(website, meter_number),
            'ppe_address': EnergaMyCounterScrapper.get_ppe_address(website),
            'ppe_number': EnergaMyCounterScrapper.get_ppe_number(website),
            'tariff': EnergaMyCounterScrapper.get_tariff(website),
            'meter_number': meter_number,
        }
        _LOGGER.debug('Got an update from Energa website for the counter nr {%s}: {%s}', meter_number, result)
        return EnergaData(result)

    async def _login(self, username: str, password: str):
        """The logic of authenticating into the Energa website. Returns the HTML after being logged in."""

        energa_integration = EnergaWebsiteIntegration(self._hass)
        try:
            html_result = await energa_integration.get_meter_data(username, password)
        except (HTTPError, urllib.error.URLError) as error:
            _LOGGER.error('Got an error response from the energa website {%s}: {%s}', ENERGA_MY_METER_DATA_URL, error)
            raise EnergaWebsiteLoadingError from error

        if html_result is None:
            raise EnergaWebsiteLoadingError

        if not EnergaMyCounterScrapper.is_logged_in(html_result):
            raise EnergaMyCounterAuthorizationError

        return html_result


class EnergaWebsiteIntegration:
    """Simple wrapper for accessing the Energa website with mechanize framework"""

    def __init__(self, hass: HomeAssistant):
        self._hass: HomeAssistant = hass
        self._browser: Browser = self._prepare_browser()

    @property
    def browser(self):
        """Returns the currently configured browser"""
        return self._browser

    @browser.setter
    def browser(self, value):
        """Updates the currently configured browser"""
        self._browser = value

    async def open_energa_website(self):
        """Opens the home page of Energa My Meter website"""
        _LOGGER.debug('Opening Energa My Meter website {%s}...', ENERGA_MY_METER_DATA_URL)
        response = await self._hass.async_add_executor_job(
            lambda: self._browser.open(ENERGA_MY_METER_DATA_URL, timeout=ENERGA_REQUESTS_TIMEOUT))
        html_response = response.read()
        _LOGGER.debug('Load website response {%s} [{%s}]', response.geturl(), response.getcode())
        return self._parse_response(html_response)

    async def authorize_user(self, username: str, password: str):
        """Authorize user and return the logged in website"""
        self._browser.select_form(id="loginForm")
        self._browser.form["j_username"] = username
        self._browser.form['j_password'] = password
        _LOGGER.debug('Logging into Energa My Meter website {%s}...', ENERGA_MY_METER_DATA_URL)
        response = await self._hass.async_add_executor_job(self._browser.submit)
        html_response = response.read()
        _LOGGER.debug('Logged in response {%s} [{%s}]', response.geturl(), response.getcode())
        return self._parse_response(html_response)

    async def get_meter_data(self, username: str, password: str):
        """For simplicity shortcut for authorizing the user and getting the response"""
        await self.open_energa_website()
        return await self.authorize_user(username, password)

    @staticmethod
    def _parse_response(html_response):
        return lxml.html.fromstring(html_response)

    @staticmethod
    def _prepare_browser() -> Browser:
        """Prepares a new browser for Energa calls"""
        browser: Browser = Browser()
        browser.set_handle_robots(False)
        browser.set_handle_equiv(False)
        browser.set_handle_refresh(False)
        return browser
