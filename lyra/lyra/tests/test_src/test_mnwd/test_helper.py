import pytest

from lyra.src.mnwd import helper
from lyra.tests import utils


@pytest.mark.parametrize(
    "file", [None, utils._rsb_metrics_file(), utils._rsb_metrics_file_path()]
)
def test_fetch_and_refresh_drooltool_metrics_file(mock_get_MNWD_file_obj_metrics, file):
    assert helper.fetch_and_refresh_drooltool_metrics_file(file=file)


@pytest.mark.parametrize(
    "file", [None, utils._rsb_geo_file(), utils._rsb_geo_file_path()]
)
def test_fetch_and_refresh_oc_rsb_geojson_file(mock_get_MNWD_file_obj_geo, file):
    assert helper.fetch_and_refresh_oc_rsb_geojson_file(file=file)


# from lyra.core import cache
# import time
# import orjson


# @cache.cache_decorator(ex=3600 * 6)  # expires in 6 hours
# def cached_func(*args, **kwargs):
#     print("sleeping...", end="")
#     time.sleep(3)
#     print("awake!")

#     return orjson.dumps((args, kwargs))


# @pytest.mark.parametrize("site", [1, 1, 1])
# @pytest.mark.parametrize("param", [2, 2, 2])
# def test_cached(
#     nocache,
#     # clearcache,
#     site,
#     param,
# ):
#     cached_func(site, param)


@pytest.mark.parametrize("site", [23])
@pytest.mark.parametrize(
    "variable",
    ["overall_MeterID_count", "overall_daily_est_outdoor_budget_overage_sum"],
)
@pytest.mark.parametrize("trace_upstream", [True, False])
@pytest.mark.parametrize("start_date", ["2016-06-01", "2016-01-01"])
@pytest.mark.parametrize("end_date", ["2017-06-01", "2017-01-01"])
@pytest.mark.parametrize("agg_method", ["sum", "mean"])
def test_get_timeseries_from_dt_metrics(
    nocache,
    mock_rsb_geo_bytestring,
    data_engine,
    site,
    variable,
    start_date,
    end_date,
    agg_method,
    trace_upstream,
):
    engine = data_engine
    kwargs = dict(
        site=site,
        variable=variable,
        start_date=start_date,
        end_date=end_date,
        agg_method=agg_method,
        trace_upstream=trace_upstream,
        engine=engine,
    )
    df = helper.get_timeseries_from_dt_metrics(**kwargs)

    assert len(df) in [8, 13, 18]


@pytest.mark.integration
@pytest.mark.parametrize("site", [4])
@pytest.mark.parametrize(
    "variable",
    ["overall_MeterID_count", "overall_daily_est_outdoor_budget_overage_sum"],
)
@pytest.mark.parametrize("trace_upstream", [True, False])
@pytest.mark.parametrize("start_date", ["2016-06-01", "2016-01-01"])
@pytest.mark.parametrize("end_date", ["2017-06-01", "2017-01-01"])
@pytest.mark.parametrize("agg_method", ["sum", "mean"])
def test_get_timeseries_from_dt_metrics_integration(
    # reconnect_engine,
    site,
    variable,
    start_date,
    end_date,
    agg_method,
    trace_upstream,
):
    kwargs = dict(
        site=site,
        variable=variable,
        start_date=start_date,
        end_date=end_date,
        agg_method=agg_method,
        trace_upstream=trace_upstream,
    )
    df = helper.get_timeseries_from_dt_metrics(**kwargs)

    assert len(df) in [8, 13, 18]


@pytest.mark.integration
def test_get_MNWD_file_obj_integration():
    slug = "rsb_geo"
    file = helper.get_MNWD_file_obj(slug)
    assert slug in file.ftp_name.lower()
