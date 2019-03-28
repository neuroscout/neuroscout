import altair as alt


def plot_interactive_design_matrix(dm):
    dm = dm.reset_index().rename(columns={'index': 'scan_number'})
    dm = dm.melt('scan_number', var_name='regressor', value_name='value')

    pts = alt.selection_multi(encodings=['x'])

    base_color = alt.Color(
        'value:Q', sort='ascending',
        legend=None, scale=alt.Scale(scheme='viridis'))

    heat = alt.Chart(dm).mark_rect().encode(
        alt.Y('scan_number:O',
              axis=alt.Axis(title=None, ticks=False, labels=False)),
        alt.X('regressor:N', axis=alt.Axis(title=None, ticks=False)),
        fill=base_color,
        stroke=alt.condition(pts,
                             base_color,
                             alt.value('black'))
    ).properties(
        width=500,
        height=900,
        selection=pts
    )

    line = alt.Chart(dm).mark_line().encode(
        alt.X('scan_number', axis=alt.Axis(ticks=False)),
        y='value:Q',
        color=alt.Color('regressor', legend=None)
    ).transform_filter(
        pts
    )

    plt = alt.vconcat(
        heat,
        line
    ).configure_scale(bandPaddingInner=0.0)

    return plt.to_json()
