"""pytest fixtures."""
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    assert not enable_custom_integrations
    yield


@pytest.fixture(autouse=True)
def hass_with_jobs_mock(hass: HomeAssistant) -> HomeAssistant:
    """Add a functionality that properly decorates executor jobs"""

    def simple_execute_job(target, *args):
        return target(*args)

    hass.async_add_executor_job = AsyncMock()
    hass.async_add_executor_job.side_effect = simple_execute_job
    return hass
