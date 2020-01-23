from .io import update_record
import pandas as pd


def _flatten(li):
    return [item for sublist in li for item in sublist]


def _check_scale_variance(pes_df, transformations):
    # Check for inputs to Scale with no variance
    in_scale = [t['Input'] for t in transformations if t['Name'] == 'Scale']
    in_scale = _flatten(in_scale)

    no_var = []
    if in_scale:
        in_scale_df = pes_df[pes_df.predictor_name.isin(in_scale)]
        for (n, id), grp in in_scale_df.groupby(['predictor_name', 'run_id']):
            if grp.value.astype('float').var() == 0:
                no_var.append(n)

    if no_var:
        return ["Applying Scale transformation to variables with no "
                f"variance will fail. ({', '.join(no_var)})"]
    else:
        return []


def add_warnings(analysis, pes, report_object):
    warnings = []

    pes_df = pd.DataFrame(pes)
    transformations = analysis['model']['Steps'][0]['Transformations']
    pred_map = {di['id']: di['name'] for di in analysis['predictors']}
    pes_df['predictor_name'] = pes_df.predictor_id.map(pred_map)

    warnings += _check_scale_variance(pes_df, transformations)

    if warnings:
        update_record(
            report_object,
            warnings=warnings,
        )
