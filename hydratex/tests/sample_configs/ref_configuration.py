from hydratex.config.input_parameter import InputParameter
from hydratex.config.system_config import (
        ACM,
        EOS,
        ACMType,
        EOSType,
        Guest,
        GuestComponent,
        StructureType,
        SystemConfig,
)
from hydratex.core.hydrate.hydrate_structure import get_hydrate_cage_properties
from hydratex.core.methods.search_methods import SearchMethod
from hydratex.data.create_guest_bundle import GuestBundle
from hydratex.data.retreive_acm_parameters import ActivityCoeffParams, UniQuacParams
from hydratex.data.retreive_critical_properties import CriticalProperties
from hydratex.data.retreive_henry_law_constant import HenryConstants
from hydratex.data.retreive_initial_guess import InitialGuessFuncParams
from hydratex.data.retreive_kihara_parameters import KiharaParameters

TEST_SYSTEM_CONFIGURATION = SystemConfig(
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


GUEST = Guest(
        code="ch4",
        name="Methane",
        description="Primary structure I hydrate former, light paraffin",
    )

CRITICAL_PROPERTY = CriticalProperties(
        compound_id="ch4",
        compound_name="Methane",
        Tc=190.564,
        Pc=4.599,
        Vc=98.6,
        acentric=0.0115,
    )

HENRY_CONSTANT = HenryConstants(
        compound_id="ch4",
        compound_name="Methane",
        H1=-183.786,
        H2=9112.582,
        H3=25.0405,
        H4=-0.00015,
    )

KIHARA_PARAMETER = KiharaParameters(
        sigma=3.2607e-10, epsilon=153.0596, core=3.834e-11
    )

INITIATION_PARAMETER = InitialGuessFuncParams(
        compound_id="ch4",
        compound_name="Methane",
        search_method=SearchMethod.PRESSURE_SEARCH,
        param_a=0.11215677565793201,
        param_b=-29.740628337235222,
        model_type="ln P = a*T + b",
    )

ACM_PARAMETER = ActivityCoeffParams(
        acm_type=ACMType.UNIQUAC,
        components=GUEST.code,
        parameters=UniQuacParams(
            r_params={"ch4": 1.152, "h2o": 1.4},
            q_params={"ch4": 1.12393, "h2o": 0.92},
            tau_ij={("ch4", "h2o"): -1.67, ("h2o", "ch4"): 11.68},
        ),
    )

HYDRATE_LATTICE_PROPERTIES = get_hydrate_cage_properties(
        structure=StructureType.SI)

GUEST_BUNDLE = GuestBundle(
        compound_id=GUEST,
        critical_property=CRITICAL_PROPERTY,
        henry_constant=HENRY_CONSTANT,
        kihara_parameters=KIHARA_PARAMETER,
        initiation_param=INITIATION_PARAMETER,
        acm_parameters=ACM_PARAMETER,
        hydrate_lattice=HYDRATE_LATTICE_PROPERTIES
    )

GUEST_BUNDLE_DICT = {'ch4': GUEST_BUNDLE}


SINGLE_INPUT_PARAMETERS = InputParameter(
    guest_input = 'ch4',
    eos_input = 'pt',
    acm_input = 'uniquac',
    temperature = 285
)

SWEEP_INPUT_PARAMETERS = InputParameter(
    guest_input = 'ch4',
    eos_input = 'pt',
    acm_input = 'uniquac',
    is_temp = True,
    lower_bound = 275,
    upper_bound = 280,
    step_size = 1,
)