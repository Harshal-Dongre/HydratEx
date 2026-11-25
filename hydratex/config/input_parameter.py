from pydantic import BaseModel


class InputParameter(BaseModel):
    guest_input: str | None = None
    eos_input: str | None = None
    acm_input: str | None= None
    is_temp: bool | None = None 


    # single point evaluation
    temperature: float | None = None
    pressure: float | None = None

    # sweep evaluation
    lower_bound: float | None = None
    upper_bound: float | None = None
    step_size: float | None = None

