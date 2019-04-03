import altair as alt
import numpy as np
import pandas as pd

alt.data_transformers.enable('default', max_rows=None)

def sort_dm(dm_wide, interest=[]):
    return pd.concat(
        [dm_wide[interest], dm_wide[set(dm_wide.columns) - set(interest)], ],
        axis=1)

def melt_dm(dm):
    dm = dm.reset_index().rename(columns={'index': 'scan_number'})
    return dm.melt('scan_number', var_name='regressor', value_name='value')


def plot_design_matrix(dm_wide):
    dm = melt_dm(dm_wide)

    pts = alt.selection_multi(encodings=['x'])
    time_labels = list(range(0, dm.scan_number.max(), 50))

    base_color = alt.Color(
        'value:Q', sort='ascending',
        legend=None, scale=alt.Scale(scheme='viridis'))

    heat = alt.Chart(dm).mark_rect().encode(
        alt.Y('scan_number:O',
              axis=alt.Axis(title='Time (TRs)', ticks=False,
                            values=time_labels, labels=True)),
        alt.X('regressor:N', sort=None, axis=alt.Axis(
            labelAngle=-45, title=None, ticks=False)),
        fill=base_color,
        stroke=base_color,
        opacity=alt.condition(pts, alt.value(1), alt.value(0.7))
    ).properties(
        width=800,
        height=700,
        selection=pts
    ).interactive()
    line = alt.Chart(dm).mark_line(clip=True).encode(
        alt.X('scan_number',
              axis=alt.Axis(
                  title='Time (TRs)', values=time_labels, ticks=False),
              scale=alt.Scale(domain=(0, int(dm.scan_number.max()))),
              ),
        y=alt.Y('value:Q', axis=alt.Axis(title='Amplitude')),
        color=alt.Color(
            'regressor', sort=None, legend=alt.Legend(orient='right'))
    ).transform_filter(
        pts
    ).properties(
        width=700,
        height=275,
    )

    plt = alt.vconcat(
        heat,
        line,
        resolve=alt.Resolve(
            scale=alt.LegendResolveMap(color=alt.ResolveMode('independent')))
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
        alt.X('index',  sort=None, axis=alt.Axis(title=None)),
        alt.Y('index_2', sort=None, axis=alt.Axis(title=None)),
        tooltip=['r'],
        fill=alt.Color(
            'r:Q', sort='descending', legend=alt.Legend(title='r'),
            scale=alt.Scale(scheme='redyellowblue', domain=[-1, 1]))
    ).properties(
        width=400,
        height=400,
    ).configure_scale(
        bandPaddingInner=0.015
    ).configure_view(
        strokeWidth=0
    ).interactive()

    return corr_mat.to_dict()
