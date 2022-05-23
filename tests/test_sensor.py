"""Testing the sensors configuration of the integration"""
from unittest.mock import MagicMock

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import EntityCategory
import pytest

from custom_components.energa_my_meter.sensor import (
    EnergaContractPeriodSensor,
    EnergaEnergyProducedSensor,
    EnergaEnergyUsedSensor,
    EnergaPPEAddressSensor,
    EnergaTariffSensor,
)


class TestEnergaSensors:
    """Tests for creating and managing sensors"""

    @pytest.fixture(autouse=True)
    def coordinator_mock(self):
        return MagicMock()

    @pytest.fixture(autouse=True)
    def config_entry_mock(self):
        return {
            'ppe_number': 2,
            'meter_number': 1
        }

    def test_energy_used_should_be_available_if_value_is_provided(self, coordinator_mock, config_entry_mock):
        """If the energy value is set correctly the integration should create a proper available sensor"""
        coordinator_mock.data = {
            'energy_used': 123
        }

        result = EnergaEnergyUsedSensor(config_entry_mock, coordinator_mock)

        assert result.available
        assert result.entity_registry_enabled_default
        assert result.native_value == 123

    def test_energy_used_should_not_be_available_if_value_is_not_provided(self, coordinator_mock, config_entry_mock):
        """If the energy value is not set the integration should create a sensor that is unavailable to the user"""
        coordinator_mock.data = {
            'energy_used': None
        }

        result = EnergaEnergyUsedSensor(config_entry_mock, coordinator_mock)

        assert not result.available
        assert not result.entity_registry_enabled_default
        assert result.native_value is None

    def test_setting_up_energy_sensor_should_set_energy_attributes(self, coordinator_mock, config_entry_mock):
        """
            Energy values sensors should be properly configured in the Home Assistant
            with the support for the Energy Dashboard
        """
        coordinator_mock.data = {
            'energy_produced': 123
        }

        result = EnergaEnergyProducedSensor(config_entry_mock, coordinator_mock)

        assert result.native_value == 123
        assert result.device_class == 'energy'
        assert result.state_class == 'total_increasing'
        assert result.native_unit_of_measurement == 'kWh'
        assert result.entity_category is None

    def test_additional_sensor_should_have_diagnostic_type(self, coordinator_mock, config_entry_mock):
        """Additional sensors should have diagnostic type"""
        coordinator_mock.data = {
            'tariff': 'Tariff'
        }

        result = EnergaTariffSensor(config_entry_mock, coordinator_mock)

        assert result.entity_category == EntityCategory.DIAGNOSTIC
        assert result.native_value == 'Tariff'

    def test_sensors_should_have_proper_generated_unique_id(self, coordinator_mock, config_entry_mock):
        """All sensors should have unique ID generated without the risk of duplicates"""
        coordinator_mock.data = {
            'ppe_address': 'PPE Address'
        }

        result = EnergaPPEAddressSensor(config_entry_mock, coordinator_mock)

        assert result.unique_id == 'energa_my_meter_2_1_ppe_address'

    def test_sensors_should_have_proper_device_info_generated(selfself, coordinator_mock, config_entry_mock):
        """Sensors should be grouped with the device info using PPE & meter number as they are unique"""
        coordinator_mock.data = {
            'contract_period': 'Contract period'
        }

        result = EnergaContractPeriodSensor(config_entry_mock, coordinator_mock)

        assert result.device_info is not None
        assert result.device_info['entry_type'] == DeviceEntryType.SERVICE
        assert result.device_info['manufacturer'] is not None
        assert result.device_info['sw_version'] is not None
        assert result.device_info['model'] is not None
        assert result.device_info['identifiers'] is not None
        assert result.device_info['name'] is not None
        assert result.device_info['configuration_url'] is not None
