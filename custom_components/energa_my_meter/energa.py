"""
Base integration with the Energa My meter website
"""

from enum import Enum
import logging
import urllib
from datetime import datetime
import json
import mechanize
from lxml.html.soupparser import fromstring

from .errors import (
    EnergaMyCounterAuthorizationError,
    EnergaWebsiteLoadingError,
    EnergaNoSuitableCountersFoundError, EnergaHistoricalDataGatheringError
)

from .const import (
    ENERGA_MY_METER_DATA_URL,
    ENERGA_MY_METER_HISTORICAL_DATA_URL,
    ENERGA_REQUESTS_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class EnergaHistoricalDataType(Enum):
    """
    Enum with all possible data types presented on the historical data graph.
    Each type changes the resolution of the graph with the DAY being the most detailed.
    """
    YEAR = 'YEAR'
    MONTH = 'MONTH'
    WEEK = 'WEEK'
    DAY = 'DAY'


class EnergaData:
    """Representation of the data gathered from the Energa website"""

    def __init__(self, data: dict):
        self._data: dict = data
        self._data['historical_data'] = {}

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

    def get_historical_data(self, data_type=EnergaHistoricalDataType):
        """Returns gathered historical data for the specific data type"""
        return self._data['historical_data'].get(data_type)

    def add_historical_data(self, data, data_type=EnergaHistoricalDataType.DAY):
        """
            Adds the historical data of the specified type converting it to the proper objects.
            This method is still unfinished.
        """

        if not self._data['historical_data'].get(data_type.value):
            self._data['historical_data'][data_type.value] = {}

        historical_date_start = data['response']['mainChartDate']
        self._data['historical_data'][data_type.value][historical_date_start] = data['response']

    def __getitem__(self, items):
        return self._data.__getitem__(items)


class EnergaMyCounterScrapper:
    """Class with static members containing XPath logic that gathers the data from the Energa HTMLs"""

    @staticmethod
    def get_text_value_by_xpath(html, xpath) -> str:
        """Returns normalized value string if xpath expression was found correctly"""
        result_raw = html.xpath(xpath)
        return None if not result_raw or len(result_raw) == 0 else ''.join(result_raw).strip()

    @staticmethod
    def get_detail_info(html, detail_name) -> str:
        """Helper method to get a specific detail from the details part of the website"""
        xpath = ('//div[@id="content"]//div[@id="left"]/div[@class="detailsInfo"]/'
                 + 'div/span/b[text()="{detail_name}"]/../../text()').format(
            detail_name=detail_name
        )
        return EnergaMyCounterScrapper.get_text_value_by_xpath(html, xpath)

    @staticmethod
    def parse_as_number(text) -> int:
        """Converts string to int if string is not null"""
        return None if not text else int(text)

    @staticmethod
    def parse_as_float(text) -> float:
        """Converts string to float if string is not null"""
        return None if not text else float(text.replace(',', '.'))

    @staticmethod
    def parse_as_date(text) -> datetime:
        """Converts string to date object of specific format if string is not null"""
        return None if not text else datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")

    @staticmethod
    def get_energy_used(html) -> float:
        """Returns the value of the energy used from Energa HTML website"""
        xpath = '//div[@id="content"]//div[@id="right"]/table//tr[1]/td[@class="last"]/span/text()'
        result_str = EnergaMyCounterScrapper.get_text_value_by_xpath(html, xpath)
        return EnergaMyCounterScrapper.parse_as_float(result_str)

    @staticmethod
    def get_energy_used_last_update(html) -> datetime:
        """Returns the last time the value of the energy was updated by Energa"""
        xpath = '//div[@id="content"]//div[@id="right"]/table//tr[1]/td[@class="first"]/div[2]/text()'
        result_str = EnergaMyCounterScrapper.get_text_value_by_xpath(html, xpath)
        return EnergaMyCounterScrapper.parse_as_date(result_str)

    @staticmethod
    def get_energy_produced(html) -> float:
        """Returns the value of the energy produced from Energa HTML website"""
        xpath = '//div[@id="content"]//div[@id="right"]/table//tr[3]/td[@class="last"]/span/text()'
        result_str = EnergaMyCounterScrapper.get_text_value_by_xpath(html, xpath)
        return EnergaMyCounterScrapper.parse_as_float(result_str)

    @staticmethod
    def get_ppe_number(html) -> int:
        """Returns the number of the PPE from Energa HTML website"""
        number_str = EnergaMyCounterScrapper.get_detail_info(html, 'Numer PPE')
        return EnergaMyCounterScrapper.parse_as_number(number_str)

    @staticmethod
    def get_seller(html) -> str:
        """Returns the name of the seller from Energa HTML website"""
        return EnergaMyCounterScrapper.get_detail_info(html, 'Sprzedawca')

    @staticmethod
    def get_client_type(html) -> str:
        """Returns the client type from Energa HTML website"""
        return EnergaMyCounterScrapper.get_detail_info(html, 'Typ')

    @staticmethod
    def get_contract_period(html) -> str:
        """Returns the users contract period from Energa HTML website"""
        return EnergaMyCounterScrapper.get_detail_info(html, 'Okres umowy')

    @staticmethod
    def get_tariff(html) -> str:
        """Returns the name of meter's currently associated tariff from Energa HTML website"""
        xpath = ('//div[@id="content"]//div[@id="left"]/div[@class="detailsInfo"]/'
                 + 'div/span/b[text()="Taryfa"]/../../span/text()')
        return EnergaMyCounterScrapper.get_text_value_by_xpath(html, xpath)

    @staticmethod
    def get_ppe_address(html) -> str:
        """Returns the address of the PPE from Energa HTML website"""
        xpath = ('//div[@id="content"]//div[@id="left"]/div[@class="detailsInfo"]/'
                 + 'div/span/b[text()="Adres PPE"]/../../div/text()')
        return EnergaMyCounterScrapper.get_text_value_by_xpath(html, xpath)

    @staticmethod
    def get_meter_id(html, meter_number) -> int:
        """
        Returns the internal meters ID used on Energa HTML website.
        This ID is normally hidden for the user and is only used in internal website calls
        """
        xpath = ('//form[@name="meterSelectForm"]/select[@name="meterSelectF"]/'
                 + 'option[contains(text(), "{meter_number}")]/@value').format(
            meter_number=meter_number
        )
        number_str = EnergaMyCounterScrapper.get_text_value_by_xpath(html, xpath)
        return EnergaMyCounterScrapper.parse_as_number(number_str)

    @staticmethod
    def get_meter_number(html) -> int:
        """Returns the number of the user's meter from Energa HTML website"""
        xpath = '//div[@id="content"]//div[@id="left"]//div[text()="Licznik"]/../b/text()'
        number_str = EnergaMyCounterScrapper.get_text_value_by_xpath(html, xpath)
        return EnergaMyCounterScrapper.parse_as_number(number_str)

    @staticmethod
    def get_user_counters_list(html):
        """Returns the list of the user's meters ({ID: description} objects) from Energa HTML website"""
        result = {}

        options = html.findall('.//form[@name="meterSelectForm"]/select[@name="meterSelectF"]/option')

        for option in options:
            meter_id = option.xpath('./@value')[0].strip()
            counter_description = option.xpath('./text()')[0].strip()

            result[meter_id] = {
                'counter_description': counter_description,
            }

        return result

    @staticmethod
    def is_logged_in(html) -> bool:
        """Returns true if the user is logged in"""
        login_form = html.xpath('//form[@id="loginForm"]')
        if login_form is None or len(login_form) == 0:
            return EnergaMyCounterScrapper.get_meter_number(html) is not None
        return False


class EnergaMyCounterClient:
    """Base logic of gathering the data from the Energa website - the order of requests and scraping the data"""

    def __init__(self, hass, username: str = None, password: str = None):
        self._hass = hass
        self._username = username
        self._password = password
        self._browser = None

    def update_credentials(self, username: str, password: str):
        """Stores new credentials used to authenticate on the Energa website"""
        self._username = username
        self._password = password

    async def get_user_counters(self):
        """Returns the list of counters found on the website for the specified user"""
        website = await self._login()

        counters_list = EnergaMyCounterScrapper.get_user_counters_list(website)

        if len(counters_list) == 0:
            raise EnergaNoSuitableCountersFoundError

        return counters_list

    async def gather_data(self) -> EnergaData:
        """Returns all useful data found on the main page of Energa website"""

        website = await self._login()

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

    async def get_historical_usage(
            self,
            meter_id: int,
            date_timestamp: int,
            data_type: EnergaHistoricalDataType = EnergaHistoricalDataType.DAY,
            browser=None
    ):
        """
        Returns historical data that can be found on the historical data graph.
        This method is still unfinished.
        """
        if not browser:
            logged_in = await self._login()
            browser = self._browser
            if not EnergaMyCounterScrapper.is_logged_in(logged_in['html']):
                raise EnergaMyCounterAuthorizationError

        url = (f'{ENERGA_MY_METER_HISTORICAL_DATA_URL}?mainChartDate={date_timestamp}'
               + f'&type={data_type.value}&meterPoint={meter_id}')

        _LOGGER.debug(
            'Getting historical data for type {%s} for meter {%s} and timestamp {%s}...',
            data_type, meter_id, date_timestamp
        )

        try:
            historical_data_response = await self._hass.async_add_executor_job(browser.open, url, None,
                                                                               ENERGA_REQUESTS_TIMEOUT)

            _LOGGER.debug(
                'Historical data response {%s} [{%s}]',
                historical_data_response.geturl(), historical_data_response.getcode()
            )

            historical_data = json.loads(historical_data_response.read())
        except mechanize.HTTPError as error:
            _LOGGER.error('Got an error response from the energa website {%s}: {%s}', url, error)
            raise EnergaWebsiteLoadingError from error
        except urllib.error.URLError as error:
            _LOGGER.error('Got a generic URLError when reaching Energa website {%s}: {%s}', url, error)
            raise EnergaWebsiteLoadingError from error
        except ValueError as error:
            raise EnergaMyCounterAuthorizationError from error

        if not historical_data or not historical_data['success']:
            _LOGGER.error('Error when gathering data for meter {%s}: {%s}', meter_id, historical_data)
            raise EnergaHistoricalDataGatheringError

        return historical_data

    @property
    def browser(self):
        """Returns the internal browser object used to get the Energa website."""
        return self._browser

    async def _login(self):
        """The logic of authenticating into the Energa website. Returns the HTML after being logged in."""
        browser = mechanize.Browser()
        browser.set_handle_robots(False)
        browser.set_handle_equiv(False)
        browser.set_handle_refresh(False)

        _LOGGER.debug('Logging into the Energa My Meter website {%s}...', ENERGA_MY_METER_DATA_URL)
        try:
            load_response = await self._hass.async_add_executor_job(browser.open, ENERGA_MY_METER_DATA_URL, None,
                                                                    ENERGA_REQUESTS_TIMEOUT)

            _LOGGER.debug('Load website response {%s} [{%s}]', load_response.geturl(), load_response.getcode())

            browser.select_form(id="loginForm")
            browser.form["j_username"] = self._username
            browser.form['j_password'] = self._password
            log_response = await self._hass.async_add_executor_job(browser.submit)

            _LOGGER.debug('Log in response {%s} [{%s}]', log_response.geturl(), log_response.getcode())

            html_result = fromstring(log_response.read())
            self._browser = browser
        except mechanize.HTTPError as error:
            _LOGGER.error('Got an error response from the energa website {%s}: {%s}', ENERGA_MY_METER_DATA_URL, error)
            raise EnergaWebsiteLoadingError from error
        except urllib.error.URLError as error:
            _LOGGER.error(
                'Got a generic URLError when reaching Energa website {%s}: {%s}',
                ENERGA_MY_METER_DATA_URL, error
            )
            raise EnergaWebsiteLoadingError from error

        if html_result is None:
            raise EnergaWebsiteLoadingError

        if not EnergaMyCounterScrapper.is_logged_in(html_result):
            raise EnergaMyCounterAuthorizationError

        return html_result
