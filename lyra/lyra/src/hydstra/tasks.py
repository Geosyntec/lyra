import datetime
import io
import json
from copy import deepcopy
import pytz

import geopandas
import pandas
from shapely.ops import nearest_points

from lyra.connections import azure_fs
from lyra.core.config import cfg
from lyra.src.hydstra import api, helper
from lyra.src.mnwd import spatial
from lyra.src.rsb import graph


def process_varfroms(varlist, var, cfg):
    var_cfg = cfg["variables"][var]
    varfroms = var_cfg["varfrom"]
    varfrom_fallback = var_cfg["varfrom_fallback"]
    for v in deepcopy(varlist):
        for vfrom in varfroms:
            if v["variable"] == vfrom:
                v.update(var_cfg)
                v["varfrom"] = vfrom
                return v
        if int(float((v["variable"]))) == int(varfrom_fallback):
            v.update(var_cfg)
            v["varfrom"] = vfrom
            return v


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

        if d is not None:  # check if mapping is possible
            end_datetime = datetime.datetime.now(pytz.timezone("US/Pacific"))
            start_datetime = end_datetime - datetime.timedelta(days=90)
            inputs = dict(
                site=dct["site"],
                varfrom=d["varfrom"],
                varto=d["varto"],
                interval="day",
                start_date=start_datetime.date().isoformat(),
                end_date=end_datetime.date().isoformat(),
            )
            timeseries_details = await helper.get_site_variable_as_trace(**inputs)

            if timeseries_details.get("trace"):
                site["discharge_info"] = d
                site["has_discharge"] = d is not None
            else:  # assume no rating table thus no discharge data
                site["discharge_info"] = None
                site["has_discharge"] = False

        d = process_varfroms(dct["variables"], "rainfall", cfg)
        site["rainfall_info"] = d
        site["has_rainfall"] = d is not None

        d = process_varfroms(dct["variables"], "conductivity", cfg)
        site["conductivity_info"] = d
        site["has_conductivity"] = d is not None

        sites[dct["site"]] = site

    return sites


async def get_site_geojson_info():
    site_list = (await api.get_swn_site_list())["return"]["sites"]
    variables = (await api.get_variables(site_list, datasource="PUBLISH"))["return"]
    site_geojson = (await api.get_site_geojson(site_list))["return"]

    sites = await build_swn_variables(variables, cfg)
    site_df = pandas.DataFrame(sites).T
    sites_with_trace = site_df.query("has_discharge | has_conductivity").index

    gdf = geopandas.read_file(json.dumps(site_geojson)).set_index("id")

    rsbs = geopandas.read_file(json.dumps(spatial.rsb_geojson()))

    us_traced = (
        geopandas.sjoin(
            gdf.loc[sites_with_trace], rsbs[["CatchIDN", "geometry"]], how="left"
        )
        .reindex(columns=["CatchIDN"])
        .astype({"CatchIDN": "Int64"})
    )

    def trace_each(val):
        try:
            return graph.rsb_upstream_trace(int(val)).decode()
        except:
            return

    us_traced["upstream"] = us_traced.apply(lambda x: trace_each(x["CatchIDN"]), axis=1)

    geo_info = gdf.join(us_traced, how="left").join(site_df, how="left").reset_index()

    destinations = geo_info.query("has_rainfall").geometry.unary_union

    def near_rain(row, destinations):
        if row.has_rainfall:
            return row.geometry
        try:
            return nearest_points(row.geometry, destinations)[1]
        except:
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
