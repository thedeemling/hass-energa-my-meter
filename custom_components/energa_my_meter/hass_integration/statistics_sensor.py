"""
A special type of sensor that allows to overwrite states for statistics in the past.
As Energa does not report live data, but updates it at most once a day, simply downloading the current meter value
will not create a proper statistics.
"""
import logging
from typing import override

from homeassistant.components.recorder.models import StatisticMetaData
from homeassistant.components.recorder.statistics import async_import_statistics
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .energa_coordinator import EnergaCoordinator
from ..common import generate_stats_base_entity_name, generate_stats_display_name
from ..energa.stats_modes import EnergaStatsModes
from ..hass_integration.base_sensor import EnergaBaseSensor

_LOGGER = logging.getLogger(__name__)


class EnergyStatisticsSensor(CoordinatorEntity, EnergaBaseSensor):
    """
    Representation of Energa statistics sensor.
    This sensor cannot have any current state (will always be shown as unavailable)
    and exists only to keep track of statistics.
    """

    def __init__(
            self,
            entry: ConfigEntry,
            mode: EnergaStatsModes,
            coordinator: EnergaCoordinator,
            zone: str
    ):
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        EnergaBaseSensor.__init__(
            self,
            entry=entry,
            name_id=generate_stats_base_entity_name(mode, zone),
            name=generate_stats_display_name(mode, zone)
        )
        self._mode = mode
        self._zone = zone

        self._attr_icon = 'mdi:meter-electric-outline'
        self._state = None
        self._update_ts = None
        self._next_update_ts = None

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_extra_state_attributes = {}
        self._attr_precision = 5
        self._available = True

    @staticmethod
    def statistics(s: str) -> str:
        """Statistics method"""
        return f'{s}_statistics'

    @override
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handles the update returned by the coordinator"""
        _LOGGER.debug("Updating statistics gathered by the coordinator for %s...", self.entity_id)
        stats = self.coordinator.get_specific_statistic(self._mode, self._zone)
        metadata = StatisticMetaData(
            source="recorder",
            statistic_id=self.entity_id,
            name=self._attr_name,
            unit_of_measurement=self._attr_unit_of_measurement,
            has_mean=False,
            has_sum=True,
        )
        if len(stats) > 0:
            _LOGGER.debug(
                "The coordinator has %s statistics for %s. Saving them as %s => %s...",
                len(stats), self.entity_id,
                metadata,
                stats
            )
            async_import_statistics(self.hass, metadata, stats)
        else:
            _LOGGER.debug('No updates for statistics %s.', self.entity_id)

        super()._handle_coordinator_update()
