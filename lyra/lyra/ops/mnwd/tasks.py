from lyra.connections.database import engine
from lyra.core.config import config
from lyra.ops.mnwd.helpers import (
    fetch_and_refresh_drooltool_metrics_file,
    fetch_and_refresh_oc_rsb_geojson_file,
    set_drooltool_database_with_file,
)

from lyra.ops.mnwd import spatial


def update_drooltool_database(
    engine=engine, update: bool = True, file=None, fields_from_config=True, share=None
):

    if update:
        fetch_and_refresh_drooltool_metrics_file(file=file, share=share)

    fields = None
    if fields_from_config:
        fields = [dct["variable"] for dct in config["mnwd"]["dt_metrics"]["fields"]]

    response = dict(
        taskname="update_drooltool_database",
        succeeded=set_drooltool_database_with_file(
            engine, file=file, fields=fields, share=share
        ),
    )

    return response


def update_rsb_geojson(file=None, share=None):
    succeeded = fetch_and_refresh_oc_rsb_geojson_file(file=file, share=share)
    response = dict(taskname="update_rsb_geojson", succeeded=succeeded)

    return response


def rsb_json(f: str = "topojson", xmin=None, ymin=None, xmax=None, ymax=None, **kwargs):
    # {"xmin":-117.78,"ymin":33.46,"xmax":-117.63,"ymax":33.65}
    xmin = xmin or -117.78
    ymin = ymin or 33.45
    xmax = xmax or -117.58
    ymax = ymax or 33.72
    bbox = (xmin, ymin, xmax, ymax)
    data = None
    if f == "geojson":
        data = spatial.rsb_geojson(bbox=bbox)
    elif f == "topojson":
        data = spatial.rsb_topojson(bbox=bbox, **kwargs)
    return data
