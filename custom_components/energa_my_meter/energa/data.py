import json
from datetime import datetime


class EnergaStatisticsData:
    """Representation of the historical Energa data for energy usage"""

    def __init__(self, response: dict):
        self.tariff = response['tariffName']
        self.timezone = response['tz']
        self.unit = response['unit']
        self.date_from = response['mainChartDate']
        self.date_to = None
        self.historical_points = []

        for point in response['mainChart']:
            timestamp = point['tm']
            self.date_to = timestamp
            self.historical_points.append({
                'timestamp': timestamp,
                'value': point['zones'][0]
            })

    def __str__(self):
        obj = {'tariff': self.tariff, 'timezone': self.timezone, 'unit': self.unit, 'date_from': self.date_from,
               'date_to': self.date_to, 'historical_points': self.historical_points}
        return json.dumps(obj)


class EnergaData:
    """Representation of the data gathered from the Energa website"""

    def __init__(self, data: dict):
        self._data: dict = data

    @property
    def meter_number(self) -> int:
        """Returns the number of the meter - known to the client from the contract"""
        return self._data['meter_number']

    @property
    def seller(self) -> str:
        """Returns the name of the contract seller"""
        return self._data['seller']

    @property
    def client_type(self) -> str:
        """Returns the type of the client"""
        return self._data['client_type']

    @property
    def contract_period(self) -> str:
        """Returns the period of the contract in the string representation"""
        return self._data['contract_period']

    @property
    def energy_used(self) -> int:
        """Returns the incremental value of the meter"""
        return self._data['energy_used']

    @property
    def energy_used_last_update(self) -> datetime:
        """Returns the information when was the last time Energa updated the value of the meter"""
        return self._data['energy_used_last_update']

    @property
    def energy_produced(self) -> int:
        """Returns the incremental value of the information how much the meter registered produced energy"""
        return self._data['energy_produced']

    @property
    def meter_id(self) -> int:
        """Returns the internal ID of the meter (used in the Energa website calls)"""
        return self._data['meter_id']

    @property
    def ppe_address(self) -> str:
        """Returns address of the registered PPE related to the meter"""
        return self._data['ppe_address']

    @property
    def ppe_number(self) -> int:
        """Returns number of the registered PPE related to the meter"""
        return self._data['ppe_number']

    @property
    def tariff(self) -> str:
        """Returns the name of the tariff related to the meter"""
        return self._data['tariff']

    def __getitem__(self, items):
        return self._data.__getitem__(items)
