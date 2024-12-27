"""
Classes implementing live sensors for Energa integration
Live sensors are updated by coordinator,
so they will not call Energa website on their own, but rather once at the same time
"""
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfEnergy

from .energa_coordinator import EnergaCoordinator
from .live_sensor import EnergaLiveSensor
from ..common import normalize_entity_string
from ..energa.data import EnergaMeterReading


class EnergaMeterReadingSensor(EnergaLiveSensor):
    """The meter reading sensor that contains the last measured value"""

    def __init__(self, entry: ConfigEntry, coordinator: EnergaCoordinator, reading_name: str):
        name_id = self._generate_entity_name(reading_name)
        super().__init__(entry=entry, name_id=name_id, coordinator=coordinator,
                         name=f'Meter reading ({reading_name})')
        self._reading_name = reading_name
        self._attr_icon = 'mdi:lightning-bolt'
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def _get_meter_data(self) -> EnergaMeterReading | None:
        """Returns the data for the related meter reading"""
        meter_readings = self._get_data_from_coordinator('meter_readings', [])
        return next(obj for obj in meter_readings if obj.meter_name == self._reading_name)

    @staticmethod
    def _generate_entity_name(reading_name: str):
        return normalize_entity_string(
            reading_name
            .replace('A+', 'from_grid')
            .replace('A-', 'to_grid')
        )

    @property
    def native_value(self) -> float | str | None:
        """Returns the value of the sensor from the coordinator updates"""
        data = self._get_meter_data()
        return data.value if data else None

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Entity will be disabled if it does not contain any data - perhaps it could not be gathered"""
        data = self._get_meter_data()
        return data is not None

    @property
    def available(self) -> bool:
        """Entity will not be available in GUI if it does not contain any data - perhaps it could not be gathered"""
        data = self._get_meter_data()
        return data is not None

    @property
    def extra_state_attributes(self) -> dict:
        data = self._get_meter_data()
        return {
            'last_energa_update': data.reading_time if data else None
        }


class EnergaTariffSensor(EnergaLiveSensor):
    """Meters currently associated tariff sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: EnergaCoordinator):
        super().__init__(entry=entry, name_id='tariff', coordinator=coordinator, name='Tariff')
        self._attr_icon = 'mdi:camera-burst'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class EnergaPPEAddressSensor(EnergaLiveSensor):
    """The address of the PPE sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: EnergaCoordinator):
        super().__init__(entry=entry, name_id='ppe_address', coordinator=coordinator, name='PPE address')
        self._attr_icon = 'mdi:map-marker'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class EnergaContractPeriodSensor(EnergaLiveSensor):
    """The string representation of the user's contract period sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: EnergaCoordinator):
        super().__init__(entry=entry, name_id='contract_period', coordinator=coordinator, name='Contract period')
        self._attr_icon = 'mdi:calendar-range'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class EnergaClientTypeSensor(EnergaLiveSensor):
    """The client type sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: EnergaCoordinator):
        super().__init__(entry=entry, name_id='client_type', coordinator=coordinator, name='Client type')
        self._attr_icon = 'mdi:account-box-multiple'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class EnergaSellerSensor(EnergaLiveSensor):
    """The name of the seller sensor"""

    def __init__(self, entry: ConfigEntry, coordinator: EnergaCoordinator):
        super().__init__(entry=entry, name_id='seller', coordinator=coordinator, name='Seller')
        self._attr_icon = 'mdi:account-box-multiple'
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
