"""Base configuration for Energa integration"""

ENERGA_MY_METER_URL = 'https://mojlicznik.energa-operator.pl'
ENERGA_MY_METER_LOGIN_URL = f'{ENERGA_MY_METER_URL}/dp/UserLogin.do'
ENERGA_MY_METER_DATA_URL = f'{ENERGA_MY_METER_URL}/dp/UserData.do'
ENERGA_ACCOUNT_DATA_URL = f'{ENERGA_MY_METER_URL}/dp/UserAccount.do'
ENERGA_HISTORICAL_DATA_URL = f'{ENERGA_MY_METER_URL}/dp/resources/chart'
ENERGA_REQUESTS_TIMEOUT = 10
