"""Tests for the config flow."""
from unittest.mock import patch, MagicMock

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from custom_components.energa_my_meter import CONFIG_FLOW_SELECTED_METER_ID, CONFIG_FLOW_SELECTED_METER_NUMBER, \
    EnergaMyMeterAuthorizationError
from custom_components.energa_my_meter.config_flow import EnergaConfigFlow
from custom_components.energa_my_meter.const import CONFIG_FLOW_NUMBER_OF_DAYS_TO_LOAD
from helpers import decorate_home_assistant_mock


class TestYamlImport:
    @patch("custom_components.energa_my_meter.energa.client.EnergaMyMeterClient")
    @patch("custom_components.energa_my_meter.common.async_config_entry_by_username", return_value=False)
    @patch("homeassistant.config_entries.ConfigFlow.async_set_unique_id")
    @patch(
        target="custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.open_connection"
    )
    async def test_step_import_yaml_when_configuration_is_valid(
            self,
            open_connection_mock: MagicMock,
            _unique_id_mock: MagicMock,
            _config_entry_by_username_mock: MagicMock,
            _client_mock: MagicMock,
            hass: HomeAssistant,
    ) -> None:
        config_flow = EnergaConfigFlow()
        config_flow.hass = decorate_home_assistant_mock(hass)

        expected_result_data = {
            CONFIG_FLOW_NUMBER_OF_DAYS_TO_LOAD: 10,
            CONF_PASSWORD: 'somepassword',
            CONFIG_FLOW_SELECTED_METER_NUMBER: 2345,
            CONFIG_FLOW_SELECTED_METER_ID: 1234,
            CONF_USERNAME: 'someusername',
        }

        result = await config_flow.async_step_import({
            CONF_USERNAME: expected_result_data[CONF_USERNAME],
            CONF_PASSWORD: expected_result_data[CONF_PASSWORD],
            CONFIG_FLOW_SELECTED_METER_ID: expected_result_data[CONFIG_FLOW_SELECTED_METER_ID],
            CONFIG_FLOW_SELECTED_METER_NUMBER: expected_result_data[CONFIG_FLOW_SELECTED_METER_NUMBER]
        })

        assert result["type"] == "create_entry"
        assert result["title"] == "Energa someusername (2345)"
        assert result["data"] == expected_result_data
        open_connection_mock.assert_called_once()


class TestUIFlow:
    @patch("custom_components.energa_my_meter.energa.client.EnergaMyMeterClient")
    @patch("custom_components.energa_my_meter.common.async_config_entry_by_username", return_value=False)
    @patch("homeassistant.config_entries.ConfigFlow.async_set_unique_id")
    @patch(
        target="custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.open_connection"
    )
    @patch(
        target="custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.get_meters",
        return_value={'1234': {'meter_description': '1232133 12345'}}
    )
    async def test_when_user_input_is_valid(
            self,
            _get_meters_mock: MagicMock,
            _open_connection_mock: MagicMock,
            _unique_id_mock: MagicMock,
            _config_entry_by_username_mock: MagicMock,
            _client_mock: MagicMock,
            hass: HomeAssistant,
    ) -> None:
        config_flow = EnergaConfigFlow()
        config_flow.hass = decorate_home_assistant_mock(hass)

        expected_result_data = {
            CONFIG_FLOW_NUMBER_OF_DAYS_TO_LOAD: 100,
            CONF_PASSWORD: 'somepassword',
            CONFIG_FLOW_SELECTED_METER_NUMBER: '12345',
            CONFIG_FLOW_SELECTED_METER_ID: '1234',
            CONF_USERNAME: 'someusername',
        }

        user_result = await config_flow.async_step_user({
            CONF_USERNAME: expected_result_data[CONF_USERNAME],
            CONF_PASSWORD: expected_result_data[CONF_PASSWORD]
        })

        assert user_result.get('errors') == {}

        meters_result = await config_flow.async_step_meter({
            CONFIG_FLOW_SELECTED_METER_NUMBER: (
                expected_result_data[CONFIG_FLOW_SELECTED_METER_ID] + ',' +
                expected_result_data[CONFIG_FLOW_SELECTED_METER_NUMBER]
            ),
            CONFIG_FLOW_NUMBER_OF_DAYS_TO_LOAD: expected_result_data[CONFIG_FLOW_NUMBER_OF_DAYS_TO_LOAD]
        })

        assert meters_result["type"] == "create_entry"
        assert meters_result["data"] == expected_result_data
        assert meters_result["title"] == "Energa someusername (12345)"

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
            hass: HomeAssistant,
    ) -> None:
        config_flow = EnergaConfigFlow()
        config_flow.hass = decorate_home_assistant_mock(hass)

        user_result = await config_flow.async_step_user({
            CONF_USERNAME: 'some user',
            CONF_PASSWORD: 'some pass'
        })

        assert user_result.get('errors') == {'base': 'unauthorized'}
