from typing import List
from pathlib import Path
import json
import pandas
import asyncio
import datetime

# from lyra.api.endpoints.hydstra import get_variables, get_site_list
from lyra.core.async_requests import send_request
from lyra.core.config import settings


def get_site_list():
    site_list = {
        "function": "get_site_list",
        "version": 1,
        "params": {"site_list": "TSFILES(DSOURCES(tscARCHIVE))"},
    }

    return asyncio.run(send_request(settings.HYDSTRA_BASE_URL, payload=site_list))[
        "_return"
    ]


def site_preferred_variables(site_list: List[str]):
    get_variable_list = {
        "function": "get_variable_list",
        "version": 1,
        "params": {
            "site_list": ",".join(
                site_list
            ),  # TODO: this is required, call site list first.
            "datasource": "A",
            "var_filter": None,
        },
    }

    promise = asyncio.run(
        send_request(settings.HYDSTRA_BASE_URL, payload=get_variable_list)
    )
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

    variables = variables.merge(
        variables.query("name in @use_vars.keys()")
        .groupby(["site", "name"])
        .variable.min()  # <-- use the minimum number as the 'preferred value for now. Just a WAG.'
        .reset_index()
        .assign(preferred=True)
        .set_index(["site", "name", "variable"])["preferred"],
        left_on=["site", "name", "variable"],
        right_index=True,
        how="left",
    ).fillna(False)

    return variables


def site_variable_map(variables: pandas.DataFrame):
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
    cur_dir = Path(__file__).parent

    ts = datetime.datetime.utcnow().isoformat()

    static_dir = cur_dir.parent / "static"

    site_list = get_site_list()
    site_list["ts"] = ts
    with open(static_dir / "site_list.json", "w") as f:
        json.dump(site_list, f, indent=2)

    variables = site_preferred_variables(site_list=site_list["sites"])
    variables["ts"] = ts
    with open(static_dir / "site_variables.json", "w") as f:
        json.dump({"site_variables": variables.to_dict("records")}, f, indent=2)

    site_var_mapping = site_variable_map(variables)
    site_var_mapping["ts"] = ts
    with open(static_dir / "site_variable_mapping.json", "w") as f:
        json.dump(site_var_mapping, f, indent=2)


if __name__ == "__main__":
    main()
