import altair as alt
import numpy as np

alt.data_transformers.enable('default', max_rows=None)


def melt_dm(dm):
    dm = dm.reset_index().rename(columns={'index': 'scan_number'})
    return dm.melt('scan_number', var_name='regressor', value_name='value')


def plot_design_matrix(dm):
    dm = melt_dm(dm)

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

    return plt.to_dict()


def plot_corr_matrix(dm_wide):
    dm_corr = dm_wide.corr()
    dm_corr = dm_corr.where(
        np.triu(np.ones(dm_corr.shape)).astype(np.bool)).reset_index()
    dm_corr_long = dm_corr.melt(
        var_name='index_2',
        value_vars=dm_wide.columns,  id_vars='index', value_name='r')

    corr_mat = alt.Chart(dm_corr_long).mark_rect().encode(
        alt.X('index',  axis=alt.Axis(title=None)),
        alt.Y('index_2', axis=alt.Axis(title=None)),
        tooltip=['r'],
        fill=alt.Color(
            'r:Q', sort='descending',
            legend=alt.Legend(title='r'),
            scale=alt.Scale(scheme='redyellowblue', domain=[-1, 1]))
        ).properties(
            width=400,
            height=400,
        ).configure_scale(
            bandPaddingInner=0.01
        ).configure_view(
            strokeWidth=0
        ).interactive()

    return corr_mat.to_dict()
