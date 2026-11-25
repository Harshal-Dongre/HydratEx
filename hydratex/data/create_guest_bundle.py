from dataclasses import dataclass

from hydratex.config.system_config import SystemConfig
from hydratex.core.hydrate.hydrate_structure import (
    HydrateLattice,
    get_hydrate_cage_properties,
)
from hydratex.core.methods.search_methods import SearchMethod
from hydratex.data.input_str_normalization import Guest
from hydratex.data.retreive_acm_parameters import (
    ActivityCoeffParams,
    get_acm_parameters,
)
from hydratex.data.retreive_critical_properties import (
    CriticalProperties,
    get_critical_properties,
)
from hydratex.data.retreive_henry_law_constant import (
    HenryConstants,
    get_henry_law_parameters,
)
from hydratex.data.retreive_initial_guess import (
    InitialGuessFuncParams,
    get_initial_guesses_param,
)
from hydratex.data.retreive_kihara_parameters import (
    KiharaParameters,
    get_kihara_parameters,
)


@dataclass (frozen=True)
class GuestBundle:
    compound_id: Guest
    critical_property: CriticalProperties
    henry_constant: HenryConstants
    kihara_parameters: KiharaParameters
    initiation_param: InitialGuessFuncParams
    acm_parameters: ActivityCoeffParams
    hydrate_lattice: HydrateLattice

class GuestBundleData:
    """
    Retrieve model parameters from the database using SQL and return them as a bundle data structure.
    """
    def __init__(self,
                 sys_config: SystemConfig,
                 search_method:SearchMethod):
        """
        Args:
            sys_config: Validated system configuration data for HydratEx simulation.
            search_method: Search method to use for the concerned simulation configuration.
        """

        self.sys_config = sys_config
        self.search_method = search_method

    def populate(self) -> GuestBundle:
        """
        Populates the bundle data structure with:
            - Critical properties (phase boundaries)
            - Henry constants (solubility estimates)
            - Kihara parameters (optimized for a given system)
            - Initial guess (fast equilibrium computes)
            - Activity coefficients parameters (liquid phase non-idealities)
            - Hydrate lattice crystallographic data
        Returns:

        """
        crit_properties = get_critical_properties(sys_config=self.sys_config)
        henry_constants = get_henry_law_parameters(sys_config=self.sys_config)
        kihara_parameters = get_kihara_parameters(sys_config=self.sys_config)
        initial_guesses = get_initial_guesses_param(sys_config=self.sys_config, search_method=self.search_method)
        acm_parameters = get_acm_parameters(sys_config=self.sys_config)
        hydrate_crystal_data = get_hydrate_cage_properties(structure=self.sys_config.hyd_structure, ref_dataset='Sloan')

        return GuestBundle(
            compound_id=self.sys_config.primary_guest,  # TODO - multiple guests
            critical_property=crit_properties,
            henry_constant=henry_constants,
            kihara_parameters=kihara_parameters,
            initiation_param=initial_guesses,
            acm_parameters=acm_parameters,
            hydrate_lattice=hydrate_crystal_data
        )

