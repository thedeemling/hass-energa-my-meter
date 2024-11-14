"""Tests for the config flow."""
import json
from unittest.mock import patch, MagicMock

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from custom_components.energa_my_meter import CONF_SELECTED_METER_ID, CONF_SELECTED_METER_NUMBER, \
    EnergaMyMeterAuthorizationError
from custom_components.energa_my_meter.config_flow import EnergaConfigFlow
from custom_components.energa_my_meter.const import CONF_NUMBER_OF_DAYS_TO_LOAD, CONF_SELECTED_MODES, \
    CONF_SELECTED_ZONES, CONF_SELECTED_METER_PPE, CONF_SELECTED_METER_NAME


@patch("custom_components.energa_my_meter.energa.client.EnergaMyMeterClient")
@patch("custom_components.energa_my_meter.common.async_config_entry_by_username", return_value=False)
@patch("homeassistant.config_entries.ConfigFlow.async_set_unique_id")
async def test_step_import_yaml_when_configuration_is_valid(
        _unique_id_mock: MagicMock,
        _config_entry_by_username_mock: MagicMock,
        _client_mock: MagicMock,
        hass_with_jobs_mock: HomeAssistant,
) -> None:
    """Loading a valid configuration from YAML should not raise any errors and should finish successfully."""
    config_flow = EnergaConfigFlow()
    config_flow.hass = hass_with_jobs_mock

    expected_result_data = {
        CONF_NUMBER_OF_DAYS_TO_LOAD: 10,
        CONF_PASSWORD: 'somepassword',
        CONF_SELECTED_METER_NUMBER: 2345,
        CONF_SELECTED_METER_ID: 1234,
        CONF_SELECTED_METER_PPE: 1234,
        CONF_USERNAME: 'someusername',
        CONF_SELECTED_ZONES: ['zone1'],
        CONF_SELECTED_MODES: ['ENERGY_PRODUCED']
    }

    result = await config_flow.async_step_import({
        CONF_USERNAME: expected_result_data[CONF_USERNAME],
        CONF_PASSWORD: expected_result_data[CONF_PASSWORD],
        CONF_SELECTED_METER_ID: expected_result_data[CONF_SELECTED_METER_ID],
        CONF_SELECTED_METER_NUMBER: expected_result_data[CONF_SELECTED_METER_NUMBER],
        CONF_SELECTED_METER_PPE: expected_result_data[CONF_SELECTED_METER_PPE],
        CONF_SELECTED_ZONES: ['zone1'],
        CONF_SELECTED_MODES: ['ENERGY_PRODUCED']
    })

    assert result["type"] == "create_entry"
    assert result["title"] == "Energa someusername (2345)"
    assert result["data"] == expected_result_data

class TestUIFlow:
    """Testing the UI flow"""

    @patch("custom_components.energa_my_meter.energa.client.EnergaMyMeterClient")
    @patch("custom_components.energa_my_meter.common.async_config_entry_by_username", return_value=False)
    @patch("homeassistant.config_entries.ConfigFlow.async_set_unique_id")
    @patch(
        target="custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.open_connection"
    )
    @patch(
        target="custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.disconnect"
    )
    @patch(
        target="custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.get_meters",
        return_value=[{'meter_id': '1234', 'meter_name': 'Some name', 'ppe': '123', 'meter_number': '111'}]
    )
    @patch(
        target="custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.get_supported_zones",
        return_value=['zone1']
    )
    async def test_when_user_input_is_valid(
            self,
            _get_supported_zones: MagicMock,
            _get_meters_mock: MagicMock,
            _open_connection_mock: MagicMock,
            _disconnect_mock: MagicMock,
            _unique_id_mock: MagicMock,
            _config_entry_by_username_mock: MagicMock,
            _client_mock: MagicMock,
            hass_with_jobs_mock: HomeAssistant,
    ) -> None:
        """Loading the valid configuration from UI should finish successfully."""
        config_flow = EnergaConfigFlow()
        config_flow.hass = hass_with_jobs_mock

        expected_result_data = {
            CONF_NUMBER_OF_DAYS_TO_LOAD: 100,
            CONF_PASSWORD: 'somepassword',
            CONF_SELECTED_METER_NUMBER: '111',
            CONF_SELECTED_METER_PPE: '123',
            CONF_SELECTED_METER_ID: '1234',
            CONF_USERNAME: 'someusername',
            CONF_SELECTED_ZONES: ['zone1'],
            CONF_SELECTED_MODES: ['ENERGY_PRODUCED'],
            CONF_SELECTED_METER_NAME: 'My meter'
        }

        user_result = await config_flow.async_step_user({
            CONF_USERNAME: expected_result_data[CONF_USERNAME],
            CONF_PASSWORD: expected_result_data[CONF_PASSWORD]
        })

        assert user_result.get('errors') == {}

        meters_result = await config_flow.async_step_meter({
            CONF_SELECTED_METER_NUMBER: json.dumps({
                'meter_name': expected_result_data[CONF_SELECTED_METER_NAME],
                'meter_id': expected_result_data[CONF_SELECTED_METER_ID],
                'meter_number': expected_result_data[CONF_SELECTED_METER_NUMBER],
                'ppe': expected_result_data[CONF_SELECTED_METER_PPE],
            })
        })

        assert meters_result.get('errors') == {}

        statistics_result = await config_flow.async_step_statistics({
            CONF_NUMBER_OF_DAYS_TO_LOAD: expected_result_data[CONF_NUMBER_OF_DAYS_TO_LOAD],
            CONF_SELECTED_ZONES: expected_result_data[CONF_SELECTED_ZONES],
            CONF_SELECTED_MODES: expected_result_data[CONF_SELECTED_MODES]
        })

        assert statistics_result["type"] == "create_entry"
        assert statistics_result["data"] == expected_result_data
        assert statistics_result["title"] == "Energa someusername (111)"

    @patch("custom_components.energa_my_meter.energa.client.EnergaMyMeterClient")
    @patch("custom_components.energa_my_meter.common.async_config_entry_by_username", return_value=False)
    @patch("homeassistant.config_entries.ConfigFlow.async_set_unique_id")
    @patch(
        target="custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.open_connection",
        side_effect=EnergaMyMeterAuthorizationError()
    )
    async def test_when_user_did_not_provide_valid_credentials(
            self,
            _open_connection_mock: MagicMock,
            _unique_id_mock: MagicMock,
            _config_entry_by_username_mock: MagicMock,
            _client_mock: MagicMock,
            hass_with_jobs_mock: HomeAssistant,
    ) -> None:
        """Loading configuration with invalid credentials should return an unauthorized flow error"""
        config_flow = EnergaConfigFlow()
        config_flow.hass = hass_with_jobs_mock

        user_result = await config_flow.async_step_user({
            CONF_USERNAME: 'some user',
            CONF_PASSWORD: 'some pass'
        })

        assert user_result.get('errors') == {'base': 'unauthorized'}
