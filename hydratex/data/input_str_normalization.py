"""Strings Input Normalization and Validation Module for HydratEx.

This module acts as the gateway layer between raw user-supplied string configurations
and core thermodynamic model instances. It queries the local SQLite registry database
to validate aliases, resolve primary keys, map enumeration types, and instantiate
fully-configured EOS, ACM, and Guest objects for simulation orchestration.

Core Operations:
    - Alias resolution via `{input_type}_aliases` tables.
    - Enumeration mapping via `EOSType` and `ACMType` registries.
    - Database retrieval of canonical names and descriptions.
    - Dynamic factory instantiation using model builders.
"""

import sqlite3

from hydratex.config.input_parameter import InputParameter
from hydratex.config.system_config import ACM, EOS, ACMType, EOSType, Guest
from hydratex.core.exceptions import UnsupportedModelError
from hydratex.data.get_db_path import get_db_path

db_path = get_db_path()

# import registry from System Config
MODEL_CLASSES = {"eos": EOS,
                 "acm": ACM,
                 "guest": Guest,
                 }


def validate_str_input(input_params: InputParameter):
    """
    Normalizes raw user input parameters into validated thermodynamic
    phase equilibrium model configurations for HydratEx.

    Args:
        input_params (InputParameter): Container holding raw string values
        for guest, ACM and EOS models.

    Returns:
        dict | tuple: Standardized model instances (EOS, ACM, Guest) ready for
        simulation orchestration.

    Raises:
      UnsupportedModelError: If any provided model key, guest type, or input
        category is not recognized or supported by the HydratEx registry.
    """


    eos_config = normalize_eos(input_params.eos_input)
    acm_config = normalize_acm(input_params.acm_input)
    guest_config = normalize_guest(input_params.guest_input)

    return eos_config, acm_config, guest_config


def normalize_instance(input_type: str, input_value: str):
    """
    Generalized helper function that creates Model classes for system configuration
    dataclasses (EOS, ACM, Guest) based on raw user inputs.

    Args:
        input_type: Type of container to create - EOS, ACM or Guest.
        input_value: Raw user input string value associated with the container.

    Returns:
        Model class containing Model_Type, Model_Key, Model_canonical_name, Model_description
         for any of the EOS, ACM, Guest inputs.

    """

    i_type = input_type.lower()
    if i_type not in MODEL_CLASSES:
        raise UnsupportedModelError(f"Input type '{input_type}' not recognized.")

    model_key = fetch_model_key(input_type, input_value)
    enum_type = get_enum_type(input_type, model_key)
    canonical_name, description = fetch_model_details(input_type, model_key)

    builder = MODEL_CLASSES[i_type]
    return builder.create(enum_type, model_key, canonical_name, description)


def normalize_eos(eos_instance):
    return normalize_instance("eos", eos_instance)

def normalize_acm(acm_instance):
    return normalize_instance("acm", acm_instance)

def normalize_guest(guest):
    return normalize_instance("guest", guest)


def fetch_model_key(input_type: str, input_value: str):
    """
    Validates user string inputs against the HydratEx registry using database queries.

    Args:
        input_type: Type of container to create - EOS, ACM or Guest.
        input_value: Raw user input string value associated with the container.

    Returns:
        Model_code which serves are primary key for EOS, ACM, Guest instances used across HydratEx.

    Raises:
        UnsupportedModelError: If any provided model key, guest type, or input is not supported.
    """

    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        query = f"SELECT {input_type}_code FROM {input_type}_aliases WHERE alias = ?"

        try:
            cursor.execute(query, (input_value,))
            row = cursor.fetchone()

            if row is None:
                raise UnsupportedModelError(
                    f"{input_type.upper()} type '{input_value.upper()}' is not currently supported by HydratEx. Please raise a feature request."
                )

            return row[f"{input_type}_code"]

        except sqlite3.OperationalError as e:
            raise RuntimeError(f"Database table does not exist or SQL is broken: {e}")


def get_enum_type(input_type: str, clean_input: str):
    """
    Enumerates validated inputs to the appropriate data containers for use across simulation engine.

    Args:
        input_type: Type of container to create - EOS, ACM or Guest.
        clean_input: Cleaned and validated user input string.

    Returns:
        Enum type corresponding to the specified input type (EOS, ACM, Guest).

    Raises:
        UnsupportedModelError: If any provided model key, guest type, or input is not supported.

    """

    i_type = input_type.lower()
    c_upper = clean_input.upper()

    if i_type == "eos":
        try:
            return EOSType[c_upper]
        except KeyError:
            raise UnsupportedModelError(
                f"EOS model '{c_upper}' is not currently supported by HydratEx."
            )
    elif i_type == "acm":
        try:
            return ACMType[c_upper]
        except KeyError:
            raise UnsupportedModelError(
                f"ACM model '{c_upper}' is not currently supported by HydratEx."
            )
    elif i_type == "guest":
        return None
    else:
        raise UnsupportedModelError(
            f"Input type '{input_type.upper()}' is not recognized by HydratEx."
        )


def fetch_model_details(input_type, clean_input):
    """
    Fetches model details associated with an EOS, ACM, Guest from database queries.

    Args:
        input_type: Type of container to use - EOS, ACM or Guest.
        clean_input: Cleaned and validated user input string.

    Returns:
        canonical_name: Complete name of the method set to be used.
        description: Description of the method set to be used for simulation.

    """

    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        query = f"""
                SELECT
                    canonical_name,
                    description
                FROM 
                    {input_type}_models
                WHERE
                    code = ?
                """

        try:
            cursor.execute(query, (clean_input,))
            row = cursor.fetchone()

            if row is None:
                raise UnsupportedModelError(
                    f"{input_type.upper()} type '{clean_input.upper()}' is not currently supported by HydratEx."
                )

            return row["canonical_name"], row["description"]

        except sqlite3.OperationalError:
            raise RuntimeError("Database table does not exist or SQL is broken")

