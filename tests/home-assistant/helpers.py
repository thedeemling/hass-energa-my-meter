from unittest.mock import AsyncMock, patch, MagicMock

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.energa_my_meter import DOMAIN


def decorate_home_assistant_mock(hass: HomeAssistant) -> HomeAssistant:
    """Add a functionality that properly decorates executor jobs"""

    def simple_execute_job(target, *args):
        return target(*args)

    hass.async_add_executor_job = AsyncMock()
    hass.async_add_executor_job.side_effect = simple_execute_job
    return hass


async def create_config_entry(
        hass: HomeAssistant,
        entry_id: str,
        options: dict = None,
        data: dict = None
) -> MockConfigEntry:
    """Create a config entry for tests"""

    if not hass.data:
        hass.data = {}

    if not hass.data.get(DOMAIN):
        hass.data[DOMAIN] = {}

    #coordinator_mock.async_refresh = MagicMock
    # coordinator_mock.data = None
    # coordinator_mock.last_update_success = True

    # data['coordinator'] = coordinator_mock

    hass.data[DOMAIN] = {
        entry_id: data
    }

    entry = MockConfigEntry(
        entry_id=entry_id,
        options=options,
        data=data,
        domain=DOMAIN,
        title=entry_id,
        version=1
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def create_client():
    client = MagicMock()
    client.open_connection = MagicMock()
    client.disconnect = MagicMock()
    client.get_account_main_data = MagicMock()
    client.get_statistics = MagicMock()
    return client
