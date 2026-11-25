import sqlite3
from dataclasses import dataclass

from hydratex.config.system_config import SystemConfig
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.data.get_db_path import get_db_path


@dataclass(frozen=True)
class CriticalProperties:
    compound_id: str
    compound_name: str
    Tc: float
    Pc: float
    Vc: float
    acentric: float
    # MW: Optional[float] --> TODO add this

db_path = get_db_path()

def get_critical_properties(sys_config: SystemConfig) -> CriticalProperties:
    """
    Helper function which queries and retrieves the critical properties of a
    requested hydrate former guest molecule from the database.

    Args:
        sys_config: Active simulation parameters and component definitions including Guest, ACM, EOS.

    Returns:
        CriticalProperties: A dataclass of critical properties of the concerned
        hydrate former. These include:
            Tc (critical temperature) - Kelvin
            Pc (critical pressure) - MPa
            Vc (critical volume) - cc/mol
            acentric (Pitzer acentric factor)
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
                crit_temperature_K AS Tc, 
                crit_pressure_MPa AS Pc, 
                crit_volume_cc_mol AS Vc, 
                acentricity as acentric
            FROM critical_properties 
            WHERE compound_id = ?
            """,
            (guest.code.upper(),))
        row = cursor.fetchone()

        if row is None:
            raise UnsupportedModelError(
                f"Critical properties for Component '{guest.code.upper()}' not found in database. Raise a feature request."
            )

        return CriticalProperties(
            compound_id=guest.code.upper(),
            compound_name=guest.name,
            **dict(row)
        )

