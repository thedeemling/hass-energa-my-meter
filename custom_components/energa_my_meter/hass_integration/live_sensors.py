"""
Classes implementing live sensors for Energa integration
Live sensors are updated by coordinator,
so they will not call Energa website on their own, but rather once at the same time
"""
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.energa_my_meter.hass_integration.base_sensor import EnergaEnergyBaseSensor, \
    EnergaAdditionalDataBaseSensor


class EnergaEnergyUsedSensor(EnergaEnergyBaseSensor):
    """Energy used sensor with support for the Energy dashboard"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='energy_used', coordinator=coordinator,
                         name='Energy used', icon='mdi:lightning-bolt')


class EnergaEnergyProducedSensor(EnergaEnergyBaseSensor):
    """Energy produced sensor with support for the Energy dashboard"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='energy_produced', coordinator=coordinator,
                         name='Energy produced', icon='mdi:home-battery')


class EnergaTariffSensor(EnergaAdditionalDataBaseSensor):
    """Meters currently associated tariff sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='tariff', coordinator=coordinator,
                         name='Tariff', icon='mdi:camera-burst')


class EnergaPPEAddressSensor(EnergaAdditionalDataBaseSensor):
    """The address of the PPE sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='ppe_address', coordinator=coordinator,
                         name='PPE address', icon='mdi:map-marker')


class EnergaContractPeriodSensor(EnergaAdditionalDataBaseSensor):
    """The string representation of the user's contract period sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='contract_period', coordinator=coordinator,
                         name='Contract period', icon='mdi:calendar-range')


class EnergaClientTypeSensor(EnergaAdditionalDataBaseSensor):
    """The client type sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='client_type', coordinator=coordinator,
                         name='Client type', icon='mdi:account-box-multiple')


class EnergaSellerSensor(EnergaAdditionalDataBaseSensor):
    """The name of the seller sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='seller', coordinator=coordinator,
                         name='Seller', icon='mdi:account-box-multiple')


class EnergaMeterInternalIdSensor(EnergaAdditionalDataBaseSensor):
    """The meter's internal ID sensor. It is used in internal Energa calls."""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='meter_id', coordinator=coordinator,
                         name='ID', icon='mdi:counter')


class EnergaMeterUsedEnergyLastUpdate(EnergaAdditionalDataBaseSensor):
    """The date of the last update on the Energa website sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='energy_used_last_update', coordinator=coordinator,
                         name='Last update', icon='mdi:update')
