"""Testing the config flow of the integration"""
from unittest.mock import MagicMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.energa_my_meter import EnergaMyMeterAuthorizationError, EnergaWebsiteLoadingError, config_flow
from custom_components.energa_my_meter.const import (
    CONFIG_FLOW_ALREADY_CONFIGURED_ERROR,
    CONFIG_FLOW_NO_SUPPORTED_METERS_ERROR,
    CONFIG_FLOW_UNAUTHORIZED_ERROR,
    CONFIG_FLOW_UNKNOWN_ERROR,
)
from custom_components.energa_my_meter.energa.errors import EnergaNoSuitableMetersFoundError


@pytest.fixture(autouse=True)
def example_user_input():
    """Returns example configuration of the Energa My Meter config entry"""
    return {CONF_USERNAME: 'example@username', CONF_PASSWORD: 'ExampleP4$$w0rD'}


class TestYAMLImportedConfigFlow:
    """A class with tests for the config flow imported from YAML configuration"""

    async def test_importing_entries_from_yaml_should_detect_duplicates(self, hass, example_user_input):
        """User used YAML configuration, and it is using the credentials of an already configured account"""

        MockConfigEntry(
            domain=config_flow.DOMAIN,
            data={CONF_USERNAME: example_user_input[CONF_USERNAME], CONF_PASSWORD: example_user_input[CONF_PASSWORD]}
        ).add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            data=example_user_input,
            context={"source": config_entries.SOURCE_IMPORT},
        )

        assert result.get('type') == data_entry_flow.RESULT_TYPE_ABORT
        assert result.get('reason') == 'already_configured'

    @patch('custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.get_meters',
           return_value=[])
    async def test_configuring_scanning_interval_in_yaml_should_remember_settings(
            self, get_meters_mock, hass, example_user_input
    ):
        """When user defines scanning interval in YAML configuration it should be used to set up the entry"""
        scan_interval = 123
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            data={
                CONF_USERNAME: example_user_input[CONF_USERNAME],
                CONF_PASSWORD: example_user_input[CONF_PASSWORD],
                CONF_SCAN_INTERVAL: scan_interval
            },
            context={"source": config_entries.SOURCE_IMPORT},
        )

        get_meters_mock.assert_called_once_with(example_user_input[CONF_USERNAME], example_user_input[CONF_PASSWORD])
        assert result.get('type') == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result.get('options') == {CONF_SCAN_INTERVAL: scan_interval}


class TestUserConfigFlow:
    """A class with tests for config flow initialized by the user"""

    async def test_user_providing_no_input_should_display_empty_form(self, hass):
        """User initiated an empty form"""
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result.get('type') == data_entry_flow.RESULT_TYPE_FORM
        assert result.get('step_id') == config_entries.SOURCE_USER

    async def test_installing_already_configured_user_entry_should_detect_duplicate(self, hass, example_user_input):
        """User provided credentials which were already configured - the system should display an error"""
        MockConfigEntry(
            domain=config_flow.DOMAIN,
            data={CONF_USERNAME: example_user_input[CONF_USERNAME], CONF_PASSWORD: example_user_input[CONF_PASSWORD]}
        ).add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            data=example_user_input,
            context={"source": config_entries.SOURCE_USER},
        )

        assert result.get('errors') == {'base': CONFIG_FLOW_ALREADY_CONFIGURED_ERROR}

    @patch('custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.get_meters',
           side_effect=EnergaMyMeterAuthorizationError)
    async def test_providing_user_input_should_validate_authentication(
            self,
            get_meters_mock: MagicMock,
            hass,
            example_user_input
    ):
        """User provided invalid credentials in the flow - the system should present an error"""

        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            data=example_user_input,
            context={"source": config_entries.SOURCE_USER},
        )

        get_meters_mock.assert_called_once_with(example_user_input[CONF_USERNAME], example_user_input[CONF_PASSWORD])
        assert result.get('errors') == {'base': CONFIG_FLOW_UNAUTHORIZED_ERROR}

    @patch('custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.get_meters',
           side_effect=EnergaWebsiteLoadingError)
    async def test_error_getting_energa_website_should_result_in_error(
            self, get_meters_mock: MagicMock, hass, example_user_input
    ):
        """Energa website connection did not work correctly - the system should present an error"""
        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            data=example_user_input,
            context={"source": config_entries.SOURCE_USER},
        )

        get_meters_mock.assert_called_once_with(example_user_input[CONF_USERNAME], example_user_input[CONF_PASSWORD])
        assert result.get('errors') == {'base': CONFIG_FLOW_UNKNOWN_ERROR}

    @patch('custom_components.energa_my_meter.energa.client.EnergaMyMeterClient.get_meters',
           side_effect=EnergaNoSuitableMetersFoundError)
    async def test_no_supported_meters_should_result_in_error(
            self,
            get_meters_mock: MagicMock,
            hass,
            example_user_input
    ):
        """User has no smart meters configured on this account - the system should present an error"""

        result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN,
            data=example_user_input,
            context={"source": config_entries.SOURCE_USER},
        )

        get_meters_mock.assert_called_once_with(example_user_input[CONF_USERNAME], example_user_input[CONF_PASSWORD])
        assert result.get('errors') == {'base': CONFIG_FLOW_NO_SUPPORTED_METERS_ERROR}

# class TestOptionsConfigFlow:
#     """Class containing tests for setting up the options"""
#
#     async def test_setting_up_entry(self, hass, example_user_input):
#         MockConfigEntry(
#             domain=config_flow.DOMAIN,
#             data={CONF_USERNAME: example_user_input[CONF_USERNAME], CONF_PASSWORD: example_user_input[CONF_PASSWORD]},
#             options={}
#         ).add_to_hass(hass)
#
