import sqlite3
from dataclasses import dataclass

from hydratex.config.system_config import ACMType, SystemConfig
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.data.get_db_path import get_db_path

db_path = get_db_path()



# Model-Specific Parameter Dataclasses
@dataclass(frozen=True)
class UniQuacParams:
    r_params: dict[str, float]
    q_params: dict[str, float]
    tau_ij: dict[tuple[str, str], float]


@dataclass(frozen=True)
class IdealACMParams:
    pass  # Ideal case - no interaction parameters


# Wrapper - ACM type and its corresponding parameters
@dataclass(frozen=True)
class ActivityCoeffParams:
    acm_type: ACMType
    components: str | list[str]
    parameters: UniQuacParams | IdealACMParams


def get_uniquac_parameters(sys_config: SystemConfig) -> UniQuacParams:
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row

        if not sys_config.is_pure_system:
            raise NotImplementedError("Multi-guest queries are not yet supported.")

        guest_codes: tuple[str, ...] = (sys_config.primary_guest.code, "h2o")
        placeholders = ",".join(["?"] * len(guest_codes))

        r_params = {}
        q_params = {}

        pure_query = f"""
            SELECT compound_id, q_parameter, r_parameter
            FROM uniquac_structure
            WHERE compound_id IN ({placeholders})
            """

        for row in db.execute(pure_query, guest_codes):
            code = row["compound_id"]
            r_params[code] = row["r_parameter"]
            q_params[code] = row["q_parameter"]

        binary_query = f"""
            SELECT compound_i, compound_j, tau_ij
            FROM uniquac_interactions
            WHERE compound_i IN ({placeholders})
                AND compound_j IN ({placeholders})
            """

        tau_ij = {}

        for row in db.execute(binary_query, guest_codes + guest_codes):
            pair = (row["compound_i"], row["compound_j"])
            tau_ij[pair] = row["tau_ij"]

        return UniQuacParams(r_params=r_params, q_params=q_params, tau_ij=tau_ij)


def get_acm_parameters(sys_config: SystemConfig) -> ActivityCoeffParams:

    acm_instance = sys_config.acm_config.acm_type

    if not sys_config.is_pure_system:
        raise NotImplementedError(
            "Multiple guests are currently unsupported by HydratEx. Stay tuned."
        )
    
    guest = sys_config.primary_guest
    
    if acm_instance == ACMType.UNIQUAC:
        acm_parameters = get_uniquac_parameters(sys_config=sys_config)

    elif acm_instance == ACMType.IDEAL:
        acm_parameters = IdealACMParams()

    else:
        raise UnsupportedModelError(
            f"Unsupported ACM '{acm_instance}' type. Raise a feature request."
        )

    return ActivityCoeffParams(
        acm_type = acm_instance,
        components = guest.code,
        parameters = acm_parameters,
    )

