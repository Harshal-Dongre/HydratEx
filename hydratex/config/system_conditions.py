from dataclasses import dataclass

from hydratex.utils.unit_coverter import PressureUnit, TemperatureUnit


@dataclass
class SystemConditions:
    """
    Represents the raw, operating (non-equilibrium) system condition
    """
    temperature : float | None
    pressure : float | None
    composition: (dict[str, float]) | None = None      # TODO - salt considerations - mixed guest considerations
    TemperatureUnit = TemperatureUnit.KELVIN
    PressureUnit = PressureUnit.MPA


@dataclass
class EquilibriumConditions:
    """
    Represents the phase equilibrium state (one resolved variable)
    """
    temperature : float
    pressure : float
    composition: (dict[str, float]) | None = None

