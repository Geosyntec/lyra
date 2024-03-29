from enum import Enum


class ReturnType(str, Enum):
    array = "array"
    hash_ = "hash"


class Interval(str, Enum):
    year = "year"
    month = "month"
    day = "day"
    hour = "hour"
    minute = "minute"
    second = "second"
    period = "period"
    default = "default"


class DataType(str, Enum):
    tot = "tot"
    sum = "tot"
    mean = "mean"
    maxmin = "maxmin"
    max = "max"
    min = "min"
    start = "start"
    end = "end"
    first = "first"
    last = "last"
    point = "point"
    partialtot = "partialtot"
    cum = "cum"
    cumsum = "cum"
