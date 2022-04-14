import networkx as nx


def graph_from_df(df, source, target, create_using=None):
    if create_using is None:  # pragma: no branch
        create_using = nx.DiGraph
    g = nx.from_pandas_edgelist(
        df, source=source, target=target, create_using=create_using
    )
    nx.set_node_attributes(g, df.set_index(source).to_dict("index"))

    return g
