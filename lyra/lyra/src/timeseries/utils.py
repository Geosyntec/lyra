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
    for _, group in df.groupby(groupby):
        _df = group.sort_values(date_col)
        dfs.append(drop_runs(_df, value_col))

    return pandas.concat(dfs)
