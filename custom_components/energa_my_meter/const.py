"""
All const values for the Energa My meter custom component
"""

DOMAIN = 'energa_my_meter'

DEFAULT_SCAN_INTERVAL = 300
DEFAULT_ENTRY_TITLE = 'Energa {username} ({meter_id})'

CONFIG_FLOW_ALREADY_CONFIGURED_ERROR = 'already_configured'
CONFIG_FLOW_UNKNOWN_ERROR = 'generic_error'
CONFIG_FLOW_CAPTCHA_ERROR = 'captcha_error'
CONFIG_FLOW_UNAUTHORIZED_ERROR = 'unauthorized'
CONFIG_FLOW_NO_SUPPORTED_METERS_ERROR = 'no_supported_meters'

CONFIG_FLOW_STEP_USER = 'user'
CONFIG_FLOW_STEP_METER = 'meter'
CONFIG_FLOW_SELECTED_METER_ID = 'selected_meter_internal_id'
CONFIG_FLOW_SELECTED_METER_NUMBER = 'selected_meter'

PREVIOUS_DAYS_NUMBER_TO_BE_LOADED = 10
