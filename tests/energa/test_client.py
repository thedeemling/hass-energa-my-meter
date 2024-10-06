from unittest.mock import patch

from lxml.etree import fromstring

import pytest
from custom_components.energa_my_meter.energa.client import EnergaMyMeterClient
from custom_components.energa_my_meter.energa.data import EnergaData
from custom_components.energa_my_meter.energa.errors import EnergaNoSuitableMetersFoundError, EnergaWebsiteLoadingError


class TestEnergaMyMeterClient:
    """Testing the logic of interacting with the client of Energa My Meter Website"""

    @patch(
        target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.authenticate'
    )
    def test_open_connection(self, connector_mock):
        client = EnergaMyMeterClient()
        username = 'username'
        password = 'password'
        client.open_connection(username, password)
        connector_mock.assert_called_once_with(username, password)

    @patch(
        target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.disconnect'
    )
    def test_closing_connection(self, connector_mock):
        client = EnergaMyMeterClient()
        client.disconnect()
        connector_mock.assert_called_once()

    @patch(
        target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.open_home_page',
        return_value=fromstring('<html><body><p>Not logged in</p></body></html>'),
    )
    @patch(
        target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_meters',
        return_value=[],
    )
    def test_get_meters_when_user_does_not_have_any_meters_should_raise_error(self, _connector_mock, _scrapper_mock):
        client = EnergaMyMeterClient()
        with pytest.raises(EnergaNoSuitableMetersFoundError):
            client.get_meters()

    @patch(
        target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.open_home_page',
        return_value=fromstring('<html><body><p>Any valid html</p></body></html>'),
    )
    @patch(
        target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_meters',
        return_value=[0, 1, 2],
    )
    def test_get_meters_should_return_meters_found_on_energa_page(self, _connector_mock, _scrapper_mock):
        expected_meters = [0, 1, 2]
        client = EnergaMyMeterClient()
        result = client.get_meters()
        assert expected_meters == result

    @patch(
        target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.open_home_page',
        return_value=fromstring('<html><body><p>Any valid html</p></body></html>'),
    )
    @patch(
        target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_meter_number',
        return_value=None,
    )
    def test_account_main_data_when_user_did_not_provide_valid_meter_should_raise_an_error(
            self,
            _connector_mock,
            _scrapper_mock
    ):
        client = EnergaMyMeterClient()
        with pytest.raises(EnergaWebsiteLoadingError):
            client.get_account_main_data()

    @patch(
        target='custom_components.energa_my_meter.energa.connector.EnergaWebsiteConnector.open_home_page',
        return_value=fromstring('<html><body><p>Any valid html</p></body></html>'),
    )
    def test_account_main_data_should_return_correct_data(
            self,
            _connector_mock
    ):
        expected_result: EnergaData = EnergaData({
            'seller': 'some seller',
            'client_type': 'some client',
            'contract_period': 'some period',
            'energy_used': 12345,
            'energy_used_last_update': 12345,
            'energy_produced': 12345,
            'meter_id': 1,
            'ppe_address': 'some address',
            'ppe_number': 'ppe number',
            'tariff': 'G18',
            'meter_number': 2
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
                target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_energy_used',
                return_value=expected_result.energy_used,
            ),
            patch(
                target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper'
                       '.get_energy_used_last_update',
                return_value=expected_result.energy_used_last_update,
            ),
            patch(
                target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.get_energy_produced',
                return_value=expected_result.energy_produced,
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
            result: EnergaData = client.get_account_main_data(expected_result.meter_number, expected_result.meter_id)
            assert result == expected_result
