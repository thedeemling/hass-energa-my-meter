"""
Simple model classes for data related to Energa My Meter
"""
import json
from datetime import datetime


class EnergaHistoricalPoint:
    """Representation of one hour of Energa data"""

    def __init__(self, point: dict, zones: [str]):
        timestamp = point['tm']
        self._timestamp = timestamp
        self._estimate = point['est']
        self._values = {}

        for idx, value in enumerate(point['zones']):
            if len(zones) > idx:
                self._values[zones[idx]] = value

    @property
    def timestamp(self):
        """The timestamp of the point"""
        return self._timestamp

    @property
    def values(self) -> dict:
        """The values for every zone for the point"""
        return self._values

    @property
    def is_estimated(self):
        """Whether the point is estimated"""
        return self._estimate

    def get_normalized_timestamp(self):
        """Returns the timestamp normalized for Python date times functions"""
        return int(int(self.timestamp) / 1000)

    def get_value_for_zone(self, zone: str) -> int:
        """Returns the value for the given zone"""
        return float(self.values.get(zone)) if self.values.get(zone) else 0


class EnergaStatisticsData:
    """Representation of the historical Energa data for energy usage"""

    def __init__(self, response: dict):
        self._tariff = response['tariffName']
        self._timezone = response['tz']
        self._unit = response['unit']
        self._date_from = response['mainChartDate']
        self._date_to = None
        self._historical_points: [EnergaHistoricalPoint] = []
        self._zones = []

        for zone in response['zones']:
            self._zones.append(zone['label'])

        for point in response['mainChart']:
            self._historical_points.append(EnergaHistoricalPoint(point, self._zones))

    @property
    def historical_points(self) -> [EnergaHistoricalPoint]:
        """The list of the historical points, sorted by timestamp"""
        return self._historical_points

    @property
    def date_from(self):
        """The start date of the historical data query range"""
        return self._date_from

    @property
    def date_to(self):
        """The finishing date of the historical data query range"""
        return self._date_to

    @property
    def tariff(self):
        """The tariff that is currently used by the meter"""
        return self._tariff

    @property
    def timezone(self):
        """The name of the time zone that historical points timestamps belong to"""
        return self._timezone

    @property
    def unit(self):
        """The unit of the measurement"""
        return self._unit

    @property
    def zones(self):
        """The list of zones"""
        return self._zones

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
    def meter_name(self) -> int:
        """Returns the user-friendly name of the meter"""
        return self._data['meter_name']

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

    def get(self, key: str):
        """Returns the value of the specified key"""
        return self._data.get(key)

    def __eq__(self, other) -> bool:
        """Compares two EnergaData instances"""
        return isinstance(other, EnergaData) and self._data == other._data
