import numpy as np

from hydratex.core.hydrate.hydrate_structure import HydratePureOccupancy
from hydratex.data.create_guest_bundle import GuestBundle
from hydratex.utils.unwrap_dict_dataclass import unwrap_single


def calculate_hydration_number(
        cavity_occupancy: HydratePureOccupancy,
        guest_bundle_dict: dict[str, GuestBundle]) -> float:

    bundle = unwrap_single(guest_bundle_dict, "GuestBundleDict unwrap.")
    no_water_molecules = bundle.hydrate_lattice.small.water_molecules
    no_cages_small = bundle.hydrate_lattice.small.cages_number
    no_cages_large = bundle.hydrate_lattice.large.cages_number

    small_cage_occupancy = cavity_occupancy.small.FractionalOcc
    large_cage_occupancy = cavity_occupancy.large.FractionalOcc


    numerator = no_water_molecules
    denominator = np.sum(small_cage_occupancy * no_cages_small +
                      large_cage_occupancy * no_cages_large)

    hydration_number = (numerator / denominator) if denominator else float("inf")
    
    return hydration_number

