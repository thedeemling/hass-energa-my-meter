"""Energa supports getting different kind of statistics via the mode parameter"""
from enum import Enum


class EnergaStatsModes(Enum):
    """A list of possible statistics modes"""
    ENERGY_CONSUMED = 'A+'
    ENERGY_PRODUCED = 'A-'


class EnergaStatsTypes(Enum):
    """A list of possible statistics types"""
    DAY = 'DAY'
    WEEK = 'WEEK'
    MONTH = 'MONTH'
    YEAR = 'YEAR'
