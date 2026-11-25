import sqlite3
from dataclasses import dataclass

from hydratex.config.system_config import SystemConfig
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.data.get_db_path import get_db_path


@dataclass(frozen=True)
class HenryConstants:
    compound_id: str
    compound_name: str
    H1: float
    H2: float
    H3: float
    H4: float


db_path = get_db_path()

def get_henry_law_parameters(sys_config: SystemConfig) -> HenryConstants:
    """
    Args:
        sys_config: Active simulation parameters and component definitions including Guest, ACM, EOS.

    Returns:

    Raises:
    """

    if not sys_config.is_pure_system:
        raise NotImplementedError(
            "Multiple guests are currently unsupported by HydratEx. Stay tuned."
        )
    
    guest = sys_config.primary_guest

    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute(
        """
            SELECT  
                Henry_1 AS H1, 
                Henry_2 AS H2, 
                Henry_3 AS H3, 
                Henry_4 as H4
            FROM henry_parameters 
            WHERE compound_id = ?
            """,
            (guest.code.upper(),))
        row = cursor.fetchone()

        if row is None:
            raise UnsupportedModelError(
                f"Henry's Law constants for Component '{guest.code.upper()}' not found in database. Raise a feature request."
            )

        return HenryConstants(
            compound_id=guest.code,
            compound_name=sys_config.primary_guest.name,
            **dict(row)
        )
