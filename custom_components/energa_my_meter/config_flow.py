"""
Adding the support for Home Assistant's GUI installation of the integration
"""

from __future__ import annotations

import logging
from typing import Any, Dict
import voluptuous as vol

from homeassistant.helpers import config_validation as cv
from homeassistant.core import callback
from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)

from .const import (DOMAIN, DEFAULT_SCAN_INTERVAL, DEFAULT_ENTRY_TITLE)
from .energa import EnergaMyCounterClient
from .errors import (
    EnergaMyCounterAuthorizationError,
    EnergaWebsiteLoadingError,
    EnergaNoSuitableCountersFoundError
)
from .common import async_config_entry_by_username

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
        return EnergaMyCounterOptionsFlowHandler(config_entry)

    async def async_step_import(self, user_input=None):
        """Handle a flow imported from YAML configuration"""

        if user_input is not None:
            self._data = {CONF_USERNAME: user_input[CONF_USERNAME], CONF_PASSWORD: user_input[CONF_PASSWORD]}
            self._options = {CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL]}

            await self.async_set_unique_id(user_input[CONF_USERNAME])

            if async_config_entry_by_username(self.hass, user_input[CONF_USERNAME]):
                return self.async_abort(reason='Already configured')

            energa_client = EnergaMyCounterClient(self.hass, user_input[CONF_USERNAME], user_input[CONF_PASSWORD])

            try:
                await energa_client.get_user_counters()
                title = DEFAULT_ENTRY_TITLE.format(username=user_input[CONF_USERNAME])
                return self.async_create_entry(title=title, data=self._data, options=self._options)
            except EnergaWebsiteLoadingError:
                _LOGGER.exception('Could not load the Energa website')
            except EnergaMyCounterAuthorizationError:
                _LOGGER.exception(
                    'Could not log into the Energa website using provided credentials in the YAML config!')
            except EnergaNoSuitableCountersFoundError:
                _LOGGER.exception('Could not find any smart counter on the provided Energa account!')

        return self.async_abort(reason='No input provided')

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""

        errors: Dict[str, str] = {}

        if user_input is not None:
            already_configured: ConfigEntry = async_config_entry_by_username(self.hass, user_input[CONF_USERNAME])
            await self.async_set_unique_id(user_input[CONF_USERNAME])

            if already_configured:
                _LOGGER.warning('The config entry is already configured: {%s}!', already_configured.title)
                errors["base"] = "already_configured"
            else:
                energa_client = EnergaMyCounterClient(self.hass, user_input[CONF_USERNAME], user_input[CONF_PASSWORD])

                try:
                    await energa_client.get_user_counters()
                except EnergaWebsiteLoadingError:
                    errors["base"] = "generic_error"
                except EnergaMyCounterAuthorizationError:
                    errors["base"] = "unauthorized"
                except EnergaNoSuitableCountersFoundError:
                    errors["base"] = "no_supported_counters"

                if not errors:
                    self._data = {
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD]
                    }
                    title = DEFAULT_ENTRY_TITLE.format(username=user_input[CONF_USERNAME])
                    return self.async_create_entry(title=title, data=self._data)

        schema = vol.Schema({
            vol.Required(CONF_USERNAME): cv.string,
            vol.Required(CONF_PASSWORD): cv.string
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class EnergaMyCounterOptionsFlowHandler(OptionsFlow):
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
