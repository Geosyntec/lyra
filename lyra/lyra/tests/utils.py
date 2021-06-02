import importlib


def _rsb_geo_file(*args, **kwargs):
    file = importlib.resources.open_binary("lyra.tests.data", "test_rsb_geo.json")
    setattr(file, "ftp_name", "test_rsb_geo.json")
    return file


def _rsb_geo_file_path(*args, **kwargs):
    with importlib.resources.path("lyra.tests.data", "test_rsb_geo.json") as p:
        return p


def _rsb_data_file_path(*args, **kwargs):
    with importlib.resources.path("lyra.tests.data", "test_rsb_data.csv") as p:
        return p


def _rsb_metrics_file(*args, **kwargs):
    # print("mocked mnwd.helper get_MNWD_file_obj")
    file = importlib.resources.open_binary(
        "lyra.tests.data", "DroolTool_Metrics_test.csv"
    )
    setattr(file, "ftp_name", "DroolTool_Metrics_test.csv")
    return file


def _rsb_metrics_file_path(*args, **kwargs):
    with importlib.resources.path("lyra.tests.data", "DroolTool_Metrics_test.csv") as p:
        return p


def _azure_put_file_object(*args, **kwargs):
    # print("mocked azure put file")
    return


def _dt_metrics_file(*args, **kwargs):
    file = importlib.resources.open_binary("lyra.tests.data", "test_dt_metrics.csv")
    return file


def _dt_metrics_file_path(*args, **kwargs):
    with importlib.resources.path("lyra.tests.data", "test_dt_metrics.csv") as p:
        return p
