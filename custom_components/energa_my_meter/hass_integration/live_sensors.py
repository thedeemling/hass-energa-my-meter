"""
Classes implementing live sensors for Energa integration
Live sensors are updated by coordinator,
so they will not call Energa website on their own, but rather once at the same time
"""
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.const import EntityCategory, UnitOfEnergy
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from ..hass_integration.base_sensor import EnergaBaseCoordinatorSensor


class EnergaEnergyUsedSensor(EnergaBaseCoordinatorSensor):
    """Energy used sensor with support for the Energy dashboard"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='energy_used', coordinator=coordinator, name='Energy used')
        self._attr_icon = 'mdi:lightning-bolt'
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR


class EnergaEnergyProducedSensor(EnergaBaseCoordinatorSensor):
    """Energy produced sensor with support for the Energy dashboard"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='energy_produced', coordinator=coordinator, name='Energy produced')
        self._attr_icon = 'mdi:home-battery'
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR


class EnergaTariffSensor(EnergaBaseCoordinatorSensor):
    """Meters currently associated tariff sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='tariff', coordinator=coordinator, name='Tariff')
        self._attr_icon = 'mdi:camera-burst'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class EnergaPPEAddressSensor(EnergaBaseCoordinatorSensor):
    """The address of the PPE sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='ppe_address', coordinator=coordinator, name='PPE address')
        self._attr_icon = 'mdi:map-marker'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class EnergaContractPeriodSensor(EnergaBaseCoordinatorSensor):
    """The string representation of the user's contract period sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='contract_period', coordinator=coordinator, name='Contract period')
        self._attr_icon = 'mdi:calendar-range'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class EnergaClientTypeSensor(EnergaBaseCoordinatorSensor):
    """The client type sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='client_type', coordinator=coordinator, name='Client type')
        self._attr_icon = 'mdi:account-box-multiple'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class EnergaSellerSensor(EnergaBaseCoordinatorSensor):
    """The name of the seller sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='seller', coordinator=coordinator, name='Seller')
        self._attr_icon = 'mdi:account-box-multiple'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class EnergaMeterInternalIdSensor(EnergaBaseCoordinatorSensor):
    """The meter's internal ID sensor. It is used in internal Energa calls."""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='meter_id', coordinator=coordinator, name='ID')
        self._attr_icon = 'mdi:counter'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class EnergaMeterUsedEnergyLastUpdate(EnergaBaseCoordinatorSensor):
    """The date of the last update on the Energa website sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: DataUpdateCoordinator):
        super().__init__(entry=entry, name_id='energy_used_last_update', coordinator=coordinator, name='Last update')
        self._attr_icon = 'mdi:update'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
