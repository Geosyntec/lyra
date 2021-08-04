import numpy
import pandas


def drop_runs(df, value_col=None):
    if value_col is None:
        value_col = "value"
    df = (
        df.assign(
            _thin=lambda df: df[value_col].eq(df[value_col].shift(1))
            & df[value_col].eq(df[value_col].shift(-1))
        )
        .query("not _thin")
        .drop(columns=["_thin"])
    )
    return df


def drop_runs_tidy(df, date_col="date", value_col=None, groupby=None):

    if groupby is None:
        return drop_runs(df, value_col)

    dfs = []
    for _, group in df.groupby(groupby, sort=False):
        _df = group.sort_values(date_col)
        dfs.append(drop_runs(_df, value_col))

    return pandas.concat(dfs)


def _infer_freq(index):
    return index.to_series().diff().min()


def infer_freq(index):
    """If no frequency, use min difference in index timestamp to guess.

    Parameters
    ----------
    index : pandas.Series.index or pandas.DataFrame.index

    """
    if not index.inferred_type == "datetime64":
        raise ValueError("must be a datetime index")

    if len(index) < 3:
        return _infer_freq(index)

    freq = pandas.infer_freq(index)

    if freq is None:
        freq = _infer_freq(index)
    return freq


def clean_series(series):
    """Ensure series with datetime index has regular frequency data.

    Parameters
    ----------
    series : pandas.Series
    """
    if getattr(series.index, "freq", None) is None:
        freq = infer_freq(series.index)
        return series.asfreq(freq, fill_value=0)
    else:
        return series


def number_nonzero_runs(series, zero_tol=None):
    if zero_tol is None:
        zero_tol = 0
    m = series.gt(zero_tol)
    return numpy.where(m, (series.shift(1).le(zero_tol, fill_value=0) & m).cumsum(), 0)


def get_storm_events(series, event_separation_hrs=None):
    if event_separation_hrs is None:
        event_separation_hrs = "6"

    col_name = series.name
    df = clean_series(series).to_frame()
    assert infer_freq(df.index) == "H", "must be hourly data."
    window = max(
        pandas.Timedelta(f"{event_separation_hrs}H"), pandas.Timedelta(df.index.freq)
    )

    res = (
        df.assign(
            __precip_cumul=lambda df: df[col_name].rolling(window).sum().fillna(0)
        )
        .assign(storm=lambda df: number_nonzero_runs(df.__precip_cumul, zero_tol=1e-6))
        .drop("__precip_cumul", axis=1)
    )

    return res


def identify_dry_weather(
    rainfall_record,
    min_event_depth=None,
    event_separation_hrs=None,
    after_rain_delay_hrs=None,
):
    """
    rainfall record must be hourly
    """

    if min_event_depth is None:
        min_event_depth = 0.1
    if event_separation_hrs is None:
        event_separation_hrs = 6
    if after_rain_delay_hrs is None:
        after_rain_delay_hrs = 72

    events = get_storm_events(
        rainfall_record, event_separation_hrs=event_separation_hrs
    )

    events_over_threshold = (
        events.groupby("storm")["value"]
        .sum()
        .transform(lambda x: x > min_event_depth)
        .reset_index()
        .assign(is_qualifying_event=lambda df: df["value"])
        .set_index("storm")
    )

    events = events.merge(
        events_over_threshold["is_qualifying_event"],
        how="left",
        left_on="storm",
        right_index=True,
    ).assign(
        is_dry=lambda df: (
            df["is_qualifying_event"]
            .rolling(f"{after_rain_delay_hrs}H")
            .sum()
            .fillna(0)
            == 0
        )
    )

    return events
