from typing import List, Optional

from pydantic import BaseModel, validator, root_validator
import pandas
import orjson

from lyra.core.config import config
from lyra.core.utils import flatten_expand_list
from lyra.src.mnwd.dt_metrics import dt_metrics

cfg = config()
VALID_VARIABLES = list(cfg["variables"].keys())
VALID_HYDSTRA_SITES = list(cfg["preferred_variables"].keys())
# VALID_RSB_SITES = list(
#     pandas.DataFrame(orjson.loads(dt_metrics()))["catchidn"].astype(str).unique()
# )
# VALID_SITES = VALID_HYDSTRA_SITES + VALID_RSB_SITES


class SingleVarSpec(BaseModel):
    variable: str
    sites: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    intervals: Optional[List[str]] = None
    trace_upstreams: Optional[List[bool]] = None
    agg_methods: Optional[List[str]] = None

    @validator("sites", "intervals", "agg_methods")
    def expand_flatten(cls, v):
        if v is not None:
            return flatten_expand_list(v)

    @validator("sites")
    def check_sites(cls, v):
        # for site in v:
        #     assert site in VALID_SITES, f"invalid site: `{site}`"
        return v

    @validator("variable")
    def check_variable(cls, v):
        assert v in VALID_VARIABLES, f"invalid variable: `{v}`"
        return v

    @root_validator
    def check_site_variables(cls, values):
        sites = values.get("sites", [])
        variable = values.get("variable")
        for site in sites:
            if site in VALID_HYDSTRA_SITES:
                assert (
                    variable in cfg["preferred_variables"][site]
                ), f"'{variable}' not found at site '{site}'"
        return values

    @root_validator
    def check_max_length(cls, values):
        same_length = ["intervals", "trace_upstreams", "agg_methods"]
        n = len(values.get("sites", []))
        for s in same_length:
            v = values.get(s) or []
            assert len(v) <= n, f"count of '{s}' must <= number of sites."
        return values
