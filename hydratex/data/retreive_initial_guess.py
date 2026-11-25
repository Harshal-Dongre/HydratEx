import sqlite3
from dataclasses import dataclass

from hydratex.config.system_config import SystemConfig
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.core.methods.search_methods import SearchMethod
from hydratex.data.get_db_path import get_db_path


@dataclass(frozen=True)
class InitialGuessFuncParams:
    compound_id: str
    compound_name: str
    search_method: SearchMethod
    param_a: float
    param_b: float
    model_type: str

db_path = get_db_path()

def get_initial_guesses_param(sys_config: SystemConfig, search_method: SearchMethod) -> InitialGuessFuncParams:
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
                param_a,
                param_b,
                model_type
            FROM initial_guess_param
            WHERE compound_id = ?
                AND search_method = ?
            """,
            (guest.code, search_method.value)
        )

        row = cursor.fetchone()

        if row is None:
            raise UnsupportedModelError(
                "Initial guess function not implemented. Please raise an issue."
            )

        return InitialGuessFuncParams(
            compound_id = guest.code,
            compound_name = guest.name,
            search_method = search_method,
            **dict(row)
        )
