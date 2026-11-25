import logging

from hydratex.config.default_config_loader import load_default_config
from hydratex.config.input_parameter import InputParameter
from hydratex.config.system_config import GuestComponent, SystemConfig
from hydratex.data.input_flt_normalization import validate_float_input
from hydratex.data.input_str_normalization import validate_str_input

logger = logging.getLogger(__name__)


# check support in database and normalize input for simulation
def validate_input_params(input_params: InputParameter):

    if (input_params.lower_bound is not None) and (input_params.lower_bound == input_params.upper_bound):
        raise ValueError(
            f"Lower bound '{input_params.lower_bound}' cannot be equal to upper bound '{input_params.upper_bound}'."
        )

    if input_params.eos_input is None or input_params.acm_input is None:
        input_params.eos_input, input_params.acm_input = populate_empty_inputs(input_params)

    eos_config, acm_config, guest_config = validate_str_input(input_params)
    hydrate_structure = validate_float_input(
        input_params=input_params,
        guest=guest_config
    )

    sys_config = SystemConfig(
        eos_config=eos_config,
        acm_config=acm_config,
        components=(GuestComponent(guest=guest_config, mole_fraction=1),),
        hyd_structure=hydrate_structure,
    )

    return sys_config


def populate_empty_inputs(input_params: InputParameter):
    default_config = load_default_config()  # YAML config

    if input_params.eos_input is None:
        input_params.eos_input = default_config["default_eos"].lower()

        logger.info(f"Missing EOS input, using {default_config["default_eos"].upper()} as EOS instance",
                    extra={'phase': "VALIDATION"})

    if input_params.acm_input is None:
        input_params.acm_input = default_config["default_acm"].lower()

        logger.info(f"Missing ACM input, using {default_config["default_acm"].upper()} as ACM instance",
                    extra={'phase': "VALIDATION"})

    return input_params.eos_input, input_params.acm_input



