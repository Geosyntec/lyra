import datetime
import io
import json
import logging
from copy import deepcopy
from typing import Any, Dict

import geopandas
import pandas
import pytz
from shapely.ops import nearest_points

from lyra.connections import azure_fs
from lyra.core.config import cfg
from lyra.src.hydstra import api, helper
from lyra.src.mnwd import spatial
from lyra.src.mnwd.dt_metrics import dt_metrics
from lyra.src.rsb import graph

logger = logging.getLogger(__file__)


def process_varfroms(varlist, var, cfg):
    var_cfg = cfg["variables"][var]
    varfroms = var_cfg["varfrom"]
    varfrom_fallback = var_cfg["varfrom_fallback"]

    for v in deepcopy(varlist):
        for vfrom in varfroms:
            if v["variable"] == vfrom:
                out = deepcopy(v)
                out.update(var_cfg)
                out["varfrom"] = vfrom
                return out

    for v in deepcopy(varlist):
        if int(float((v["variable"]))) == int(varfrom_fallback):
            out = deepcopy(v)
            out.update(var_cfg)
            out["varfrom"] = vfrom
            return out


async def build_swn_variables(variables, cfg):
    sites = {}
    for i, dct in enumerate(variables["sites"]):
        site = {}

        d = process_varfroms(dct["variables"], "distance_to_water", cfg)
        site["distance_to_water_info"] = d
        site["has_distance_to_water"] = d is not None

        d = process_varfroms(dct["variables"], "raw_level", cfg)
        site["raw_level_info"] = d
        site["has_raw_level"] = d is not None

        d = process_varfroms(dct["variables"], "discharge", cfg)
        site["discharge_info"] = d
        site["has_discharge"] = d is not None

        if d is not None:  # check if mapping is possible
            end_datetime = datetime.datetime.now(pytz.timezone("US/Pacific"))
            start_datetime = end_datetime - datetime.timedelta(days=30 * 6)
            inputs = dict(
                site=dct["site"],
                varfrom=d["varfrom"],
                varto=d["varto"],
                interval="day",
                start_date=start_datetime.date().isoformat(),
                end_date=end_datetime.date().isoformat(),
            )
            timeseries_details = await helper.get_site_variable_as_trace(**inputs)

            error_num = timeseries_details.get("error_num")

            if error_num != 0:
                logger.info(
                    f'found NO DATA @ {dct["site"]}. response: {timeseries_details}'
                )

            if error_num == 124:
                site["discharge_info"] = None
                site["has_discharge"] = False
                site["missing_rating_table"] = True

        d = process_varfroms(dct["variables"], "rainfall", cfg)
        site["rainfall_info"] = d
        site["has_rainfall"] = d is not None

        d = process_varfroms(dct["variables"], "conductivity", cfg)
        site["conductivity_info"] = d
        site["has_conductivity"] = d is not None

        sites[dct["site"]] = site

    return sites


def hystra_format_dt(dt):
    return dt.date().isoformat().replace("-", "") + "000000"


def get_catchidns_with_dt_metrics():
    dt = datetime.datetime.now().date()
    y = dt.year
    records = dt_metrics(
        variables=["overall_MeterID_count"], groupby=["sum"], years=range(2015, y)
    )
    _df = pandas.DataFrame(json.loads(records))
    catchidns = _df.catchidn.unique()

    return catchidns


async def process_dt_metrics(s, upstream, catchidns, metrics):

    site_dct: Dict[str, Any] = {}

    if not upstream:
        print(f"site {s} has no upstream catchidns")
        for m in metrics:
            site_dct[f"has_{m}"] = False
            site_dct[f"{m}_info"] = None
        return site_dct

    if not any(c in catchidns for c in upstream):
        print(f"site {s} has no drool tool results")
        for m in metrics:
            site_dct[f"has_{m}"] = False
            site_dct[f"{m}_info"] = None
        return site_dct

    try:
        dt = datetime.datetime.now().date()
        y = dt.year + 1

        records = dt_metrics(
            catchidns=upstream,
            variables=["overall_MeterID_count"],
            groupby=["sum"],
            years=range(2015, y),
        )
        series = (
            pandas.DataFrame(json.loads(records))
            .assign(
                date=lambda df: pandas.to_datetime(
                    df["year"].astype(str) + df["month"].astype(str), format="%Y%m"
                )
            )
            .set_index("date")["value"]
        )
        start, end = (
            hystra_format_dt(series.index.min()),
            hystra_format_dt(series.index.max()),
        )

        for m in metrics:
            site_dct[f"has_{m}"] = True

            _info = deepcopy(cfg["variables"][m])
            _info["period_start"] = start
            _info["period_end"] = end
            _info["variable"] = m

            site_dct[f"{m}_info"] = _info
        return site_dct

    except Exception as e:
        print(s)
        raise e


def trace_each(val):
    try:
        return json.loads(graph.rsb_upstream_trace(int(val)))
    except Exception as e:
        print(f"skipping {val} because {e}")
        return []


async def get_site_geojson_info():
    site_list = set((await api.get_swn_site_list())["return"]["sites"])
    variables = (await api.get_variables(site_list, datasource="PUBLISH"))["return"]
    site_geojson = (await api.get_site_geojson(site_list))["return"]

    sites = await build_swn_variables(variables, cfg)
    site_df = pandas.DataFrame(sites).T

    gdf = (
        geopandas.read_file(json.dumps(site_geojson))
        .loc[lambda df: ~df["id"].isnull()]
        .set_index("id")
    )

    rsbs = geopandas.read_file(json.dumps(spatial.rsb_geojson()))

    us_traced = (
        geopandas.sjoin(gdf, rsbs[["CatchIDN", "geometry"]], how="left")
        .reindex(columns=["CatchIDN"])
        .astype({"CatchIDN": "Int64"})
    )

    to_trace = us_traced["CatchIDN"].dropna().astype(int).unique()
    traced = {c: trace_each(c) for c in to_trace}

    geo_info = (
        gdf.join(us_traced, how="left")
        .join(site_df, how="left")
        .assign(upstream=lambda df: df["CatchIDN"].map(traced))
    )

    catchidns = get_catchidns_with_dt_metrics()

    metrics = list(
        filter(
            lambda x: cfg["variables"][x]["source"] == "dt_metrics",
            cfg["variables"].keys(),
        )
    )

    ls = []
    for i, r in geo_info.iterrows():
        station = r.station
        upstream = r.upstream

        if not isinstance(upstream, list):
            upstream = None

        dct = await process_dt_metrics(station, upstream, catchidns, metrics)
        dct["station"] = station

        ls.append(dct)
    ls_df = pandas.DataFrame(ls)
    geo_info = geo_info.merge(ls_df, on="station")

    ls = []
    variables = cfg["variables"].keys()
    for _, r in geo_info.iterrows():
        var = [i + "_info" for i in variables if getattr(r, f"has_{i}")]
        variables_regression = [
            i
            for i in var
            if not any(v in i for v in ["raw_level", "distance_to_water"])
        ]
        variables_diversion_scenario = [i for i in var if "discharge" in i]
        ls.append(
            {
                "station": r.station,
                "variables": var,
                "variables_regression": variables_regression,
                "variables_diversion_scenario": variables_diversion_scenario,
            }
        )
    ls_df = pandas.DataFrame(ls)
    geo_info = geo_info.merge(ls_df, on="station")

    destinations = geo_info.query("has_rainfall")

    # limit to just the sites with a reading in the last 6 months.
    dt = datetime.datetime.now() - datetime.timedelta(days=30 * 6)
    ix = [
        info["period_end"] > hystra_format_dt(dt) for info in destinations.rainfall_info
    ]
    destinations = destinations.loc[ix].geometry.unary_union

    def near_rain(row, destinations):
        if row.has_rainfall:
            return row.geometry
        try:
            return nearest_points(row.geometry, destinations)[1]
        except Exception as e:
            logger.warning(str(e))
            return

    geo_info["nearest_rainfall_station_pt"] = geo_info.apply(
        lambda x: near_rain(x, destinations), axis=1
    )
    geo_info["nearest_rainfall_station"] = geo_info.apply(
        lambda x: geo_info.loc[
            geo_info.geometry == x.nearest_rainfall_station_pt
        ].station.values[0],
        axis=1,
    )

    geo_info = geo_info.drop(columns=["nearest_rainfall_station_pt"])

    return geo_info


async def save_site_geojson_info():  # pragma: no cover

    geo_info = await get_site_geojson_info()
    path = cfg["site_path"]

    geo_info_dct = json.loads(geo_info.to_json())
    ts = datetime.datetime.utcnow().isoformat()

    geo_info_dct["ts"] = ts

    path.write_text(json.dumps(geo_info_dct))

    file_obj = io.BytesIO()
    file_obj.write(json.dumps(geo_info_dct).encode())

    azure_fs.put_file_object(file_obj, "swn/hydstra/swn_sites.json")
