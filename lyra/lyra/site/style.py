def render_in_jupyter_notebook_css_style(df):

    """
    From https://stackoverflow.com/a/49687866/2007153

    Get a Jupyter like html of pandas dataframe

    """

    styles = [
        # table properties
        dict(
            selector=" ",
            props=[
                ("margin", "0"),
                ("font-family", '"Helvetica", "Arial", sans-serif'),
                ("border-collapse", "collapse"),
                ("border", "none"),
            ],
        ),
        # background shading
        dict(selector="tbody tr:nth-child(even)", props=[("background-color", "#fff")]),
        dict(selector="tbody tr:nth-child(odd)", props=[("background-color", "#eee")]),
        # hover row
        dict(selector="tbody tr:hover", props=[("background-color", "#c8eaff")]),
        # row text
        dict(selector="tbody tr", props=[("font-size", "8pt")]),
        # cell spacing
        dict(selector="td,th", props=[("padding", ".5em 1.5em")]),
        # header cell properties
        dict(selector="th", props=[("font-size", "100%"), ("text-align", "center")]),
    ]
    return (df.style.set_table_styles(styles)).render()
