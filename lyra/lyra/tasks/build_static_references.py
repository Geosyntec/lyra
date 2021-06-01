import asyncio
import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pandas

from lyra.core.async_requests import send_request
from lyra.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_site_list() -> Dict[str, Any]:
    site_list = {
        "function": "get_site_list",
        "version": 1,
        "params": {"site_list": "TABLE(SITE)"},
    }

    response = asyncio.run(send_request(settings.HYDSTRA_BASE_URL, payload=site_list))
    result: Dict[str, Any] = response["_return"]

    return result


def get_swn_site_list() -> Dict[str, Any]:
    site_list = {
        "function": "get_site_list",
        "version": 1,
        "params": {"site_list": "GROUP(SITE_TYPE,SWN_ALISO)"},
    }

    response = asyncio.run(send_request(settings.HYDSTRA_BASE_URL, payload=site_list))
    result: Dict[str, Any] = response["_return"]

    return result


def site_preferred_variables(site_list: List[str]) -> pandas.DataFrame:
    get_variable_list = {
        "function": "get_variable_list",
        "version": 1,
        "params": {
            "site_list": ",".join(site_list),
            # "datasource": "A",
            "datasource": "PUBLISH",
            "var_filter": None,
        },
    }

    promise = asyncio.run(
        send_request(settings.HYDSTRA_BASE_URL, payload=get_variable_list)
    )

    swn_site_list = get_swn_site_list()

    vars_by_site = []

    for blob in promise["_return"]["sites"]:
        site = blob["site"]
        for variable in blob["variables"]:
            variable["site"] = site
            vars_by_site.append(variable)

    variables = pandas.DataFrame(vars_by_site)

    use_vars = {
        "Rainfall": {"agg": "tot"},  # hydstra codes, not pandas ones.
        "Discharge": {"agg": "mean"},
    }

    variables = (
        variables.assign(in_swn=lambda df: df["site"].isin(swn_site_list["sites"]))
        .merge(
            variables.query("name in @use_vars.keys()")
            .groupby(["site", "name"])["variable"]
            .min()  # <-- use the minimum number as the 'preferred value for now. Just a WAG.'
            .reset_index()
            .assign(preferred=True)
            .set_index(["site", "name", "variable"])["preferred"],
            left_on=["site", "name", "variable"],
            right_index=True,
            how="left",
        )
        .fillna(False)
    )

    return variables


def site_variable_map(variables: pandas.DataFrame) -> Dict[str, Any]:
    mapping = (
        variables.query("preferred")
        .assign(label=lambda df: df["name"] + "-" + df["variable"])
        .groupby(["site"])
        .apply(
            lambda x: x[["label", "variable"]].set_index("label").to_dict()["variable"]
        )
    )

    return {"site_variable_mapping": mapping.to_dict()}


def main():
    succeeded = False
    try:
        cur_dir = Path(__file__).parent

        ts = datetime.datetime.utcnow().isoformat()

        static_dir = cur_dir.parent / "static"

        site_list = get_site_list()
        site_list["ts"] = ts
        # logger.info(site_list)
        with open(static_dir / "site_list.json", "w") as f:
            json.dump(site_list, f, indent=2)

        variables = site_preferred_variables(site_list=site_list["sites"])
        variables["ts"] = ts
        # logger.info(variables)
        with open(static_dir / "site_variables.json", "w") as f:
            json.dump({"site_variables": variables.to_dict("records")}, f, indent=2)

        site_var_mapping = site_variable_map(variables)
        site_var_mapping["ts"] = ts
        # logger.info(site_var_mapping)
        with open(static_dir / "site_variable_mapping.json", "w") as f:
            json.dump(site_var_mapping, f, indent=2)

        succeeded = True

    except Exception as e:
        logger.error(e)

    return succeeded


if __name__ == "__main__":
    main()
