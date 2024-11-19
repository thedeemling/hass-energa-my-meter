"""
All const values for the Energa My meter custom component
"""

DOMAIN = 'energa_my_meter'

DEFAULT_SCAN_INTERVAL = 300
DEFAULT_ENTRY_TITLE = '{meter_name}'

CONFIG_FLOW_ALREADY_CONFIGURED_ERROR = 'already_configured'
CONFIG_FLOW_UNKNOWN_ERROR = 'generic_error'
CONFIG_FLOW_CAPTCHA_ERROR = 'captcha_error'
CONFIG_FLOW_WEBSITE_ERROR = 'website_error'
CONFIG_FLOW_UNAUTHORIZED_ERROR = 'unauthorized'
CONFIG_FLOW_NO_SUPPORTED_METERS_ERROR = 'no_supported_meters'
CONFIG_FLOW_STEP_USER = 'user'
CONFIG_FLOW_STEP_METER = 'meter'
CONFIG_FLOW_STEP_STATISTICS = 'statistics'

CONF_SELECTED_METER_ID = 'selected_meter_internal_id'
CONF_SELECTED_METER_NUMBER = 'selected_meter'
CONF_SELECTED_METER_NAME = 'meter_name'
CONF_SELECTED_METER_PPE = 'selected_ppe'
CONF_SELECTED_ZONES = 'selected_zones'
CONF_SELECTED_MODES = 'selected_modes'
CONF_NUMBER_OF_DAYS_TO_LOAD = 'number_of_days_to_load'

PREVIOUS_DAYS_NUMBER_TO_BE_LOADED = 10
MAXIMUM_DAYS_TO_BE_LOADED_AT_ONCE = 60

DEBUGGING_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
