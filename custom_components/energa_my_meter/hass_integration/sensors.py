from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.energa_my_meter.hass_integration.base_sensor import EnergaEnergyBaseSensor, \
    EnergaAdditionalDataBaseSensor


class EnergaEnergyUsedSensor(EnergaEnergyBaseSensor):
    """Energy used sensor with support for the Energy dashboard"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:lightning-bolt'
        super().__init__(entry=entry, name_id='energy_used', coordinator=coordinator,
                         name=f'Energy used')


class EnergaEnergyProducedSensor(EnergaEnergyBaseSensor):
    """Energy produced sensor with support for the Energy dashboard"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:home-battery'
        super().__init__(entry=entry, name_id='energy_produced', coordinator=coordinator,
                         name=f'Energy produced')


class EnergaTariffSensor(EnergaAdditionalDataBaseSensor):
    """Meters currently associated tariff sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:camera-burst'
        super().__init__(entry=entry, name_id='tariff', coordinator=coordinator,
                         name=f'Tariff')


class EnergaPPEAddressSensor(EnergaAdditionalDataBaseSensor):
    """The address of the PPE sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:map-marker'
        super().__init__(entry=entry, name_id='ppe_address', coordinator=coordinator,
                         name=f'PPE address')


class EnergaContractPeriodSensor(EnergaAdditionalDataBaseSensor):
    """The string representation of the user's contract period sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:calendar-range'
        super().__init__(entry=entry, name_id='contract_period', coordinator=coordinator,
                         name=f'Contract period')


class EnergaClientTypeSensor(EnergaAdditionalDataBaseSensor):
    """The client type sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:account-box-multiple'
        super().__init__(entry=entry, name_id='client_type', coordinator=coordinator,
                         name=f'Client type')


class EnergaSellerSensor(EnergaAdditionalDataBaseSensor):
    """The name of the seller sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:account-box-multiple'
        super().__init__(entry=entry, name_id='seller', coordinator=coordinator,
                         name=f'Seller')


class EnergaMeterInternalIdSensor(EnergaAdditionalDataBaseSensor):
    """The meter's internal ID sensor. It is used in internal Energa calls."""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:counter'
        super().__init__(entry=entry, name_id='meter_id', coordinator=coordinator,
                         name=f'ID')


class EnergaMeterUsedEnergyLastUpdate(EnergaAdditionalDataBaseSensor):
    """The date of the last update on the Energa website sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        self._attr_icon = 'mdi:update'
        super().__init__(entry=entry, name_id='energy_used_last_update', coordinator=coordinator,
                         name=f'Last update')
