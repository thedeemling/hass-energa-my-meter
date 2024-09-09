"""
Adding the support for Home Assistant's GUI installation of the integration
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from custom_components.energa_my_meter.energa.client import EnergaMyMeterClient
from custom_components.energa_my_meter.energa.errors import (
    EnergaMyMeterAuthorizationError,
    EnergaNoSuitableMetersFoundError,
    EnergaWebsiteLoadingError,
)
from .common import async_config_entry_by_username
from .const import (
    CONFIG_FLOW_ALREADY_CONFIGURED_ERROR,
    CONFIG_FLOW_NO_SUPPORTED_METERS_ERROR,
    CONFIG_FLOW_UNAUTHORIZED_ERROR,
    CONFIG_FLOW_UNKNOWN_ERROR,
    DEFAULT_ENTRY_TITLE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN, CONFIG_FLOW_SELECTED_METER_NUMBER, CONFIG_FLOW_STEP_USER, CONFIG_FLOW_STEP_METER,
    CONFIG_FLOW_SELECTED_METER_ID,
)

_LOGGER = logging.getLogger(__name__)


class EnergaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configuration flow for setting up new entry."""
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._options: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return EnergaMyMeterOptionsFlowHandler(config_entry)

    async def async_step_import(self, user_input=None):
        """Handle a flow imported from YAML configuration"""

        if user_input is not None:
            self._data = {
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONFIG_FLOW_SELECTED_METER_ID: user_input[CONFIG_FLOW_SELECTED_METER_ID],
                CONFIG_FLOW_SELECTED_METER_NUMBER: user_input[CONFIG_FLOW_SELECTED_METER_NUMBER]
            }
            self._options = {CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL)}

            await self.async_set_unique_id(user_input[CONF_USERNAME])

            if async_config_entry_by_username(self.hass, user_input[CONF_USERNAME]):
                return self._async_abort_entries_match(
                    {CONF_USERNAME: user_input[CONF_USERNAME], CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )

            energa = EnergaMyMeterClient()
            try:
                await self.hass.async_add_executor_job(
                    energa.open_connection,
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD]
                )
                title = DEFAULT_ENTRY_TITLE.format(username=user_input[CONF_USERNAME])
                return self.async_create_entry(title=title, data=self._data, options=self._options)
            except EnergaWebsiteLoadingError:
                _LOGGER.exception('Could not load the Energa website')
            except EnergaMyMeterAuthorizationError:
                _LOGGER.exception(
                    'Could not log into the Energa website using provided credentials in the YAML config!')
            except EnergaNoSuitableMetersFoundError:
                _LOGGER.exception('Could not find any smart meter on the provided Energa account!')

        return self._async_abort_entries_match(
            {CONF_USERNAME: user_input[CONF_USERNAME], CONF_PASSWORD: user_input[CONF_PASSWORD]}
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""

        errors: Dict[str, str] = {}

        if user_input is not None:
            already_configured: ConfigEntry = async_config_entry_by_username(self.hass, user_input[CONF_USERNAME])
            await self.async_set_unique_id(user_input[CONF_USERNAME])

            if already_configured:
                _LOGGER.warning('The config entry is already configured: {%s}!', already_configured.title)
                errors["base"] = CONFIG_FLOW_ALREADY_CONFIGURED_ERROR
            else:
                energa = EnergaMyMeterClient()
                try:
                    await self.hass.async_add_executor_job(
                        energa.open_connection,
                        user_input[CONF_USERNAME],
                        user_input[CONF_PASSWORD]
                    )
                except RuntimeError as error:
                    _LOGGER.error('An unknown error occurred: {%s}', error)
                    errors["base"] = CONFIG_FLOW_UNKNOWN_ERROR
                except EnergaWebsiteLoadingError:
                    errors["base"] = CONFIG_FLOW_UNKNOWN_ERROR
                except EnergaMyMeterAuthorizationError:
                    errors["base"] = CONFIG_FLOW_UNAUTHORIZED_ERROR
                except EnergaNoSuitableMetersFoundError:
                    errors["base"] = CONFIG_FLOW_NO_SUPPORTED_METERS_ERROR

                if not errors:
                    self._data = {
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD]
                    }
                    return await self.async_step_meter()

        schema = vol.Schema({
            vol.Required(CONF_USERNAME): cv.string,
            vol.Required(CONF_PASSWORD): cv.string
        })

        return self.async_show_form(step_id=CONFIG_FLOW_STEP_USER, data_schema=schema, errors=errors)

    async def async_step_meter(self, user_input=None):
        """Allow the user to select the meter"""

        errors: Dict[str, str] = {}
        options = []
        try:
            energa = EnergaMyMeterClient()
            await self.hass.async_add_executor_job(
                energa.open_connection,
                self._data[CONF_USERNAME],
                self._data[CONF_PASSWORD]
            )
            meters = await self.hass.async_add_executor_job(energa.get_meters)

            for meter in meters:
                pretty_description: str = meters.get(meter).get('meter_description')
                options.append({
                    'value': f'{meter},{pretty_description.split(' ')[0]}',
                    'label': pretty_description,
                })
        except EnergaWebsiteLoadingError:
            errors["base"] = CONFIG_FLOW_UNKNOWN_ERROR
        except EnergaMyMeterAuthorizationError:
            errors["base"] = CONFIG_FLOW_UNAUTHORIZED_ERROR
        except EnergaNoSuitableMetersFoundError:
            errors["base"] = CONFIG_FLOW_NO_SUPPORTED_METERS_ERROR

        if user_input is not None:
            if not errors:
                selected_option = user_input[CONFIG_FLOW_SELECTED_METER_NUMBER].split(',')
                self._data[CONFIG_FLOW_SELECTED_METER_ID] = selected_option[0]
                self._data[CONFIG_FLOW_SELECTED_METER_NUMBER] = selected_option[1]
                title = DEFAULT_ENTRY_TITLE.format(username=self._data[CONF_USERNAME],
                                                   meter_id=self._data[CONFIG_FLOW_SELECTED_METER_NUMBER])
                return self.async_create_entry(title=title, data=self._data)

        schema = vol.Schema({
            vol.Required(CONFIG_FLOW_SELECTED_METER_NUMBER): SelectSelector(
                SelectSelectorConfig(
                    multiple=False,
                    custom_value=False,
                    options=options
                )
            )

        })

        return self.async_show_form(step_id=CONFIG_FLOW_STEP_METER, data_schema=schema, errors=errors)


class EnergaMyMeterOptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """Manage the options for the custom component."""

        errors: Dict[str, str] = {}

        default_scan_interval = self._config_entry.options.get(CONF_SCAN_INTERVAL) or DEFAULT_SCAN_INTERVAL

        if user_input is not None:
            if not errors:
                return self.async_create_entry(title="", data={CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL]})

        options_schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=default_scan_interval): cv.positive_int
            }
        )
        return self.async_show_form(step_id="init", data_schema=options_schema, errors=errors)
