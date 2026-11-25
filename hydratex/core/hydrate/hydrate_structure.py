import sqlite3
from dataclasses import dataclass
from fractions import Fraction

from hydratex.config.system_config import Guest, StructureType
from hydratex.data.get_db_path import get_db_path


@dataclass
class CavityData:
    """Stores geometric and structural properties of a specific cavity type."""
    name: str                       # [cavity type]
    radius: float                   # [radius of cavity in Angstrom]
    coordination: int               # [coordination number of a cage]
    cages_number: int               # [number of cages of particular type in a unit hydrate lattice]
    water_molecules : int           # [number of water molecules constituting a unit hydrate lattice - both small and large cages combined]


@dataclass
class HydrateLattice:
    structure: StructureType
    small: CavityData
    large: CavityData


@dataclass
class OccupancyData:
    LangmuirConst: float
    FractionalOcc: float

@dataclass
class HydrateMixedOccupancy:
    structure: StructureType
    small: dict[Guest, OccupancyData]
    large: dict[Guest, OccupancyData]

@dataclass
class HydratePureOccupancy:
    structure: StructureType
    guest: Guest
    small: OccupancyData
    large: OccupancyData


db_path = get_db_path()

def get_hydrate_cage_properties(
        structure: StructureType,
        ref_dataset: str = 'Sloan'
)->HydrateLattice:

    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row

        rows = db.execute(
        """SELECT
                cage_structure AS name,
                cage_radius AS radius,
                coordination_number AS coordination,
                number_of_cages AS cages_number,
                h2o_per_cavity AS water_molecules,
                cage_name

            FROM 
                crystallographic_data
            WHERE
                structure = ?
                AND data_source = ?
        """,
            (
                structure.value, 
                ref_dataset,
            )
        ).fetchall()

    by_cage = {
        row["cage_name"]: CavityData(
            name=row["name"],
        radius=row["radius"],
        coordination=row["coordination"],
        cages_number=row["cages_number"],
        water_molecules=row["water_molecules"],
        )
        for row in rows 
    }

    return HydrateLattice(
        structure=structure,
        small = by_cage["small"],
        large = by_cage["large"]
    )


@dataclass(frozen=True)
class HydrateThermoData:
    cage_per_water: tuple[Fraction, Fraction]
    ref_volume: float              # cm³/mol at T_REF = 273.15 K
    ref_chemical_potential: float  # J/mol (empty hydrate lattice)
    del_hw0_above_ice: float       # J/mol when T > 273.15 K
    del_hw0_below_ice: float       # J/mol when T <= 273.15 K


STRUCTURE_REF_DATA: dict[StructureType, HydrateThermoData] = {
    StructureType.SI: HydrateThermoData(
        cage_per_water=(Fraction(1, 23), Fraction(3, 23)),
        ref_volume=4.6,
        ref_chemical_potential=1263.6,
        del_hw0_above_ice=-4858.9,
        del_hw0_below_ice=1151.0,
    ),
    StructureType.SII: HydrateThermoData(
        cage_per_water=(Fraction(2, 17), Fraction(1, 17)),
        ref_volume=5.0,
        ref_chemical_potential=882.8,
        del_hw0_above_ice=-5202.2,
        del_hw0_below_ice=808.0,
    ),
}
