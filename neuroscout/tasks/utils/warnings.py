from .io import update_record
import pandas as pd


def _flatten(li):
    return [item for sublist in li for item in sublist]


def _check_scale_variance(pes_df, transformations):
    """ Warns if Scale transformation is applied to any variables with
    no variance in a given run. """
    # To numeric and coerce
    pes_df['value'] = pd.to_numeric(pes_df.value, errors='coerce')

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
        return [
            f"The following variables have no variance in at least one run: "
            f"{', '.join(set(no_var))}."
            "Scale transformation cannot be applied."]
    else:
        return []


def pre_warnings(analysis, pes, report_object):
    """ Generate warnings that are relevant prior to running pyBIDS.
    This includes warnings that might result in pyBIDS crashes, and make sense
    to catch early """
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
