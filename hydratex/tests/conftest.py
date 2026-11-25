import pytest

from hydratex.config.input_parameter import InputParameter
from hydratex.config.system_conditions import SystemConditions
from hydratex.config.system_config import (
    ACM,
    EOS,
    ACMType,
    EOSType,
    Guest,
    GuestComponent,
    SimulationFlags,
    SystemConfig,
)
from hydratex.core.hydrate.hydrate_structure import (
    StructureType,
    get_hydrate_cage_properties,
)
from hydratex.core.methods.search_methods import SearchMethod
from hydratex.data.create_guest_bundle import GuestBundle
from hydratex.data.retreive_acm_parameters import ActivityCoeffParams, UniQuacParams
from hydratex.data.retreive_critical_properties import CriticalProperties
from hydratex.data.retreive_henry_law_constant import HenryConstants
from hydratex.data.retreive_initial_guess import InitialGuessFuncParams
from hydratex.data.retreive_kihara_parameters import KiharaParameters


@pytest.fixture
def std_sys_condition():
    """Test operating conditions"""
    return SystemConditions(
        temperature=285,    # Kelvins
        pressure = 9.04,    # MPa
    )

@pytest.fixture
def std_guest_ch4():
    """Guest object with standard CH4 (methane) data."""
    return Guest(
        code="ch4",
        name="Methane",
        description="Primary structure I hydrate former, light paraffin.",
    )


@pytest.fixture
def std_guest_unsupported():
    """Guest object with an invalid or unsupported code."""
    return Guest(
        code="unknown_gas", name="Unknown", description="Unsupported test species."
    )


@pytest.fixture
def std_sys_config():
    """System Configuration object with standard test data."""
    return SystemConfig(
        components=(
            GuestComponent(
                guest=Guest(
                    code="ch4",
                    name="Methane",
                    description="Primary structure I hydrate former, light paraffin",
                ),
                mole_fraction=1,
            ),
        ),
        hyd_structure=StructureType.SI,
        eos_config=EOS(
            eos_type=EOSType.PT,
            code="pt",
            name="Patel-Teja",
            description="Cubic EoS well-suited for diverse high pressure systems",
        ),
        acm_config=ACM(
            acm_type=ACMType.UNIQUAC,
            code="uniquac",
            name="Universal Quasi Chemical",
            description="Phase behavior adjusted for molecular size and surface energy",
        ),
    )


@pytest.fixture
def std_unknown_sys_config():
    """System Configuration object with invalid test data."""
    return SystemConfig(
        components=(
            GuestComponent(
                guest=Guest(
                    code="unknown_guest",
                    name="unknown guest",
                    description="unknown guest description",
                ),
                mole_fraction=1,
            ),
        ),
        hyd_structure=StructureType.SI,
        eos_config=EOS(
            eos_type=EOSType.PT,
            code="unknown_eos",
            name="unknown eos",
            description="unknown eos description",
        ),
        acm_config=ACM(
            acm_type=ACMType.UNIQUAC,
            code="unknown_acm",
            name="unknown acm",
            description="unknown acm description",
        ),
    )


@pytest.fixture
def std_guest_bundle_dict():
    """A fully configured GuestBundle object for Methane guest."""

    guest = Guest(
        code="ch4",
        name="Methane",
        description="Primary structure I hydrate former, light paraffin",
    )

    crit_property = CriticalProperties(
        compound_id="ch4",
        compound_name="Methane",
        Tc=190.564,
        Pc=4.599,
        Vc=98.6,
        acentric=0.0115,
    )

    henry_const = HenryConstants(
        compound_id="ch4",
        compound_name="Methane",
        H1=-183.786,
        H2=9112.582,
        H3=25.0405,
        H4=-0.00015,
    )

    kihara_params = KiharaParameters(
        sigma=3.2607e-10, epsilon=153.0596, core=3.834e-11
    )

    initiation_params = InitialGuessFuncParams(
        compound_id="ch4",
        compound_name="Methane",
        search_method=SearchMethod.PRESSURE_SEARCH,
        param_a=0.11215677565793201,
        param_b=-29.740628337235222,
        model_type="ln P = a*T + b",
    )

    acm_params = ActivityCoeffParams(
        acm_type=ACMType.UNIQUAC,
        components=guest.code,
        parameters=UniQuacParams(
            r_params={"ch4": 1.152, "h2o": 1.4},
            q_params={"ch4": 1.12393, "h2o": 0.92},
            tau_ij={("ch4", "h2o"): -1.67, ("h2o", "ch4"): 11.68},
        ),
    )

    hydrate_crystal_info = get_hydrate_cage_properties(
        structure=StructureType.SI)

    return {'ch4': GuestBundle(
        compound_id=guest,
        critical_property=crit_property,
        henry_constant=henry_const,
        kihara_parameters=kihara_params,
        initiation_param=initiation_params,
        acm_parameters=acm_params,
        hydrate_lattice=hydrate_crystal_info
    )}


@pytest.fixture
def std_single_sim_input():
    """A fully configured single point InputParameter object for Methane guest."""
    return InputParameter(
    guest_input = 'ch4',
    eos_input = 'pt',
    acm_input = 'uniquac',
    temperature = 285
)

@pytest.fixture
def std_sweep_input():
    """A fully configured sweep InputParameter object for Methane guest."""
    return InputParameter(
    guest_input = 'c2h6',
    eos_input = 'pt',
    acm_input = 'uniquac',
    is_temp = True,
    lower_bound = 275,
    upper_bound = 280,
    step_size = 1,
)

@pytest.fixture
def std_simulation_flags():
    """Simulation flags instance"""
    return SimulationFlags(
        verbose=False,
        save_files=False
    )