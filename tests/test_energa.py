import urllib
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import lxml.html
import pytest
from lxml import etree

from custom_components.energa_my_meter import EnergaMyCounterAuthorizationError, EnergaWebsiteLoadingError
from custom_components.energa_my_meter.energa.client import EnergaData
from custom_components.energa_my_meter.energa.client import EnergaMyMeterClient, EnergaWebsiteIntegration
from custom_components.energa_my_meter.energa.errors import EnergaNoSuitableMetersFoundError
from custom_components.energa_my_meter.energa.scrapper import EnergaWebsiteScrapper

TEST_DATA_DIR = Path(__file__).resolve().parent / 'data'


class TestEnergaMyCounterScrapper:
    """Testing the scrapping mechanism"""

    @pytest.fixture(autouse=True)
    def logged_in_html(self):
        """Fixture providing the logged in HTML example"""
        return etree.parse(TEST_DATA_DIR / 'logged_in.html', etree.HTMLParser())

    @pytest.fixture(autouse=True)
    def logged_out_html(self):
        """Fixture providing the logged out HTML example"""
        return etree.parse(TEST_DATA_DIR / 'logged_out.html', etree.HTMLParser())

    def test_user_is_logged_out(self, logged_out_html):
        """The scrapper should properly detect that the user is logged out"""
        expected = False
        result = EnergaWebsiteScrapper.is_logged_in(logged_out_html)
        assert result == expected

    def test_user_is_logged_in(self, logged_in_html):
        """The scrapper should properly detect that the user is logged in"""
        expected = True
        result = EnergaWebsiteScrapper.is_logged_in(logged_in_html)
        assert result == expected

    def test_getting_energy_used_when_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the value of the used energy when the user is logged in"""
        expected = 2933.013
        result = EnergaWebsiteScrapper.get_energy_used(html=logged_in_html)
        assert result == expected

    def test_get_last_update_when_the_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the time of the last energy value update when the user is logged in"""
        expected = datetime.strptime('2022-05-15 00:00', "%Y-%m-%d %H:%M")
        result = EnergaWebsiteScrapper.get_energy_used_last_update(logged_in_html)
        assert result == expected

    def test_get_ppe_number_when_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the number of PPE when the user is logged in"""
        expected = 123454777
        result = EnergaWebsiteScrapper.get_ppe_number(logged_in_html)
        assert result == expected

    def test_getting_seller_when_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the name of the contract seller when the user is logged in"""
        expected = 'ENERGA-Obrót SA'
        result = EnergaWebsiteScrapper.get_seller(logged_in_html)
        assert result == expected

    def test_getting_client_type_when_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the client type when the user is logged in"""
        expected = 'Odbiorca'
        result = EnergaWebsiteScrapper.get_client_type(logged_in_html)
        assert result == expected

    def test_getting_tariff_when_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the name of the currently used tariff when the user is logged in"""
        expected = 'G11'
        result = EnergaWebsiteScrapper.get_tariff(logged_in_html)
        assert result == expected

    def test_getting_ppe_address_when_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the address of PPE when the user is logged in"""
        expected = '11-111 City, Street 13/24'
        result = EnergaWebsiteScrapper.get_ppe_address(logged_in_html)
        assert result == expected

    def test_getting_meter_id_when_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the internal ID of the meter when the user is logged in"""
        meter_number = 12345656
        expected = 12345678
        result = EnergaWebsiteScrapper.get_meter_id(logged_in_html, meter_number)
        assert result == expected

    def test_getting_meter_number_when_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the number of the meter when the user is logged in"""
        expected = 12345656
        result = EnergaWebsiteScrapper.get_meter_number(logged_in_html)
        assert result == expected

    def test_getting_energy_produced_when_user_was_logged_in_and_there_is_no_produced_energy(self, logged_in_html):
        """The scrapper should be able to detect that there is no energy produced when the user is logged in"""
        expected = None
        result = EnergaWebsiteScrapper.get_energy_produced(logged_in_html)
        assert result == expected

    def test_getting_contract_period_when_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the contract period when the user is logged in"""
        expected = 'Od\xa02018-06-17'
        result = EnergaWebsiteScrapper.get_contract_period(logged_in_html)
        assert result == expected

    def test_getting_supported_meters_when_user_was_logged_in(self, logged_in_html):
        """The scrapper should be able to get the contract period when the user is logged in"""
        expected = {'12345678': {'counter_description': '12345656 (G11)'}}
        result = EnergaWebsiteScrapper.get_meters(logged_in_html)
        assert result == expected


class TestEnergaData:
    def test_converting_energa_data_from_dict(self):
        data = {
            'seller': 'Some seller',
            'client_type': 'Client type',
            'contract_period': 'Contract period',
            'energy_used': 120,
            'energy_used_last_update': datetime.now(),
            'energy_produced': 121,
            'meter_id': 123,
            'ppe_address': 'Some address',
            'ppe_number': 124,
            'tariff': 'Some tariff',
            'meter_number': 125,
        }
        result = EnergaData(data)

        assert data['seller'] == result.seller
        assert data['client_type'] == result.client_type
        assert data['contract_period'] == result.contract_period
        assert data['energy_used'] == result.energy_used
        assert data['energy_used_last_update'] == result.energy_used_last_update
        assert data['energy_produced'] == result.energy_produced
        assert data['meter_id'] == result.meter_id
        assert data['ppe_address'] == result.ppe_address
        assert data['ppe_number'] == result.ppe_number
        assert data['tariff'] == result.tariff
        assert data['meter_number'] == result.meter_number


class TestEnergaMyMeterClient:
    """Testing the logic of interacting with the Energa My Meter Website"""

    @pytest.fixture(autouse=True)
    def energa_data_scrapping_mock(self):
        base_class = 'custom_components.energa_my_meter.energa.client.EnergaMyCounterScrapper'
        with patch(f'{base_class}.get_seller', lambda x: 'Seller'), \
                patch(f'{base_class}.get_client_type', lambda x: 'Client type'), \
                patch(f'{base_class}.get_contract_period', lambda x: 'Contract period'), \
                patch(f'{base_class}.get_energy_used', lambda x: 0), \
                patch(f'{base_class}.get_energy_used_last_update', lambda x: datetime.now()), \
                patch(f'{base_class}.get_energy_produced', lambda x: 0), \
                patch(f'{base_class}.get_meter_id', lambda x, y: 1), \
                patch(f'{base_class}.get_ppe_address', lambda x: 'PPE address'), \
                patch(f'{base_class}.get_ppe_number', lambda x: 1), \
                patch(f'{base_class}.get_tariff', lambda x: 'Tariff'), \
                patch(f'{base_class}.get_tariff', lambda x: 1):
            yield

    @patch('custom_components.energa_my_meter.energa.client.EnergaWebsiteIntegration.get_meter_data',
           return_value=lxml.html.fromstring('<html><body><p>empty</p></body></html>'))
    async def test_getting_user_data_when_user_is_not_logged_in(
            self, get_meter_data_mock: MagicMock, hass
    ):
        """The client should detect that the user is not logged in"""
        username = 'username'
        password = 'password'

        client = EnergaMyMeterClient(hass)
        with pytest.raises(EnergaMyCounterAuthorizationError):
            await client.get_meters(username, password)

        get_meter_data_mock.assert_called_once_with(username, password)

    @patch('custom_components.energa_my_meter.energa.client.EnergaWebsiteIntegration.get_meter_data',
           side_effect=urllib.error.URLError(reason='test'))
    async def test_getting_user_data_when_connection_to_energa_is_not_working(
            self, get_meter_data_mock: MagicMock, hass
    ):
        """The client should return detect that there was an error connecting to the Energa website"""
        username = 'username'
        password = 'password'

        client = EnergaMyMeterClient(hass)
        with pytest.raises(EnergaWebsiteLoadingError):
            await client.get_meters(username, password)

        get_meter_data_mock.assert_called_once_with(username, password)

    @patch('custom_components.energa_my_meter.energa.client.EnergaWebsiteIntegration.get_meter_data',
           return_value=None)
    async def test_getting_user_data_when_getting_website_html_did_not_work(
            self, get_meter_data_mock: MagicMock, hass
    ):
        """The client should detect that there was a problem getting the HTML of the Energa website"""
        username = 'username'
        password = 'password'

        client = EnergaMyMeterClient(hass)
        with pytest.raises(EnergaWebsiteLoadingError):
            await client.get_meters(username, password)

        get_meter_data_mock.assert_called_once_with(username, password)

    @patch('custom_components.energa_my_meter.energa.client.EnergaMyCounterScrapper.get_meters',
           return_value=[{'1212345': {'counter_description': 'description'}}])
    @patch('custom_components.energa_my_meter.energa.client.EnergaMyMeterClient._login')
    async def test_getting_user_meters_when_the_user_is_logged_in(
            self, login_mock: MagicMock, get_meters_mock: MagicMock, hass
    ):
        """The client should return all found meters on the website if the user is logged in"""
        expected = [{'1212345': {'counter_description': 'description'}}]

        client = EnergaMyMeterClient(hass)
        result = await client.get_meters('username', 'password')

        assert expected == result
        get_meters_mock.assert_called_once()
        login_mock.assert_called_once_with('username', 'password')

    @patch('custom_components.energa_my_meter.energa.client.EnergaMyCounterScrapper.get_meters', return_value=[])
    @patch('custom_components.energa_my_meter.energa.client.EnergaMyMeterClient._login')
    async def test_getting_user_meters_when_the_user_is_logged_in_but_has_no_smart_meters(
            self, login_mock: MagicMock, get_meters_mock: MagicMock, hass
    ):
        """The client should detect that the user has no smart meters configured on his account"""
        client = EnergaMyMeterClient(hass)
        with pytest.raises(EnergaNoSuitableMetersFoundError):
            await client.get_meters('username', 'password')

        get_meters_mock.assert_called_once()
        login_mock.assert_called_once_with('username', 'password')

    @patch('custom_components.energa_my_meter.energa.client.EnergaMyCounterScrapper.get_meter_number', return_value=1)
    @patch('custom_components.energa_my_meter.energa.client.EnergaWebsiteIntegration.get_meter_data')
    @patch('custom_components.energa_my_meter.energa.client.EnergaMyCounterScrapper.is_logged_in', return_value=True)
    async def test_gathering_meter_data_when_the_user_is_logged_in(
            self, is_logged_in_mock: MagicMock, get_meter_data_mock: MagicMock, get_meter_number_mock: MagicMock, hass
    ):
        """The client should properly gather meter data when the user is logged in"""
        client = EnergaMyMeterClient(hass)
        result = await client.get_account_main_data('username', 'password')

        get_meter_data_mock.assert_called_once_with('username', 'password')
        is_logged_in_mock.assert_called_once()
        get_meter_number_mock.assert_called_once()

        assert result is not None
        assert result.meter_number == 1

    @patch('custom_components.energa_my_meter.energa.client.EnergaMyCounterScrapper.get_meter_number',
           return_value=None)
    @patch('custom_components.energa_my_meter.energa.client.EnergaMyMeterClient._login')
    async def test_gathering_meter_data_when_the_user_is_logged_in_but_meter_number_could_not_be_found(
            self, login_mock: MagicMock, get_meter_number_mock: MagicMock, hass
    ):
        """The client should detect an error when getting the meter number from the website"""
        client = EnergaMyMeterClient(hass)
        with pytest.raises(EnergaWebsiteLoadingError):
            await client.get_account_main_data('username', 'password')

        login_mock.assert_called_once_with('username', 'password')
        get_meter_number_mock.assert_called_once()


class TestEnergaWebsiteIntegration:
    """Test class with the website integration functionality"""

    @pytest.fixture(autouse=True)
    def mocked_response(self):
        mocked_response = AsyncMock()
        mocked_response.read = lambda: '<html><body>EMPTY</body></html>'
        mocked_response.getcode = lambda: 200
        mocked_response.geturl = lambda: 'http://url'

        return mocked_response

    @pytest.fixture(autouse=True)
    def mocked_browser(self):
        mocked_browser = AsyncMock()
        mocked_browser.form = {}
        return mocked_browser

    def test_getting_browser(self, hass):
        """Testing the browser creation"""
        integrator = EnergaWebsiteIntegration(hass)
        result = integrator.browser
        assert result is not None

    async def test_opening_energa_website(self, hass, mocked_response: MagicMock):
        """Opening Energa website should return a proper response object"""
        integrator = EnergaWebsiteIntegration(hass)
        with patch('mechanize.Browser.open', return_value=mocked_response):
            result = await integrator.authenticate()
            result_html = lxml.html.tostring(result)
            assert result_html == b'<html><body>EMPTY</body></html>'

    async def test_authorizing_user(self, hass, mocked_response: MagicMock, mocked_browser: MagicMock):
        """Authorizing user should setup form fields"""
        username = 'username'
        password = 'password'

        integrator = EnergaWebsiteIntegration(hass)
        integrator.browser = mocked_browser
        mocked_browser.open = lambda url, timeout: mocked_response
        mocked_browser.submit = lambda: mocked_response
        mocked_browser.select_form = lambda id: MagicMock()

        await integrator.authenticate(username, password)

        assert mocked_browser.form == {'j_username': username, 'j_password': password}
