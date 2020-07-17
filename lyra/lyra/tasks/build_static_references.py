from pathlib import Path
import json
import pandas
import asyncio

from lyra.api.endpoints import hydstra


def site_preferred_variables():

    promise = asyncio.run(hydstra.get_variables(None, "A", None))
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

    static_dir = cur_dir.parent / "static"

    variables = site_preferred_variables()
    with open(static_dir / "site_variables.json", "w") as f:
        json.dump({"site_variables": variables.to_dict("records")}, f, indent=2)

    site_var_mapping = site_variable_map(variables)
    with open(static_dir / "site_variable_mapping.json", "w") as f:
        json.dump(site_var_mapping, f, indent=2)

    with open(static_dir / "site_list.json", "w") as f:
        sitelist_response = asyncio.run(hydstra.get_site_list())
        json.dump(sitelist_response["_return"], f, indent=2)


if __name__ == "__main__":
    main()
