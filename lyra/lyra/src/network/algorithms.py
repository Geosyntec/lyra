import networkx as nx


def trace_upstream(g, from_node):
    return nx.ancestors(g, from_node) | {from_node}


def trace_downstream(g, from_node):
    return nx.descendants(g, from_node) | {from_node}
