from enum import Enum


class Interval(str, Enum):
    year = "year"
    month = "month"
    day = "day"
    hour = "hour"


class AggregationMethod(str, Enum):
    tot = "tot"
    sum = "tot"
    mean = "mean"
    max = "max"
    min = "min"


class RegressionMethod(str, Enum):
    linear = "linear"
    quad = "quad"
    poly = "poly"
    exp = "exp"
    pow = "pow"
    log = "log"
    none = "none"


class SpatialResponseFormat(str, Enum):
    topojson = "topojson"
    geojson = "geojson"


class ResponseFormat(str, Enum):
    json = "json"
    html = "html"


class ResponseDataFormat(str, Enum):
    json = "json"
    csv = "csv"


class Weather(str, Enum):
    both = "both"
    wet = "wet"
    dry = "dry"
