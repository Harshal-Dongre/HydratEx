class PressureUnit:
    MPA = "MPa"
    KPA = "kPa"
    PA = "Pa"
    BAR = "bar"
    ATM = "atm"
    PSI = "psi"
    KG_CM2 = "kg/cm²"


class TemperatureUnit:
    KELVIN = "Kelvin"
    CELSIUS = "°C"
    FAHRENHEIT = "°F"



def convert_pressure(value, from_unit, to_unit):
    # MPa as base unit
    conversion_factor = {
        PressureUnit.MPA: 1.0,
        PressureUnit.KPA: 0.001,
        PressureUnit.PA: 1e-6,
        PressureUnit.BAR: 0.1,
        PressureUnit.ATM: 0.101325,
        PressureUnit.PSI: 0.00689476,
        PressureUnit.KG_CM2: 0.0980665
    }

    value_in_mpa = value * conversion_factor[from_unit]

    return value_in_mpa / conversion_factor[to_unit]

def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:

    # Kelvin as base unit
    if from_unit == TemperatureUnit.KELVIN:
        temp_in_k = value
    elif from_unit == TemperatureUnit.CELSIUS:
        temp_in_k = value + 273.15
    elif from_unit == TemperatureUnit.FAHRENHEIT:
        temp_in_k = (value - 32) * 5/9 + 273.15
    else:
        raise ValueError(f"Unsupported source temperature unit: {from_unit}")

    # Convert from Kelvin to target unit
    if to_unit == TemperatureUnit.KELVIN:
        return temp_in_k
    elif to_unit == TemperatureUnit.CELSIUS:
        return temp_in_k - 273.15
    elif to_unit == TemperatureUnit.FAHRENHEIT:
        return (temp_in_k - 273.15) * 9/5 + 32
    else:
        raise ValueError(f"Unsupported target temperature unit: {to_unit}")

