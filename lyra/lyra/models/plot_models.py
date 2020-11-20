from typing import List, Optional

from pydantic import BaseModel, root_validator, validator

from lyra.core.config import config
from lyra.core.utils import flatten_expand_list
from lyra.models.hydstra_models import DataType, Interval

cfg = config()
VALID_VARIABLES = list(cfg["variables"].keys())
VALID_HYDSTRA_SITES = list(cfg["preferred_variables"].keys())


class SingleVarSpec(BaseModel):
    variable: str
    sites: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    intervals: Optional[List[str]] = None
    trace_upstreams: Optional[List[bool]] = None
    agg_methods: Optional[List[str]] = None

    @validator("sites", "intervals", "agg_methods", pre=True)
    def expand_flatten(cls, v):
        if v is not None:
            if isinstance(v, str):
                v = [v]
            return [i for i in flatten_expand_list(v) if i]

    # @validator("sites")
    # def check_sites(cls, v):
    #     # for site in v:
    #     #     assert site in VALID_SITES, f"invalid site: `{site}`"
    #     return v

    @validator("variable")
    def check_variable(cls, v):
        assert v in VALID_VARIABLES, f"invalid variable: `{v}`"
        return v

    @root_validator
    def check_site_variables(cls, values):
        sites = values.get("sites", [])
        variable = values.get("variable")
        source = cfg.get("variables", {}).get(variable, {}).get("source")
        for site in sites:
            if source == "hydstra":
                assert (
                    site in VALID_HYDSTRA_SITES
                ), f"'{site}' is not valid. \n\tOptions are: {VALID_HYDSTRA_SITES}"
                assert (
                    variable in cfg["preferred_variables"][site]
                ), f"'{variable}' not found at site '{site}'"
            if source == "dt_metrics":
                try:
                    _ = int(site)
                except:
                    raise ValueError(
                        "sites must be a valid positive integer, or an int coercible string"
                    )
        return values

    @root_validator
    def check_max_length(cls, values):
        same_length = ["intervals", "trace_upstreams", "agg_methods"]
        n = len(values.get("sites", []))
        for s in same_length:
            v = values.get(s) or []
            assert len(v) <= n, f"count of '{s}' must <= number of sites."
        return values
