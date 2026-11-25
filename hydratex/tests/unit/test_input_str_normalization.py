import pytest

from hydratex.config.input_parameter import InputParameter
from hydratex.config.system_config import ACM, EOS, ACMType, EOSType, Guest
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.data.input_str_normalization import validate_str_input


@pytest.mark.parametrize(
    "input_type, expected_outcome",
    [
        (
                InputParameter(guest_input='ch4', acm_input='ideal', eos_input='pt'),
                (
                        EOS(eos_type=EOSType.PT, code='pt', name='Patel-Teja',
                            description='Cubic EoS well-suited for diverse high pressure systems'),
                        ACM(acm_type=ACMType.IDEAL, code='ideal', name='Ideal',
                            description='Phase behavior with zero excess properties and identical molecular interactions'),
                        Guest(code='ch4', name='Methane',
                              description='Primary structure I hydrate former, light paraffin')
                )),
        (
                InputParameter(guest_input='co2', acm_input='uniquac', eos_input='pr'),
                (EOS(eos_type=EOSType.PR,
                     code='pr',
                     name='Peng-Robinson',
                     description='Standard cubic EoS well-suited for hydrocarbon systems'),
                 ACM(acm_type=ACMType.UNIQUAC,
                     code='uniquac',
                     name='Universal Quasi Chemical',
                     description='Phase behavior adjusted for molecular size and surface '
                                 'energy'),
                 Guest(code='co2',
                       name='Carbon dioxide',
                       description='Common acid gas hydrate former, structure I'))

        )
    ]
)
def test_normalize_and_validate_input_parameters(input_type, expected_outcome):
    results = validate_str_input(input_type)

    assert results == expected_outcome


@pytest.mark.parametrize(
    "input_params, match_msg",
    [
        (
                InputParameter(
                    guest_input="c4h10", acm_input="uniquac", eos_input="pr"
                ),
                r"GUEST type 'C4H10' is not currently supported",
        ),
        (
                InputParameter(
                    guest_input="c3h8", acm_input="unknown", eos_input="pr"
                ),
                r"ACM type 'UNKNOWN' is not currently supported by HydratEx. Please raise a feature request.",
        ),

    ],
)
def test_normalize_and_validate_input_params_error(input_params, match_msg):
    with pytest.raises(UnsupportedModelError, match=match_msg):
        validate_str_input(input_params=input_params)
