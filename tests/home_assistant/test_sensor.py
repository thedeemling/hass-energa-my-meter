"""Tests for sensor logic"""
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.components.recorder.common import async_wait_recording_done

from custom_components.energa_my_meter.common import generate_entity_name
from .helpers import create_config_entry

INTEGRATION_PACKAGE = 'custom_components.energa_my_meter.hass_integration'


async def test_creating_sensors( hass: HomeAssistant):
    """Loading a correct configuration should create all sensors with a correct state"""
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    entry_id = 'someentryid'
    ppe_number = 'somenumber'
    meter_number = 12345
    expected_data = {
        'ppe_number': ppe_number,
        'meter_number': meter_number,
        'seller': 'some-seller',
        'client_type': 'some-client-type',
        'contract_period': 'from 2012',
        'meter_id': '1234',
        'ppe_address': 'some address',
        'tariff': 'some tariff',
        'meter_readings': []
    }
    with (
        patch(
            target=f'{INTEGRATION_PACKAGE}.energa_coordinator.EnergaCoordinator.get_data',
            return_value=expected_data
        ),
        patch(
            target=f'{INTEGRATION_PACKAGE}.energa_coordinator.EnergaCoordinator.get_statistics',
            return_value={}
        ),
        patch(
            f'{INTEGRATION_PACKAGE}.energa_coordinator.EnergaCoordinator.async_refresh'
        )
    ):
        await create_config_entry(hass, entry_id, None, {
            'meter_number': meter_number,
            'ppe_number': ppe_number,
            'username': 'some user',
            'password': 'some password',
            'selected_meter': '12345',
            'selected_meter_internal_id': '1234'
        })

        await hass.async_block_till_done()
        await async_wait_recording_done(hass)

        for state_name in [
            'tariff', 'ppe_address', 'contract_period', 'client_type', 'seller'
        ]:
            state = hass.states.get(generate_entity_name('12345', state_name))
            assert state
            assert state.state == expected_data.get(state_name)
