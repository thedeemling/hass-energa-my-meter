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
ENERGA_CA_CERTIFICATES = """-----BEGIN CERTIFICATE-----
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
el23wRxXFIL7DPC9VE11xA==
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIFwDCCA6igAwIBAgIQHr9ZULjJgDdMBvfrVU+17TANBgkqhkiG9w0BAQ0FADB6
MQswCQYDVQQGEwJQTDEhMB8GA1UEChMYQXNzZWNvIERhdGEgU3lzdGVtcyBTLkEu
MScwJQYDVQQLEx5DZXJ0dW0gQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkxHzAdBgNV
BAMTFkNlcnR1bSBUcnVzdGVkIFJvb3QgQ0EwHhcNMTgwMzE2MTIxMDEzWhcNNDMw
MzE2MTIxMDEzWjB6MQswCQYDVQQGEwJQTDEhMB8GA1UEChMYQXNzZWNvIERhdGEg
U3lzdGVtcyBTLkEuMScwJQYDVQQLEx5DZXJ0dW0gQ2VydGlmaWNhdGlvbiBBdXRo
b3JpdHkxHzAdBgNVBAMTFkNlcnR1bSBUcnVzdGVkIFJvb3QgQ0EwggIiMA0GCSqG
SIb3DQEBAQUAA4ICDwAwggIKAoICAQDRLY67tzbqbTeRn06TpwXkKQMlzhyC93yZ
n0EGze2jusDbCSzBfN8pfktlL5On1AFrAygYo9idBcEq2EXxkd7fO9CAAozPOA/q
p1x4EaTByIVcJdPTsuclzxFUl6s1wB52HO8AU5853BSlLCIls3Jy/I2z5T4IHhQq
NwuIPMqw9MjCoa68wb4pZ1Xi/K1ZXP69VyywkI3C7Te2fJmItdUDmj0VDT06qKhF
8JVOJVkdzZhpu9PMMsmN74H+rX2Ju7pgE8pllWeg8xn2A1bUatMn4qGtg/BKEiJ3
HAVz4hlxQsDsdUaakFjgao4rpUYwBI4Zshfjvqm6f1bxJAPXsiEodg42MEx51UGa
mqi4NboMOvJEGyCI98Ul1z3G4z5D3Yf+xOr1Uz5MZf87Sst4WmsXXw3Hw09Omiqi
7VdNIuJGmj8PkTQkfVXjjJU30xrwCSss0smNtA0Aq2cpKNgB9RkEth2+dv5yXMSF
ytKAQd8FqKPVhJBPC/PgP5sZ0jeJP/J7UhyM9uH3PAeXjA6iWYEMspA90+NZRu0P
qafegGtaqge2Gcu8V/OXIXoMsSt0Puvap2ctTMSYnjYJdmZm/Bo/6khUHL4wvYBQ
v3y1zgD2DGHZ5yQD4OMBgQ692IU0iL2yNqh7XAjlRICMb/gv1SHKHRzQ+8S1h9E6
Tsd2tTVItQIDAQABo0IwQDAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBSM+xx1
vALTn04uSNn5YFSqxLNP+jAOBgNVHQ8BAf8EBAMCAQYwDQYJKoZIhvcNAQENBQAD
ggIBAEii1QALLtA/vBzVtVRJHlpr9OTy4EA34MwUe7nJ+jW1dReTagVphZzNTxl4
WxmB82M+w85bj/UvXgF2Ez8sALnNllI5SW0ETsXpD4YN4fqzX4IS8TrOZgYkNCvo
zMrnadyHncI013nR03e4qllY/p0m+jiGPp2Kh2RX5Rc64vmNueMzeMGQ2Ljdt4NR
5MTMI9UGfOZR0800McD2RrsLrfw9EAUqO0qRJe6M1ISHgCq8CYyqOhNf6DR5UMEQ
GfnTKB7U0VEwKbOukGfWHwpjscWpxkIxYxeU72nLL/qMFH3EQxiJ2fAyQOaA4kZf
5ePBAFmo+eggvIksDkc0C+pXwlM2/KfUrzHN/gLldfq5Jwn58/U7yn2fqSLLiMmq
0Uc9NneoWWRrJ8/vJ8HjJLWG965+Mk2weWjROeiQWMODvA8s1pfrzgzhIMfatz7D
P78v3DSk+yshzWePS/Tj6tQ/50+6uaWTRRxmHyH6ZF5v4HaUMst19W7l9o/HuKTM
qJZ9ZPskWkoDbGs4xugDQ5r3V7mzKWmTOPQD8rv7gmsHINFSH5pkAnuYZttcTVoP
0ISVoDwUQwbKytu4QTbaakRnh6+v40URFWkIsr4WOZckbxJF0WddCajJFdr60qZf
E2Efv4WstK2tBZQIgx51F9NxO5NQI1mg7TyRVJ12AMXDuDjb
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
            if isinstance(error, HTTPError):
                hdrs = error.headers
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
        browser.set_ca_data(cadata=ENERGA_CA_CERTIFICATES)
        return browser
