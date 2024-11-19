"""Testing the scrapping mechanism"""
from datetime import datetime

from custom_components.energa_my_meter.energa.scrapper import EnergaWebsiteScrapper


def test_user_is_logged_out(logged_out_html):
    """The scrapper should properly detect that the user is logged out"""
    expected = False
    result = EnergaWebsiteScrapper.is_logged_in(logged_out_html)
    assert result == expected


def test_user_is_logged_in(logged_in_html):
    """The scrapper should properly detect that the user is logged in"""
    expected = True
    result = EnergaWebsiteScrapper.is_logged_in(logged_in_html)
    assert result == expected


def test_user_sees_captcha(captcha_error_html):
    """The scrapper should properly detect that the user sees captcha error"""
    expected = True
    result = EnergaWebsiteScrapper.is_captcha_shown(captcha_error_html)
    assert result == expected


def test_getting_energy_used_when_user_was_logged_in(logged_in_html):
    """The scrapper should be able to get the value of the used energy when the user is logged in"""
    expected = 2933.013
    result = EnergaWebsiteScrapper.get_energy_used(html=logged_in_html)
    assert result == expected


def test_get_last_update_when_the_user_was_logged_in(logged_in_html):
    """The scrapper should be able to get the time of the last energy value update when the user is logged in"""
    expected = datetime.strptime('2022-05-15 00:00', "%Y-%m-%d %H:%M")
    result = EnergaWebsiteScrapper.get_energy_used_last_update(logged_in_html)
    assert result == expected


def test_get_ppe_number_when_user_was_logged_in(logged_in_html):
    """The scrapper should be able to get the number of PPE when the user is logged in"""
    expected = 123454777
    result = EnergaWebsiteScrapper.get_ppe_number(logged_in_html)
    assert result == expected


def test_getting_seller_when_user_was_logged_in(logged_in_html):
    """The scrapper should be able to get the name of the contract seller when the user is logged in"""
    expected = 'ENERGA-Obrót SA'
    result = EnergaWebsiteScrapper.get_seller(logged_in_html)
    assert result == expected


def test_getting_client_type_when_user_was_logged_in(logged_in_html):
    """The scrapper should be able to get the client type when the user is logged in"""
    expected = 'Odbiorca'
    result = EnergaWebsiteScrapper.get_client_type(logged_in_html)
    assert result == expected


def test_getting_tariff_when_user_was_logged_in(logged_in_html):
    """The scrapper should be able to get the name of the currently used tariff when the user is logged in"""
    expected = 'G11'
    result = EnergaWebsiteScrapper.get_tariff(logged_in_html)
    assert result == expected


def test_getting_ppe_address_when_user_was_logged_in(logged_in_html):
    """The scrapper should be able to get the address of PPE when the user is logged in"""
    expected = '11-111 City, Street 13/24'
    result = EnergaWebsiteScrapper.get_ppe_address(logged_in_html)
    assert result == expected


def test_getting_meter_id_when_user_was_logged_in(logged_in_html):
    """The scrapper should be able to get the internal ID of the meter when the user is logged in"""
    meter_number = 12345656
    expected = 12345678
    result = EnergaWebsiteScrapper.get_meter_id(logged_in_html, meter_number)
    assert result == expected


def test_getting_meter_number_when_user_was_logged_in(logged_in_html):
    """The scrapper should be able to get the number of the meter when the user is logged in"""
    expected = '12345656'
    result = EnergaWebsiteScrapper.get_meter_name(logged_in_html)
    assert result == expected


def test_getting_energy_produced_when_user_was_logged_in_and_there_is_no_produced_energy(logged_in_html):
    """The scrapper should be able to detect that there is no energy produced when the user is logged in"""
    expected = None
    result = EnergaWebsiteScrapper.get_energy_produced(logged_in_html)
    assert result == expected


def test_getting_contract_period_when_user_was_logged_in(logged_in_html):
    """The scrapper should be able to get the contract period when the user is logged in"""
    expected = 'Od\xa02018-06-17'
    result = EnergaWebsiteScrapper.get_contract_period(logged_in_html)
    assert result == expected


def test_getting_supported_meters_when_user_was_logged_in(account_data_html):
    """The scrapper should be able to get the contract period when the user is logged in"""
    expected = [
        {'meter_id': '1111111111', 'meter_name': 'Some meter name', 'meter_number': '123456',
         'ppe': '12345678909876543'}
    ]
    result = EnergaWebsiteScrapper.get_meters(account_data_html)
    assert result == expected


def test_detecting_an_error_on_the_page(error_html):
    """The scrapper should be able to detect that the error was shown on the page"""
    result = EnergaWebsiteScrapper.is_error_shown(error_html)
    assert result
