"""
All const values for the Energa My meter custom component
"""

DOMAIN = 'energa_my_meter'

DEFAULT_SCAN_INTERVAL = 300
ENERGA_MY_METER_URL = 'https://mojlicznik.energa-operator.pl'
ENERGA_MY_METER_DATA_URL = f'{ENERGA_MY_METER_URL}/dp/UserLogin.do'
ENERGA_MY_METER_HISTORICAL_DATA_URL = f'{ENERGA_MY_METER_URL}/dp/resources/chart'
ENERGA_REQUESTS_TIMEOUT = 10
DEFAULT_ENTRY_TITLE = 'Energa {username}'
