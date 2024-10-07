"""
Contains the internal wrapper for Energa My Meter website.
Handles the underlying browser framework
"""

import json
import logging
import urllib
from datetime import datetime
from urllib.error import HTTPError

import lxml.html
import mechanize
from mechanize import Browser

from .const import ENERGA_MY_METER_DATA_URL, ENERGA_REQUESTS_TIMEOUT, \
    ENERGA_HISTORICAL_DATA_URL, ENERGA_MY_METER_LOGIN_URL
from .errors import (
    EnergaWebsiteLoadingError,
    EnergaMyMeterAuthorizationError,
    EnergaMyMeterCaptchaRequirementError
)
from .scrapper import EnergaWebsiteScrapper

_LOGGER = logging.getLogger(__name__)


class EnergaWebsiteConnector:
    """Simple wrapper for accessing the Energa website with mechanize framework"""
    _browser: Browser

    @property
    def browser(self):
        """Returns the currently configured browser"""
        return self._browser

    @browser.setter
    def browser(self, value):
        """Updates the currently configured browser"""
        self._browser = value

    def authenticate(self, username: str, password: str, browser: Browser = None) -> bool:
        """Forces logging the user out & authenticates to the Energa website"""
        self._browser: Browser = browser if browser else self._prepare_browser()
        self._browser.cookiejar.clear()
        html_result = self._authorize_user(username, password)
        self._verify_logged_in(html_result)
        return html_result

    def disconnect(self):
        """Disconnects from the Energa website"""
        self._browser.close()

    def get_historical_consumption_for_day(self, start_date: datetime, meter_id: int, mode: str):
        """Returns the historical consumption of the meter for the specified day"""
        try:
            request = mechanize.Request(url=ENERGA_HISTORICAL_DATA_URL, method='GET', data={
                'mainChartDate': int(start_date.timestamp() * 1000),
                'type': 'DAY',
                'meterPoint': meter_id,
                'mo': mode
            })
            response = self._browser.open(request, timeout=ENERGA_REQUESTS_TIMEOUT)
            json_response = response.read()
            return json.loads(json_response)
        except (HTTPError, urllib.error.URLError) as error:
            _LOGGER.error('Got an error response from the energa website %s: %s', ENERGA_HISTORICAL_DATA_URL, error)
            raise EnergaWebsiteLoadingError from error

    def _authorize_user(self, username: str, password: str):
        """Authorize user and return the logged in website. It uses simple POST form request"""
        login_page = self._open_page(ENERGA_MY_METER_LOGIN_URL)
        token = EnergaWebsiteScrapper.get_xrf_token(login_page)
        request = mechanize.Request(url=ENERGA_MY_METER_LOGIN_URL, method='POST', data={
            'selectedForm': 1,
            'save': 'save',
            '_antixsrf': token,
            'clientOS': 'web',
            'j_username': username,
            'j_password': password,
            'rememberMe': 'on',
            'loginNow': 'zaloguj się'
        })
        return self._open_page(request)

    def open_home_page(self):
        """Opens the main view of Energa My Meter that contains most of the information"""
        html_result = self._open_page(ENERGA_MY_METER_DATA_URL)
        self._verify_logged_in(html_result)
        return html_result

    def _open_page(self, url):
        """Opens the home page of Energa My Meter website"""
        try:
            response = self._browser.open(url, timeout=ENERGA_REQUESTS_TIMEOUT)
            if response is not None:
                html_response = response.read()
            else:
                raise EnergaWebsiteLoadingError
        except (HTTPError, urllib.error.URLError) as error:
            _LOGGER.error('Got an error response from the energa website {%s}: {%s}', url, error)
            raise EnergaWebsiteLoadingError from error
        return self._parse_response(html_response)

    @staticmethod
    def _verify_logged_in(html_result):
        """Throws a suitable exception if there was any error loading the user data"""
        if html_result is None:
            raise EnergaWebsiteLoadingError

        if EnergaWebsiteScrapper.is_captcha_shown(html_result):
            raise EnergaMyMeterCaptchaRequirementError

        if not EnergaWebsiteScrapper.is_logged_in(html_result):
            raise EnergaMyMeterAuthorizationError

    @staticmethod
    def _parse_response(html_response):
        """Parses the HTML response"""
        return lxml.html.fromstring(html_response)

    @staticmethod
    def _prepare_browser() -> Browser:
        """Prepares a new browser for Energa calls"""
        browser: Browser = Browser()
        browser.set_handle_robots(False)
        browser.set_handle_equiv(False)
        browser.set_handle_refresh(False)
        return browser
