from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Query
from fastapi.responses import ORJSONResponse

from lyra.models import hydstra_models
from lyra.models.response_models import HydstraJSONResponse
from lyra.src import hydstra

router = APIRouter(default_response_class=ORJSONResponse)


@router.get("/sites", response_model=HydstraJSONResponse)
async def get_site_list() -> Dict:
    response = await hydstra.api.get_site_list()

    return {"data": response}


@router.get("/sites/info", response_model=HydstraJSONResponse)
@router.post("/sites/info", response_model=HydstraJSONResponse)
async def get_sites_db_info(
    site: Optional[str] = Query(None, example="TRABUCO"),
    field_list: Optional[List[str]] = Query(None),
    return_type: hydstra_models.ReturnType = hydstra_models.ReturnType.array,
) -> Dict:
    response = await hydstra.api.get_sites_db_info(
        site=site, field_list=field_list, return_type=return_type, filter_values=None,
    )

    return {"data": response}


# @router.post("/sites/info", response_model=HydstraJSONResponse)
# async def post_sites_db_info(
#     site: Optional[str] = Query(None, example="TRABUCO"),
#     field_list: Optional[List[str]] = Query(None),
#     return_type: hydstra_models.ReturnType = hydstra_models.ReturnType.array,
#     filter_values: Optional[Dict[str, Any]] = Body({}, example={"active": True}),
# ) -> Dict:
#     response = await hydstra.api.get_sites_db_info(
#         site=site,
#         field_list=field_list,
#         return_type=return_type,
#         filter_values=filter_values,
#     )

#     return {"data": response}


@router.get("/sites/{site}/info", response_model=HydstraJSONResponse)
async def get_site_db_info(
    site: str,
    return_type: hydstra_models.ReturnType = hydstra_models.ReturnType.array,
    field_list: Optional[List[str]] = Query(None),
) -> Dict:
    response = await hydstra.api.get_site_db_info(
        site=site, return_type=return_type, field_list=field_list,
    )

    return {"data": response}


@router.get("/sites/spatial", response_model=HydstraJSONResponse)
async def get_site_geojson(
    site_list: Optional[List[str]] = Query(None),
    field_list: Optional[List[str]] = Query(
        None,
        example=["station", "latitude", "longitude", "stntype", "stname", "shortname",],
    ),
    get_elev: Optional[int] = 0,
) -> Dict:
    response = await hydstra.api.get_site_geojson(
        site_list=site_list, field_list=field_list, get_elev=get_elev
    )

    return {"data": response}


@router.get("/sites/datasources", response_model=HydstraJSONResponse)
async def get_datasources(
    site_list: Optional[List[str]] = Query(None),
    ts_classes: Optional[List[str]] = Query(None),
) -> Dict:
    response = await hydstra.api.get_datasources(
        site_list=site_list, ts_classes=ts_classes
    )

    return {"data": response}


@router.get("/sites/variables", response_model=HydstraJSONResponse)
async def get_variables(
    site_list: Optional[List[str]] = Query(None),
    datasource: str = "PUBLISH",
    var_filter: Optional[List[str]] = Query(None),
) -> Dict:
    response = await hydstra.api.get_variables(
        site_list=site_list, datasource=datasource, var_filter=var_filter
    )

    return {"data": response}


@router.get("/sites/{site}/variables/{variable}", response_model=HydstraJSONResponse)
async def get_site_variables(
    site: str, variable: Optional[str] = None, datasource: str = "PUBLISH",
) -> Dict:
    response = await hydstra.api.get_site_variables(
        site=site, datasource=datasource, variable=variable
    )

    return {"data": response}


@router.get("/sites/traces", response_model=HydstraJSONResponse)
async def get_trace(
    site_list: List[str] = Query(...),
    start_time: str = Query(...),
    var_list: List[str] = Query(...),
    interval: hydstra_models.Interval = Query(...),
    datasource: str = Query(...),
    end_time: str = Query(...),
    data_type: hydstra_models.DataType = Query(...),
    interval_multiplier: int = 1,
    recent_points: Optional[int] = None,
) -> Dict:
    response = await hydstra.api.get_trace(
        site_list=site_list,
        start_time=start_time,
        var_list=var_list,
        interval=interval,
        datasource=datasource,
        end_time=end_time,
        data_type=data_type,
        interval_multiplier=interval_multiplier,
        recent_points=recent_points,
    )

    return {"data": response}


@router.get("/variables/info", response_model=HydstraJSONResponse)
@router.post("/variables/info", response_model=HydstraJSONResponse)
async def get_variables_db_info(
    return_type: hydstra_models.ReturnType = hydstra_models.ReturnType.array,
    filter_values: Optional[Dict] = Body({}, example={"active": True}),
) -> Dict:
    response = await hydstra.api.get_variables_db_info(
        return_type=return_type, filter_values=filter_values,
    )

    return {"data": response}


# @router.get("/sites/variables/mapping",)
# async def get_site_variable_map():

#     promise = await get_variables(None, "A", None)
#     vars_by_site = []
#     for blob in promise["_return"]["sites"]:
#         site = blob["site"]
#         for variable in blob["variables"]:
#             variable["site"] = site
#             vars_by_site.append(variable)
#     variables = pandas.DataFrame(vars_by_site)

#     use_vars = {
#         "Rainfall": {"agg": "tot"},  # hydstra codes, not pandas ones.
#         "Discharge": {"agg": "mean"},
#     }
#     variables = variables.merge(
#         variables.query("name in @use_vars.keys()")
#         .groupby(["site", "name"])
#         .variable.min()  # <-- use the minimum number as the 'preferred value for now. Just a WAG.'
#         .reset_index()
#         .assign(preferred=True)
#         .set_index(["site", "name", "variable"])["preferred"],
#         left_on=["site", "name", "variable"],
#         right_index=True,
#         how="left",
#     ).fillna(False)

#     mapping = (
#         variables.query("preferred")
#         .assign(label=lambda df: df["name"] + "-" + df["variable"])
#         .groupby(["site"])
#         .apply(
#             lambda x: x[["label", "variable"]].set_index("label").to_dict()["variable"]
#         )
#     )

#     return mapping
