"""
Contains the internal wrapper for Energa My Meter website.
Handles the underlying browser framework
"""

import json
import logging
import urllib
from datetime import timedelta, datetime
from urllib.error import HTTPError

import lxml.html
import mechanize
from homeassistant.util import dt as dt_util
from mechanize import Browser

from .const import ENERGA_MY_METER_DATA_URL, ENERGA_REQUESTS_TIMEOUT, \
    ENERGA_HISTORICAL_DATA_URL, ENERGA_MY_METER_LOGIN_URL, ENERGA_ACCOUNT_DATA_URL
from .data import EnergaStatisticsData
from .errors import (
    EnergaWebsiteLoadingError,
    EnergaMyMeterAuthorizationError,
    EnergaMyMeterCaptchaRequirementError, EnergaStatisticsCouldNotBeLoadedError, EnergaMyMeterWebsiteError
)
from .scrapper import EnergaWebsiteScrapper
from .stats_modes import EnergaStatsModes, EnergaStatsTypes

_LOGGER = logging.getLogger(__name__)
ENERGA_CERT = """-----BEGIN CERTIFICATE-----
MIIHdzCCBV+gAwIBAgIQcC5Lkwug6Xwrzg7NfD1leTANBgkqhkiG9w0BAQsFADBS
MQswCQYDVQQGEwJQTDEhMB8GA1UECgwYQXNzZWNvIERhdGEgU3lzdGVtcyBTLkEu
MSAwHgYDVQQDDBdDZXJ0dW0gT1YgVExTIEcyIFIzOSBDQTAeFw0yNTExMjYwNzEx
NDZaFw0yNjExMjYwNzExNDVaMG4xCzAJBgNVBAYTAlBMMRIwEAYDVQQIDAlwb21v
cnNraWUxDzANBgNVBAcMBkdkYW5zazEbMBkGA1UECgwSRW5lcmdhLU9wZXJhdG9y
IFNBMR0wGwYDVQQDDBQqLmVuZXJnYS1vcGVyYXRvci5wbDCCASIwDQYJKoZIhvcN
AQEBBQADggEPADCCAQoCggEBAK9VTr1YdRAB5bN+VLmExv7qkULqvltcflxtt+QU
4cWAwXzsl1DC6PYRkk9wBI4r1z2mL/swOPUBTtjUONmgjboyLXKoEn5xGyAwH600
pTvOa7TABjCFOKFZIAH7ps5CWzPnB9kZxScFsIBX0MESC8mui7KUsWoiAPQUX/eo
MSHq0j5BBh9eRNjPQozYkf/dSLAKze8P27Yp+pRZo9icmktzpO11qvArReOVeiIv
9fHnNqWZL6iE8DwTAVoeiijS7K4y4S+fBQMuFpZOrx7EmQ+5VmXyXAz3Y3CnkuH7
t26lkzU/pRLgqTseTZ0kdilfHZE8DEfmf13zEzRkHFTKC8ECAwEAAaOCAyswggMn
MAwGA1UdEwEB/wQCMAAwTwYDVR0fBEgwRjBEoEKgQIY+aHR0cDovL2NlcnR1bW92
dGxzZzJyMzljYS5jcmwuY2VydHVtLnBsL2NlcnR1bW92dGxzZzJyMzljYS5jcmww
gZoGCCsGAQUFBwEBBIGNMIGKMDUGCCsGAQUFBzABhilodHRwOi8vY2VydHVtb3Z0
bHNnMnIzOWNhLm9jc3AtY2VydHVtLmNvbTBRBggrBgEFBQcwAoZFaHR0cDovL2Nl
cnR1bW92dGxzZzJyMzljYS5yZXBvc2l0b3J5LmNlcnR1bS5wbC9jZXJ0dW1vdnRs
c2cycjM5Y2EuY2VyMB8GA1UdIwQYMBaAFOh5B22Ng/uaeWNjvKUyY7MFQXKpMCEG
A1UdIAQaMBgwCAYGZ4EMAQICMAwGCiqEaAGG9ncCZQIwHQYDVR0lBBYwFAYIKwYB
BQUHAwEGCCsGAQUFBwMCMA4GA1UdDwEB/wQEAwIFoDAzBgNVHREELDAqghQqLmVu
ZXJnYS1vcGVyYXRvci5wbIISZW5lcmdhLW9wZXJhdG9yLnBsMIIBfwYKKwYBBAHW
eQIEAgSCAW8EggFrAWkAdQDXbX0Q0af1d8LH6V/XAL/5gskzWmXh0LMBcxfAyMVp
dwAAAZq/AQhHAAAEAwBGMEQCIDDBOPiG52sojz7k3+sDfcbfbwsjSJM/Hv/eQlZS
mD0/AiAQXIeKjcgQV4SeMoCHhpYgIlhwjwi3tFD7TIK3IHjN2QB3AKyrMHBs6+yE
MfQT0vSRXxEeQiRDsfKmjE88KzunHgLDAAABmr8BCW8AAAQDAEgwRgIhALmrCcAt
1NuMqwrE+IV10LDHdyS8Rek4qwAKULdMivvnAiEA/GpsevseZnWu0bwhe1I+i8+X
5Sg9M0I5htzW6C2fTpgAdwDCMX5XRRmjRe5/ON6ykEHrx8IhWiK/f9W1rXaa2Q5S
zQAAAZq/AQn7AAAEAwBIMEYCIQCfrnVSgB1MoPm5lNBE5ITh+MX9rS134EoqqtuX
O6qknQIhAPvWaZkW16TmC0I24+27bHuekpVFZIkphFgvo2DWivqCMA0GCSqGSIb3
DQEBCwUAA4ICAQBQY03RFb2zxfnW00QCRktoUB10IHB5eFG4ualwRBN9gsuwTRZG
viDz+NzyPeU7QIQSWAkrsv0rhPm6sVU2C6fm+Vc/aYiW01afNV60C18AFvRjmpbd
EU76i4rWpJvHjuvd9Fmy1LhHw7iRp87EPDMPwLUCQov3E3GYhZGbTEqq7hHpmEhu
P37HCy2h+uvYGCojevpKIM2F0Z0/5UiFVoFcXOTRMCAdOOOGOpRXg69vq/tzbkfx
xiNUCFlkC1/Yg7hX1eBnwR+GcoRtne1iVqHhd1XTOUD4SiEp7jfvHx3v+Im0/Z2w
fy5S9WLox7aRXR1nM/788wZ3c5ospNF8AfQxdJPgf0CjAznQ/ggGSjBLMNn+1YVi
Pfm9H1hfWzpzIWVH4/KnxjtDynqPRbxtqaU9KYtAqPhl/pEH/wVRzjJ4WkfLH82W
52tJWYLcnyYWul90f1wiNRo9YrOxrkB4+ZcQjV8pHstM7JRaYn3CHxZ0kQeaf9Wr
P0fWshOMXvXTHCjIltYGQZg7T2EHu0m88UUUL7aLUIyiAUiQoIBRY84qUuccc+SG
Xii+VaHKRy76x6mwmlig/nHQ1NnxN7CadOETddjaAa22DnVwtXyN/mdFFJ5sFk8W
ER2mL4EQBhiIruRAybrEj3qto6YNEWBfYSqYK2K2w7LhrnmhHynchZlZzA==
-----END CERTIFICATE-----"""

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

    def get_historical_consumption_for_day(
            self, start_date: datetime, meter_id: int, mode: EnergaStatsModes,
            tariff_name: str | None = None
    ) -> EnergaStatisticsData:
        """Returns the historical consumption of the meter for the specified day"""
        return self._get_statistic_for_date(start_date, EnergaStatsTypes.DAY, meter_id, mode, tariff_name)

    def get_first_historical_consumption_for_type(self, start_date: datetime, meter_id: int, mode: EnergaStatsModes,
                                                  stat_type: EnergaStatsTypes) -> datetime | None:
        """Returns the first historical consumption of the meter for the specified type"""
        current_period = start_date
        result: datetime | None = None
        retries = 0
        try:
            while retries < 10:
                retries += 1
                _LOGGER.debug('Searching for the first %s statistic in the period %s (%s)', stat_type.value,
                              current_period.strftime('%Y/%m/%d'), int(current_period.timestamp()) * 1000)
                response = self._get_statistic_for_date(
                    current_period.replace(hour=0, minute=0, second=0, microsecond=0), stat_type, meter_id, mode)
                tz = dt_util.get_time_zone(response.timezone)

                if len(response.historical_points) == 0:
                    _LOGGER.debug(
                        "No historical points found in this period. The previous one contained the result: %s",
                        result.strftime('%Y/%m/%d')
                    )
                    break

                non_empty = response.get_first_non_empty_stat()
                if non_empty:
                    result = non_empty.get_date(tz=tz)
                    _LOGGER.debug("A new first non-empty %s statistic found for %s.", stat_type.value,
                                  result.strftime('%Y/%m/%d'))

                # Check the previous results if possible
                first_stat = response.historical_points[0]
                first_date = first_stat.get_date(tz=tz)
                if stat_type == EnergaStatsTypes.DAY:
                    current_period = first_date - timedelta(days=1)
                elif stat_type == EnergaStatsTypes.WEEK:
                    current_period = first_date - timedelta(days=7)
                elif stat_type == EnergaStatsTypes.MONTH:
                    last_day_of_previous_month = first_date - timedelta(days=1)
                    current_period = last_day_of_previous_month.replace(day=1)
                else:
                    last_day_of_previous_year = first_date - timedelta(days=1)
                    current_period = last_day_of_previous_year.replace(day=1, month=1)

            if result:
                _LOGGER.debug(
                    'The first found %s statistic is %s',
                    stat_type.value, result.strftime('%Y/%m/%d')
                )
                return result
            return None

        except (HTTPError, urllib.error.URLError) as error:
            _LOGGER.error('Got an error response from the energa website when getting historical stats %s (id: %s): %s',
                          ENERGA_HISTORICAL_DATA_URL, meter_id, error)
            raise EnergaWebsiteLoadingError from error

    def _get_statistic_for_date(self, start_date: datetime, stat_type: EnergaStatsTypes, meter_id: int,
                                mode: EnergaStatsModes, tariff_name: str | None = None) -> EnergaStatisticsData:
        """Returns the data returned by Energa when asking for a specific statistic period"""
        try:
            request_data = {
                'mainChartDate': int(start_date.timestamp() * 1000),
                'type': stat_type.value,
                'meterPoint': meter_id,
                'mo': mode.value
            }
            if tariff_name:
                request_data['tariffName'] = tariff_name
            request = mechanize.Request(url=ENERGA_HISTORICAL_DATA_URL, method='GET', data=request_data)
            response = self._browser.open(request, timeout=ENERGA_REQUESTS_TIMEOUT)
            json_response = response.read()
            result = json.loads(json_response)
            if result is None or not result.get('success'):
                raise EnergaStatisticsCouldNotBeLoadedError
            return EnergaStatisticsData(result.get('response'))
        except (HTTPError, urllib.error.URLError) as error:
            _LOGGER.error('Got an error response from the energa website %s (id: %s): %s',
                          ENERGA_HISTORICAL_DATA_URL, meter_id, error)
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

    def open_home_page(self, meter_id: int | None = None, ppe: int | None = None):
        """Opens the main view of Energa My Meter that contains most of the information"""
        request_data = {}
        if meter_id and ppe:
            request_data['mpc'] = meter_id
            request_data['ppe'] = ppe
        request = mechanize.Request(url=ENERGA_MY_METER_DATA_URL, method='GET', data=request_data)
        html_result = self._open_page(request)
        self._verify_logged_in(html_result)
        return html_result

    def open_account_page(self):
        """Opens the main view of Energa My Meter that contains the list of meters configured for the account"""
        request = mechanize.Request(url=ENERGA_ACCOUNT_DATA_URL, method='GET')
        html_result = self._open_page(request)
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
            _LOGGER.error('Got an error response from the energa website %s: %s', url, error)
            hdrs = getattr(error, 'headers', None) or error.info()
            _LOGGER.error("HTTP %s on %s; Location=%s; Set-Cookie=%s",
                          error.code, url, hdrs.get('Location'), hdrs.get('Set-Cookie'))

            raise EnergaWebsiteLoadingError from error
        result = self._parse_response(html_response)

        if EnergaWebsiteScrapper.is_error_shown(html=result):
            _LOGGER.warning("The Energa website is currently showing an error on the page")
            raise EnergaMyMeterWebsiteError
        return result

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
        browser.set_handle_redirect(True)
        browser.set_ca_data(cadata=ENERGA_CERT)
        return browser


