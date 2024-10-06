from datetime import datetime
from pathlib import Path

import pytest
from lxml import etree

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

    @pytest.fixture(autouse=True)
    def captcha_error_html(self):
        """Fixture providing the logged out HTML example"""
        return etree.parse(TEST_DATA_DIR / 'captcha_error.html', etree.HTMLParser())

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

    def test_user_sees_captcha(self, captcha_error_html):
        """The scrapper should properly detect that the user sees captcha error"""
        expected = True
        result = EnergaWebsiteScrapper.is_captcha_shown(captcha_error_html)
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
        expected = {'12345678': {'meter_description': '12345656 (G11)'}}
        result = EnergaWebsiteScrapper.get_meters(logged_in_html)
        assert result == expected
