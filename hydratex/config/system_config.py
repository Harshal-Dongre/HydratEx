from dataclasses import dataclass
from enum import StrEnum

import numpy as np

"""
Dataclass file

Builds dataclass for a simulation instance.
A dataclass instance is based upon: 
    * components
    * hydrate structure
    * equation of state model
    * activity coefficient model 
"""

# --- Supported ACM models ---
class ACMType(StrEnum):
    IDEAL = "ideal"
    UNIQUAC = "uniquac"

# --- Supported EOS models ---
class EOSType(StrEnum):
    PR = "peng robinson"
    PT = 'patel teja'
    # SRK = 'soave redlich kwong'         # TODO - Implement this model -

# --- Supported Hydrate structures ---
class StructureType(StrEnum):
    """Defines the primary hydrate structure families."""
    SI = 'sI'
    SII = 'sII'
    SH = 'sH'


@dataclass
class Guest:
    code: str
    name: str
    description: str
    @classmethod
    def create(cls, _enum_val, code, name, desc):
        return cls(code=code, name=name, description=desc)

@dataclass
class EOS:
    eos_type: EOSType
    code: str 
    name: str
    description: str

    @classmethod
    def create(cls, enum_val, code, name, desc):
        return cls(eos_type=enum_val, code=code, name=name, description=desc)


@dataclass
class ACM:
    acm_type: ACMType
    code: str 
    name: str 
    description: str 

    @classmethod
    def create(cls, enum_val, code, name, desc):
        return cls(acm_type=enum_val, code=code, name=name, description=desc)


@dataclass(frozen=True)
class GuestComponent:
    guest: Guest
    mole_fraction: float 


@dataclass(frozen=True)
class SystemConfig:  # for thermodynamic definitions only
    components: tuple[GuestComponent, ...]
    hyd_structure: StructureType
    eos_config: EOS
    acm_config: ACM

    def __post_init__(self) -> None:
        if not self.components:
            raise ValueError("SystemConfig requires at least one component.")

    @property
    def all_guests(self) -> tuple[Guest,...]:
        """Get all Guest in a single flat tuple."""
        return tuple(c.guest for c in self.components)

    @property
    def all_guests_codes(self) -> list[str]:
        """All guest codes as a list of strings."""
        return [c.guest.code for c in self.components]
    
    @property
    def is_pure_system(self) -> bool:
        """Branch between pure and multi-component guests."""
        return len(self.components) == 1

    @property
    def primary_guest(self) -> Guest:
        """1-element tuple for pure-system access."""
        if not self.is_pure_system:
            raise ValueError("primary_guest is only valid for pure systems.")
        return self.components[0].guest


@dataclass(frozen=True)
class SolverSettings:
    x_tol = np.float64(1e-8)
    r_tol = np.float64(1e-6)
    max_iter: int = 108     # no overboard this - 54 iterations - 10^-16 precision
    p_tol: float = 1e-4     # absolute pressure tolerance

HYDRATEX_SETTINGS = SolverSettings()

@dataclass(frozen=True)
class SimulationFlags:
    verbose: bool = False
    save_files: bool = False
