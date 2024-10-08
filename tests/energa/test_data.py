"""Tests related to the data model"""
from datetime import datetime

from custom_components.energa_my_meter.energa.client import EnergaData


def test_converting_energa_data_from_dict():
    """Convertion of the data returned by Energa into data model class"""
    data = {
        'seller': 'Some seller',
        'client_type': 'Client type',
        'contract_period': 'Contract period',
        'energy_used': 120,
        'energy_used_last_update': datetime.now(),
        'energy_produced': 121,
        'meter_id': 123,
        'ppe_address': 'Some address',
        'ppe_number': 124,
        'tariff': 'Some tariff',
        'meter_number': 125,
    }
    result = EnergaData(data)

    assert data['seller'] == result.seller
    assert data['client_type'] == result.client_type
    assert data['contract_period'] == result.contract_period
    assert data['energy_used'] == result.energy_used
    assert data['energy_used_last_update'] == result.energy_used_last_update
    assert data['energy_produced'] == result.energy_produced
    assert data['meter_id'] == result.meter_id
    assert data['ppe_address'] == result.ppe_address
    assert data['ppe_number'] == result.ppe_number
    assert data['tariff'] == result.tariff
    assert data['meter_number'] == result.meter_number
