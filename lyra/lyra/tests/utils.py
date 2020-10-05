import importlib


def _rsb_geo_file_binary(*args, **kwargs):
    file = importlib.resources.read_binary("lyra.tests.data", "test_rsb_geo.json")
    return file


def _rsb_geo_file(*args, **kwargs):
    file = importlib.resources.open_binary("lyra.tests.data", "test_rsb_geo.json")
    return file


def _rsb_geo_file_path(*args, **kwargs):
    with importlib.resources.path("lyra.tests.data", "test_rsb_geo.json") as p:
        # print("used path:", p)
        return p


def _rsb_metrics_file(*args, **kwargs):
    # print("mocked mnwd.helper get_MNWD_file_obj")
    file = importlib.resources.open_binary(
        "lyra.tests.data", "DroolTool_Metrics_test.csv"
    )
    return file


def _rsb_metrics_file_path(*args, **kwargs):
    with importlib.resources.path("lyra.tests.data", "DroolTool_Metrics_test.csv") as p:
        # print("used path:", p)
        return p


def _azure_put_file_object(*args, **kwargs):
    # print("mocked azure put file")
    return
