import numpy as np
from numba import njit


@njit(cache=True)
def compute_del_n_grid(r_values: np.ndarray,
                       guest_core: float,
                       cavity_radius: float) -> np.ndarray:
    """
    Compute the Del(N) grid for spherical cell potential estimation.

    This function calculates the Del N grid used in hydrate phase equilibrium models,
    incorporating Lennard-Jones interactions and cavity coordination geometry. It is
    Numba-accelerated for performance, as it is computationally intensive, especially
    during temperature search iterations.

    Parameters
    ----------
    r_values : np.ndarray
        Array of radial distances (in Angstroms) from 0 to (cavity_radius - guest_core).

    guest_core : float
        Core parameter of the guest molecule (in Angstroms), representing its size or
        interaction radius.

    cavity_radius : float
        Radius of the cavity (in Angstroms), defining the spatial domain for the Del N
        calculation.

    Returns
    -------
    np.ndarray
        A 2D NumPy array where:
        The first column contains the input `r_values`.
        The next four columns correspond to Del N values for exponents 4, 5, 10, and 11.

    Notes
    -----
    This function is designed for one of the most intensive steps in hydrate phase
    equilibrium modeling. It is Numba-accelerated for speed and efficiency. Avoid
    passing dataclass objects directly; instead, unpack variables and pass scalar
    or array inputs. The calculation is vectorized for exponents 4, 5, 10, and 11.

    Examples
    --------
    >>> from core.properties_n_parameters import MolecularInteractionParams, get_cavity_property  # doctest: +SKIP
    >>> guest = MolecularInteractionParams(sigma=3.58e-10, epsilon=154, core=0.28e-10)  # doctest: +SKIP
    >>> core_guest = guest.core  # doctest: +SKIP
    >>> cavity_prop = get_cavity_property('sI', 'small')  # doctest: +SKIP
    >>> cav_radius = cavity_prop.radius  # doctest: +SKIP
    >>> radius_array = np.arange(0, cav_radius - core_guest, 0.5e-13)  # doctest: +SKIP
    >>> grid = compute_del_n_grid(radius_array, core_guest, cav_radius)  # doctest: +SKIP

    """

    nr = r_values.shape[0]
    n_array = np.array([4, 5, 10, 11])  # Hand and Holder equation
    nn = n_array.size
    del_n_grid = np.empty((nn + 1, nr), dtype=np.float64)

    for i in range(nr):
        r = r_values[i]
        for j in range(nn):
            n_factor = n_array[j]
            term1 = np.power((1 - (r / cavity_radius) - (guest_core / cavity_radius)), -n_factor)
            term2 = np.power((1 + (r / cavity_radius) - (guest_core / cavity_radius)), -n_factor)
            del_n_grid[j + 1, i] = (term1 - term2) / n_factor

    del_n_grid[0, :] = r_values
    return del_n_grid

# TODO - large grid and small grid pre-computation and speed up.

@njit(cache=True)
def compute_spherical_cell_potential(r_values: np.ndarray,
                                     guest_core: float,
                                     guest_sigma: float,
                                     guest_epsilon: float,
                                     cavity_radius: float,
                                     cavity_coordination: int,
                                     temperature: float,
                                     del_n_r_grid: np.ndarray) -> float:
    """
    Computes the spherical cell potential of a single hydrate cavity.

    This potential estimates the net interaction energy between an enclosed guest molecule
    and all surrounding host molecules forming a spherical cavity, based on the
    Lennard-Jones-Devonshire cell theory.

    Parameters
    ----------
        r_values : np.ndarray
            Radial distance array [Å], from 0 to (cavity radius - guest core).

        guest_core : float
            Core radius of the guest molecule [Å].

        guest_sigma : float
            Collision diameter [Å].

        guest_epsilon : float
            Lennard-Jones well depth [1/K].

        cavity_radius : float
            Radius of the cavity [Å].

        cavity_coordination : int
            Coordination number (number of host molecules per cavity).

        temperature : float
            System temperature [K].

        del_n_r_grid : np.ndarray
            Interaction weighting grid (same length as `r_values`).

    Returns
    -------
    float
        Spherical cell potential of the guest molecule in the cavity.

    Notes
    ------
        - Assumes all host molecules are equidistant from the guest at cavity wall.
        - Uses trapezoidal integration over radial range.
        - `len(r_values)` must match `del_n_r_grid.shape[1]`.

    Usages
    >>> from core.properties_n_parameters import MolecularInteractionParams, get_cavity_property # doctest: +SKIP
    >>> guest = MolecularInteractionParams(sigma=3.58e-10, epsilon=154, core = 0.28e-10) # doctest: +SKIP
    >>> core, sigma, epsilon = guest.core, guest.sigma, guest.epsilon # doctest: +SKIP
    >>> cavity_prop = get_cavity_property(structure_key= 'sI', cavity_type= 'small') # doctest: +SKIP
    >>> cav_radius, cav_coord = cavity_prop.radius, cavity_prop.coordination # doctest: +SKIP
    >>> radius_array = np.arange(0, (cav_radius-core)  # doctest: +SKIP
    >>> grid = compute_del_n_grid(r_values= radius_array, guest_core = core, cavity_radius = cav_radius)# doctest: +SKIP
    >>> temp = 270 # doctest: +SKIP
    >>> w_r = compute_spherical_cell_potential(radius_array, core, sigma, epsilon, cav_rad, cav_coord, temp, grid) # doctest: +SKIP
    """

    # del_N_grid to value allotment and re-estimation if size mismatch
    del4n = del_n_r_grid[1, :]
    del5n = del_n_r_grid[2, :]
    del10n = del_n_r_grid[3, :]
    del11n = del_n_r_grid[4, :]

    w_factor = 2 * cavity_coordination * guest_epsilon

    w_term11 = np.power(guest_sigma, 12) / (np.power(cavity_radius, 11) * r_values)
    w_term12 = del10n + ((guest_core / cavity_radius) * del11n)
    w_term21 = np.power(guest_sigma, 6) / (np.power(cavity_radius, 5) * r_values)
    w_term22 = del4n + ((guest_core / cavity_radius) * del5n)

    w_term = w_factor * ((w_term11 * w_term12) - (w_term21 * w_term22))

    integrand_term = np.exp(-w_term / temperature) * np.power(r_values, 2)
    integrand_term = np.nan_to_num(integrand_term, nan=0.0)

    integral_value = np.trapezoid(integrand_term, r_values)

    return float(integral_value)

def safe_cell_potential(r_values: np.ndarray,
                        guest_core: float,
                        guest_sigma: float,
                        guest_epsilon: float,
                        cavity_radius: float,
                        cavity_coordination: int,
                        temperature: float,
                        del_n_r_grid: np.ndarray = None) -> float:
    """
    Safe wrapper around the Numba-accelerated spherical cell potential.

    Automatically recalculates del_n_r_grid if shape mismatch is found.
    """

    if del_n_r_grid is None or r_values.shape[0] != del_n_r_grid.shape[1]:
        # logger.info("Shape mismatch detected. Recalculating del(N) grid instead.")
        del_n_r_grid = compute_del_n_grid(r_values, guest_core, cavity_radius)

    return compute_spherical_cell_potential(r_values,
                                            guest_core,
                                            guest_sigma,
                                            guest_epsilon,
                                            cavity_radius,
                                            cavity_coordination,
                                            temperature,
                                            del_n_r_grid)

