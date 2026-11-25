import pytest

from hydratex.config.input_parameter import InputParameter
from hydratex.core.exceptions import UnsupportedModelError, UnsupportedRangeError
from hydratex.data.input_validation import validate_input_params


def test_validate_input_params_empty_eos_acm():
    input_params = InputParameter(
        eos_input=None,
        acm_input=None,
        guest_input='ch4',
        temperature=285.15
    )

    sys_config = validate_input_params(input_params)

    assert sys_config.components[0].guest.code == "ch4"
    assert sys_config.eos_config.code == "pt"
    assert sys_config.acm_config.code == "uniquac"


def test_validate_input_params():
    input_params = InputParameter(
        eos_input='pr',
        acm_input='ideal',
        guest_input='c2h6',
        temperature=259.15
    )

    sys_config = validate_input_params(input_params)

    assert sys_config.components[0].guest.name == "Ethane"
    assert sys_config.acm_config.name == "Ideal"
    assert sys_config.eos_config.name == "Peng-Robinson"


def test_validate_input_params_temp_out_range():
    input_params = InputParameter(
        guest_input='ch4',
        temperature=100
    )

    with pytest.raises(UnsupportedRangeError,
                       match=r"Temperature = \[100\.\] K is below supported minimum \[250\.0\] K for CH4 system\."):
        validate_input_params(input_params)


def test_validate_input_params_unknown_type():
    input_params = InputParameter(
        guest_input='ch4',
        temperature=300,
        eos_input='unknown',
    )

    with pytest.raises(UnsupportedModelError,
                       match=r"EOS type 'UNKNOWN' is not currently supported by HydratEx\. Please raise a feature request\."):
        validate_input_params(input_params)
