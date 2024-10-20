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
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, NumberSelector, NumberSelectorConfig, \
    NumberSelectorMode, SelectOptionDict
from homeassistant.util import dt as dt_util

from .common import async_config_entry_by_username, get_zone_display_name
from .const import (
    CONFIG_FLOW_ALREADY_CONFIGURED_ERROR,
    CONFIG_FLOW_NO_SUPPORTED_METERS_ERROR,
    CONFIG_FLOW_UNAUTHORIZED_ERROR,
    CONFIG_FLOW_UNKNOWN_ERROR,
    DEFAULT_ENTRY_TITLE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN, CONF_SELECTED_METER_NUMBER, CONFIG_FLOW_STEP_USER, CONFIG_FLOW_STEP_METER,
    CONF_SELECTED_METER_ID, CONFIG_FLOW_CAPTCHA_ERROR, CONF_NUMBER_OF_DAYS_TO_LOAD,
    PREVIOUS_DAYS_NUMBER_TO_BE_LOADED, CONF_SELECTED_ZONES, CONFIG_FLOW_STEP_STATISTICS, CONF_SELECTED_MODES,
)
from .energa.client import EnergaMyMeterClient
from .energa.errors import (
    EnergaMyMeterAuthorizationError,
    EnergaNoSuitableMetersFoundError,
    EnergaWebsiteLoadingError, EnergaMyMeterCaptchaRequirementError,
)
from .energa.stats_modes import EnergaStatsModes

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
                CONF_USERNAME: user_input.get(CONF_USERNAME),
                CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                CONF_SELECTED_METER_ID: user_input.get(CONF_SELECTED_METER_ID),
                CONF_SELECTED_METER_NUMBER: user_input.get(CONF_SELECTED_METER_NUMBER),
                CONF_SELECTED_MODES: user_input.get(CONF_SELECTED_MODES),
                CONF_SELECTED_ZONES: user_input.get(CONF_SELECTED_ZONES),
                CONF_NUMBER_OF_DAYS_TO_LOAD: user_input.get(
                    CONF_NUMBER_OF_DAYS_TO_LOAD) if user_input.get(
                    CONF_NUMBER_OF_DAYS_TO_LOAD) else PREVIOUS_DAYS_NUMBER_TO_BE_LOADED,
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
                title = DEFAULT_ENTRY_TITLE.format(
                    username=self._data.get(CONF_USERNAME),
                    meter_id=self._data.get(CONF_SELECTED_METER_NUMBER)
                )
                return self.async_create_entry(title=title, data=self._data, options=self._options)
            except EnergaMyMeterCaptchaRequirementError:
                _LOGGER.exception(
                    'A Captcha challenge is shown to the user. ' +
                    'Try to log into the Energa and finish the challenge or try again later.'
                )
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
                    # noinspection PyTypeChecker
                    await self.hass.async_add_executor_job(energa.disconnect)
                except RuntimeError as error:
                    _LOGGER.error('An unknown error occurred: {%s}', error)
                    errors["base"] = CONFIG_FLOW_UNKNOWN_ERROR
                except EnergaMyMeterCaptchaRequirementError:
                    errors["base"] = CONFIG_FLOW_CAPTCHA_ERROR
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

        if user_input is not None:
            if not errors:
                selected_option = user_input[CONF_SELECTED_METER_NUMBER].split(',')
                self._data[CONF_SELECTED_METER_ID] = selected_option[0]
                self._data[CONF_SELECTED_METER_NUMBER] = selected_option[1]
                return await self.async_step_statistics()
        else:
            options = []
            try:
                energa = EnergaMyMeterClient()
                await self.hass.async_add_executor_job(
                    energa.open_connection,
                    self._data[CONF_USERNAME],
                    self._data[CONF_PASSWORD]
                )

                # noinspection PyTypeChecker
                meters = await self.hass.async_add_executor_job(energa.get_meters)
                # noinspection PyTypeChecker
                await self.hass.async_add_executor_job(energa.disconnect)

                _LOGGER.debug("Found %s meter(s) on the specified account.", len(meters))

                for meter in meters:
                    pretty_description: str = meters.get(meter).get('meter_description')
                    options.append({
                        'value': f'{meter},{pretty_description.split(' ')[0]}',
                        'label': pretty_description,
                    })
            except EnergaMyMeterCaptchaRequirementError:
                errors["base"] = CONFIG_FLOW_CAPTCHA_ERROR
            except EnergaWebsiteLoadingError:
                errors["base"] = CONFIG_FLOW_UNKNOWN_ERROR
            except EnergaMyMeterAuthorizationError:
                errors["base"] = CONFIG_FLOW_UNAUTHORIZED_ERROR
            except EnergaNoSuitableMetersFoundError:
                errors["base"] = CONFIG_FLOW_NO_SUPPORTED_METERS_ERROR

            schema = vol.Schema({
                vol.Required(CONF_SELECTED_METER_NUMBER): SelectSelector(
                    SelectSelectorConfig(
                        multiple=False,
                        custom_value=False,
                        options=options
                    )
                )
            })

            return self.async_show_form(step_id=CONFIG_FLOW_STEP_METER, data_schema=schema, errors=errors)

    async def async_step_statistics(self, user_input=None):
        """Allows the user to select which zones to load"""
        errors: Dict[str, str] = {}

        if user_input is not None:
            if not errors:
                self._data[CONF_SELECTED_ZONES] = user_input[CONF_SELECTED_ZONES]
                self._data[CONF_SELECTED_MODES] = user_input[CONF_SELECTED_MODES]
                self._data[CONF_NUMBER_OF_DAYS_TO_LOAD] = user_input[CONF_NUMBER_OF_DAYS_TO_LOAD]

                title = DEFAULT_ENTRY_TITLE.format(username=self._data[CONF_USERNAME],
                                                   meter_id=self._data[CONF_SELECTED_METER_NUMBER])
                return self.async_create_entry(title=title, data=self._data)
        else:
            options = []
            try:
                energa = EnergaMyMeterClient()
                await self.hass.async_add_executor_job(
                    energa.open_connection,
                    self._data[CONF_USERNAME],
                    self._data[CONF_PASSWORD]
                )
                zones = await self.hass.async_add_executor_job(
                    energa.get_supported_zones,
                    self._data[CONF_SELECTED_METER_ID],
                    dt_util.now(),
                    None
                )
                # noinspection PyTypeChecker
                await self.hass.async_add_executor_job(energa.disconnect)

                _LOGGER.debug("Found %s zone(s) on the specified account.", len(zones))

                for zone in zones:
                    options.append(SelectOptionDict(value=zone, label=get_zone_display_name(zone)))

            except EnergaMyMeterCaptchaRequirementError:
                errors["base"] = CONFIG_FLOW_CAPTCHA_ERROR
            except EnergaWebsiteLoadingError:
                errors["base"] = CONFIG_FLOW_UNKNOWN_ERROR
            except EnergaMyMeterAuthorizationError:
                errors["base"] = CONFIG_FLOW_UNAUTHORIZED_ERROR
            except EnergaNoSuitableMetersFoundError:
                errors["base"] = CONFIG_FLOW_NO_SUPPORTED_METERS_ERROR

            schema = vol.Schema({
                vol.Required(CONF_SELECTED_ZONES): SelectSelector(
                    SelectSelectorConfig(
                        multiple=True,
                        custom_value=False,
                        options=options
                    )
                ),
                vol.Required(CONF_SELECTED_MODES): SelectSelector(
                    SelectSelectorConfig(
                        multiple=True,
                        custom_value=False,
                        options=[
                            SelectOptionDict(value=EnergaStatsModes.ENERGY_CONSUMED.name, label='Pobrana (A+)'),
                            SelectOptionDict(value=EnergaStatsModes.ENERGY_PRODUCED.name, label='Wyprodukowana (A-)')
                        ]
                    )
                ),
                vol.Required(CONF_NUMBER_OF_DAYS_TO_LOAD,
                             default=PREVIOUS_DAYS_NUMBER_TO_BE_LOADED): NumberSelector(
                    NumberSelectorConfig(
                        step=1,
                        min=1,
                        mode=NumberSelectorMode.BOX
                    )
                )
            })

            return self.async_show_form(step_id=CONFIG_FLOW_STEP_STATISTICS, data_schema=schema, errors=errors)


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
