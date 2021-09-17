import asyncio
from typing import Any, Dict, List, Optional

import pandas

from lyra.src.timeseries import Timeseries, utils


def active_system_timeseries(
    boolean_weather_series, months_active=None, days_active=None, hours_active=None
):

    months_active = (
        months_active if months_active is not None else range(1, 13)
    )  # all months, 1-12
    days_active = (
        days_active if days_active is not None else range(7)
    )  # all days, monday is 0
    hours_active = hours_active if hours_active is not None else range(24)  # all hours
    div_df = boolean_weather_series.to_frame(name="weather").assign(
        active=lambda df: (
            df["weather"]
            & df.index.month.isin(months_active)
            & df.index.weekday.isin(days_active)
            & df.index.hour.isin(hours_active)
        )
    )

    return div_df["active"]


def run_diversion_scenario(
    inflow_rate,
    diversion_rate,
    infiltration_rate,
    increment_seconds=1,
    initial_pool_volume=0,
    max_pool_volume=0,
    active_ts=None,
):

    if active_ts is None:
        active_ts = pandas.Series(True, index=inflow_rate.index)

    _pool_volume = []
    _inflow_volume = []
    _inflow_rate = []
    _diverted_volume = []
    _diversion_rate = []
    _infiltrated_volume = []
    _infiltration_rate = []
    _discharged_volume = []
    _discharge_rate = []

    current_pool_volume = initial_pool_volume

    def _increment(
        current_pool_volume,
        inflow_rate,
        diversion_rate,
        infiltration_rate,
        increment_seconds=1,
        max_pool_volume=0,
    ):

        _inflow_volume.append(inflow_rate * increment_seconds)
        _inflow_rate.append(inflow_rate)

        current_pool_volume = current_pool_volume + inflow_rate * increment_seconds

        # infiltrate
        infiltrated_volume = max(
            0, min(current_pool_volume, infiltration_rate * increment_seconds)
        )
        _infiltrated_volume.append(infiltrated_volume)
        _infiltration_rate.append(infiltrated_volume / increment_seconds)
        current_pool_volume -= infiltrated_volume

        # divert
        diverted_volume = max(
            0, min(current_pool_volume, diversion_rate * increment_seconds)
        )
        _diverted_volume.append(diverted_volume)
        _diversion_rate.append(diverted_volume / increment_seconds)
        current_pool_volume -= diverted_volume

        # discharge
        discharged_volume = max(0, current_pool_volume - max_pool_volume)
        _discharged_volume.append(discharged_volume)
        _discharge_rate.append(discharged_volume / increment_seconds)
        current_pool_volume -= discharged_volume

        _pool_volume.append(current_pool_volume)

        return current_pool_volume

    for r, active in zip(inflow_rate, active_ts):
        current_pool_volume = _increment(
            current_pool_volume,
            r,
            diversion_rate * int(active),
            infiltration_rate,
            increment_seconds,
            max_pool_volume,
        )

    results = pandas.DataFrame(
        {
            "inflow_volume": _inflow_volume,
            "inflow_rate": _inflow_rate,
            "infiltrated_volume": _infiltrated_volume,
            "infiltration_rate": _infiltration_rate,
            "diverted_volume": _diverted_volume,
            "diversion_rate": _diversion_rate,
            "discharged_volume": _discharged_volume,
            "discharge_rate": _discharge_rate,
            "storage_volume": _pool_volume,
        }
    )

    results.index = inflow_rate.index

    return results


async def gather_timeseries(ts: Timeseries) -> None:

    await asyncio.gather(ts.init_ts(), ts.get_nearest_rainfall_ts_async())


def simulate_diversion(
    ts: Dict[str, Any],
    diversion_rate_cfs: float,
    storage_max_depth_ft: float = 0.0,
    storage_initial_depth_ft: float = 0.0,
    storage_area_sqft: float = 0.0,
    infiltration_rate_inhr: float = 0.0,
    operated_weather_condition: str = "dry",
    rainfall_event_depth_threshold: float = 0.1,
    event_separation_hrs: float = 6.0,
    after_rain_delay_hrs: float = 72.0,
    diversion_months_active: Optional[List[int]] = None,
    diversion_days_active: Optional[List[int]] = None,
    diversion_hours_active: Optional[List[int]] = None,
    **kwargs: Optional[Dict],
) -> pandas.DataFrame:

    initial_pool_volume = storage_initial_depth_ft * storage_area_sqft
    max_pool_volume = storage_max_depth_ft * storage_area_sqft  # cubic feet
    infiltration_rate_cfs = infiltration_rate_inhr / 12 / 3600 * storage_area_sqft
    inc = 3600

    discharge_ts = Timeseries(**ts)

    asyncio.run(gather_timeseries(discharge_ts))

    rg_ts = discharge_ts.get_nearest_rainfall_ts()

    precip_depth_ts = pandas.Series(rg_ts.timeseries["value"], name="rainfall_depth")

    if operated_weather_condition == "both":
        diversion_active_bool_series = pandas.Series(
            True, index=rg_ts.weather_condition_series.index
        )
    else:
        dw = utils.identify_dry_weather(
            rg_ts.timeseries["value"],
            min_event_depth=rainfall_event_depth_threshold,
            event_separation_hrs=event_separation_hrs,
            after_rain_delay_hrs=after_rain_delay_hrs,
        )
        if operated_weather_condition == "dry":
            diversion_active_bool_series = dw["is_dry"]
        else:
            diversion_active_bool_series = ~dw["is_dry"]

    active_ts = active_system_timeseries(
        diversion_active_bool_series,
        months_active=diversion_months_active,
        days_active=diversion_days_active,
        hours_active=diversion_hours_active,
    )

    inflow_ts = discharge_ts.timeseries.value.asfreq("H").interpolate("cubic")

    results = run_diversion_scenario(
        inflow_ts,
        diversion_rate_cfs,
        infiltration_rate_cfs,
        inc,
        initial_pool_volume,
        max_pool_volume,
        active_ts=active_ts,
    )

    results = results.join(precip_depth_ts)

    return results
