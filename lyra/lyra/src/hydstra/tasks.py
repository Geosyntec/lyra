from copy import deepcopy
import datetime
import io
import json

import geopandas
import pandas

from lyra.core import utils
from lyra.connections import azure_fs
from lyra.core.config import config
from lyra.src.hydstra import api
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


def build_swn_variables(variables, cfg):
    sites = {}
    for dct in variables["sites"]:
        site = {}

        d = process_varfroms(dct["variables"], "discharge", cfg)
        site["discharge_info"] = d
        site["has_discharge"] = d is not None

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
    cfg = config()

    sites = build_swn_variables(variables, cfg)
    site_df = pandas.DataFrame(sites).T
    sites_with_trace = site_df.query(
        "has_discharge == True | has_conductivity == True"
    ).index

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
    path = utils.local_path("data/mount/swn/hydstra").resolve() / "swn_sites.geojson"

    geo_info_dct = json.loads(geo_info.to_json())
    ts = datetime.datetime.utcnow().isoformat()

    geo_info_dct["ts"] = ts

    path.write_text(json.dumps(geo_info_dct))

    file_obj = io.BytesIO()
    file_obj.write(json.dumps(geo_info_dct).encode())

    azure_fs.put_file_object(file_obj, "swn/hydstra/swn_sites.geojson", share=None)

    pass