import json
import logging
import urllib
from datetime import datetime
from urllib.error import HTTPError

import lxml.html
import mechanize
from homeassistant.core import HomeAssistant
from mechanize import Browser

from custom_components.energa_my_meter import EnergaWebsiteLoadingError, EnergaMyMeterAuthorizationError
from custom_components.energa_my_meter.energa.const import ENERGA_MY_METER_DATA_URL, ENERGA_REQUESTS_TIMEOUT, \
    ENERGA_MY_METER_URL, ENERGA_HISTORICAL_DATA_URL, ENERGA_MY_METER_LOGIN_URL
from custom_components.energa_my_meter.energa.scrapper import EnergaWebsiteScrapper

_LOGGER = logging.getLogger(__name__)


class EnergaWebsiteConnector:
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

    async def authenticate(self, username: str, password: str):
        """Forces logging the user out & authenticates to the Energa website"""
        self._browser.cookiejar.clear()
        await self._open_page(ENERGA_MY_METER_LOGIN_URL)
        html_result = await self._authorize_user(username, password)
        if html_result is None:
            raise EnergaWebsiteLoadingError

        if not EnergaWebsiteScrapper.is_logged_in(html_result):
            raise EnergaMyMeterAuthorizationError

        return html_result

    async def get_historical_consumption_for_day(self, start_date: datetime, meter_id: int):
        """Returns the historical consumption of the meter for the specified day"""
        _LOGGER.debug(
            'Getting the historical data from %s for the day resolution from %s for the meter with ID %s...',
            ENERGA_MY_METER_URL, start_date.strftime('%Y-%m-%dT%H:%M:%S'), meter_id)
        try:
            request = mechanize.Request(url=ENERGA_HISTORICAL_DATA_URL, method='GET', data={
                'mainChartDate': int(start_date.timestamp() * 1000),
                'type': 'DAY',
                'meterPoint': meter_id,
                'mo': 'A+'
            })
            _LOGGER.debug('Executing the request: %s', request.get_full_url())

            response = await self._hass.async_add_executor_job(
                lambda: self._browser.open(request, timeout=ENERGA_REQUESTS_TIMEOUT))
            json_response = response.read()
            return json.loads(json_response)
        except (HTTPError, urllib.error.URLError) as error:
            _LOGGER.error('Got an error response from the energa website %s: %s', ENERGA_HISTORICAL_DATA_URL, error)
            raise EnergaWebsiteLoadingError from error

    async def _authorize_user(self, username: str, password: str):
        """Authorize user and return the logged in website"""
        self._browser.select_form(id="loginForm")
        self._browser.form["j_username"] = username
        self._browser.form['j_password'] = password
        try:
            response = await self._hass.async_add_executor_job(self._browser.submit)
            html_response = response.read()
        except (HTTPError, urllib.error.URLError) as error:
            _LOGGER.error('Got an error response from the energa website {%s}: {%s}', ENERGA_MY_METER_DATA_URL, error)
            raise EnergaWebsiteLoadingError from error
        return self._parse_response(html_response)

    async def open_home_page(self):
        html_result = await self._open_page(ENERGA_MY_METER_DATA_URL)
        if html_result is None:
            raise EnergaWebsiteLoadingError

        if not EnergaWebsiteScrapper.is_logged_in(html_result):
            raise EnergaMyMeterAuthorizationError

        return html_result

    async def _open_page(self, url):
        """Opens the home page of Energa My Meter website"""
        _LOGGER.debug('Opening Energa My Meter website {%s}...', url)
        try:
            response = await self._hass.async_add_executor_job(
                lambda: self._browser.open(url, timeout=ENERGA_REQUESTS_TIMEOUT))
            html_response = response.read()
        except (HTTPError, urllib.error.URLError) as error:
            _LOGGER.error('Got an error response from the energa website {%s}: {%s}', url, error)
            raise EnergaWebsiteLoadingError from error
        _LOGGER.debug('Load website response {%s} [{%s}]', response.geturl(), response.getcode())
        return self._parse_response(html_response)

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
