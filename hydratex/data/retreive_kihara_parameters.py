import sqlite3
from dataclasses import dataclass

from hydratex.config.system_config import SystemConfig
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.data.get_db_path import get_db_path


@dataclass(frozen=True)
class KiharaParameters:
    sigma: float
    epsilon: float
    core: float = 0.0  # defaults to zero if not specified

db_path = get_db_path()

def get_kihara_parameters(sys_config: SystemConfig) -> KiharaParameters:
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        if not sys_config.is_pure_system:
            raise NotImplementedError(
                "Multiple guests are currently unsupported by HydratEx. Stay tuned."
            )
        
        guest = sys_config.primary_guest


        cursor.execute(
            """
                SELECT
                    sigma,
                    epsilon,
                    core
                FROM optimized_kihara_parameters
                WHERE
                    compound_id = ?
                    AND eos_instance = ?
                    AND acm_instance = ?
            """,
            (
                guest.code,
                sys_config.eos_config.code,
                sys_config.acm_config.code,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            raise UnsupportedModelError(
                f"Kihara parameters missing for guest '{guest.code}'. Please raise an issue or use experimental model to obtain Kihara parameters."
            )

        return KiharaParameters(
            **dict(row)
        )