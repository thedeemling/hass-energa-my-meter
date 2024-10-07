"""Tests for sensor logic"""
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from helpers import create_config_entry


class TestSensor:
    async def test_creating_live_sensors(self, hass: HomeAssistant):
        entry_id = 'someentryid'
        ppe_number = 'somenumber'
        meter_number = 12345
        expected_data = {
            'ppe_number': ppe_number,
            'meter_number': meter_number,
            'seller': 'some-seller',
            'client_type': 'some-client-type',
            'contract_period': 'from 2012',
            'energy_used': '8877',
            'energy_used_last_update': dt_util.now().strftime('%Y-%m-%d %H:%M:%S.%f%z'),
            'energy_produced': '1122',
            'meter_id': '1234',
            'ppe_address': 'some address',
            'tariff': 'some tariff'
        }
        with (
            patch(
                target='custom_components.energa_my_meter.hass_integration.energa_my_meter_updater.EnergaMyMeterUpdater.get_data',
                return_value=expected_data
            ),
            patch(
                'custom_components.energa_my_meter.hass_integration.energa_my_meter_updater.EnergaMyMeterUpdater.async_refresh'
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

            for state_name in [
                'energy_used', 'energy_produced', 'tariff', 'ppe_address', 'contract_period',
                'client_type', 'seller', 'meter_id', 'energy_used_last_update'
            ]:
                state = hass.states.get(f'sensor.energa_12345_{state_name}')
                assert state
                assert state.state == expected_data.get(state_name)
