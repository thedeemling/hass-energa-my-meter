"""Testing the logic of interacting with the client of Energa My Meter Website"""

from unittest.mock import patch

import pytest
from lxml import etree

from custom_components.energa_my_meter.energa.client import EnergaMyMeterClient
from custom_components.energa_my_meter.energa.data import EnergaData
from custom_components.energa_my_meter.energa.errors import EnergaNoSuitableMetersFoundError, EnergaWebsiteLoadingError


@patch(
    target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.authenticate'
)
def test_open_connection(connector_mock):
    """Testing the open connection"""
    client = EnergaMyMeterClient()
    username = 'username'
    password = 'password'
    client.open_connection(username, password)
    connector_mock.assert_called_once_with(username, password)


@patch(
    target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.disconnect'
)
def test_closing_connection(connector_mock):
    """Testing the closing connection"""
    client = EnergaMyMeterClient()
    client.disconnect()
    connector_mock.assert_called_once()


@patch(
    target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.open_account_page',
    return_value=etree.fromstring('<html><body><p>Not logged in</p></body></html>'),
)
@patch(
    target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_meters',
    return_value=[],
)
def test_get_meters_when_user_does_not_have_any_meters_should_raise_error(_connector_mock, _scrapper_mock):
    """Testing the get_meters function that should raise an error when the user has no meters"""
    client = EnergaMyMeterClient()
    with pytest.raises(EnergaNoSuitableMetersFoundError):
        client.get_meters()


@patch(
    target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.open_account_page',
    return_value=etree.fromstring('<html><body><p>Any valid html</p></body></html>'),
)
@patch(
    target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_meters',
    return_value=[{'meter_id': '0', 'ppe': '0', 'meter_name': '0'}, {'meter_id': '1', 'ppe': '1', 'meter_name': '1'}],
)
def test_get_meters_should_return_meters_found_on_energa_page(_connector_mock, _scrapper_mock):
    """Testing the get_meters function that should return all the meters found"""
    expected_meters = [{'meter_id': '0', 'ppe': '0', 'meter_name': '0'},
                       {'meter_id': '1', 'ppe': '1', 'meter_name': '1'}]
    client = EnergaMyMeterClient()
    result = client.get_meters()
    assert expected_meters == result


@patch(
    target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.open_home_page',
    return_value=etree.fromstring('<html><body><p>Any valid html</p></body></html>'),
)
@patch(
    target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_meter_name',
    return_value=None,
)
def test_account_main_data_when_user_did_not_provide_valid_meter_should_raise_an_error(
        _connector_mock,
        _scrapper_mock
):
    """Testing the get_account_main_data that should raise an error when Energa returns invalid data"""
    client = EnergaMyMeterClient()
    with pytest.raises(EnergaWebsiteLoadingError):
        client.get_account_main_data()


@patch(
    target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.open_home_page',
    return_value=etree.fromstring('<html><body><p>Any valid html</p></body></html>'),
)
def test_account_main_data_should_return_correct_data(_connector_mock):
    """Testing the get_account_main_data that should return the correct data"""
    expected_result: EnergaData = EnergaData({
        'seller': 'some seller',
        'client_type': 'some client',
        'contract_period': 'some period',
        'ppe_address': 'some address',
        'ppe_number': 'ppe number',
        'tariff': 'G18',
        'meter_name': 'test',
        'meter_readings': []
    })
    client = EnergaMyMeterClient()
    with (
        patch(
            target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_seller',
            return_value=expected_result.seller,
        ),
        patch(
            target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_client_type',
            return_value=expected_result.client_type,
        ),
        patch(
            target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_contract_period',
            return_value=expected_result.contract_period,
        ),
        patch(
            target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_meter_name',
            return_value=expected_result.meter_name,
        ),
        patch(
            target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_ppe_address',
            return_value=expected_result.ppe_address,
        ),
        patch(
            target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_ppe_number',
            return_value=expected_result.ppe_number,
        ),
        patch(
            target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_tariff',
            return_value=expected_result.tariff,
        )
    ):
        result: EnergaData = client.get_account_main_data()
        assert result == expected_result
