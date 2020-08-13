from pathlib import Path
from hashids import Hashids

from ..models import Analysis, Report

from .utils.build import build_analysis, impute_confounds
from .utils.viz import plot_design_matrix, plot_corr_matrix, sort_dm
from .utils.io import (
    update_record, PathBuilder, write_jsons, write_tarball, analysis_to_json)
from .utils.warnings import pre_warnings

MIN_CLI_VERSION = '0.3.3'


def compile(flask_app, hash_id, run_ids=None, build=False):
    """ Compile analysis_id. Validate analysis using pybids and
    writout analysis bundle
    Args:
        hash_id (str): analysis hash_id
        run_ids (list): Optional list of runs to include
        build (bool): Validate in pybids?
    """
    FILE_DATA = Path(flask_app.config['FILE_DIR'])
    analysis_object = Analysis.query.filter_by(hash_id=hash_id).one()

    try:
        a_id, analysis, resources, pes, bids_dir,\
         task_name, TR = analysis_to_json(
            hash_id, run_ids)
    except Exception as e:
        update_record(
            analysis_object,
            exception=e,
            traceback='Error deserializing analysis'
        )
        raise

    try:
        tmp_dir, bundle_paths, _ = build_analysis(
            analysis, pes, bids_dir, task_name, run_ids, build=build)
    except Exception as e:
        update_record(
            analysis_object,
            exception=e,
            traceback='Error building analysis'
        )
        raise

    try:
        sidecar = {'RepetitionTime': TR}
        resources['validation_hash'] = Hashids(
            flask_app.config['SECONDARY_HASH_SALT'],
            min_length=10).encode(a_id)
        resources['version_required'] = MIN_CLI_VERSION

        # Write out JSON files to tmp_dir
        bundle_paths += write_jsons([
                (analysis, 'analysis'),
                (resources, 'resources'),
                (analysis.get('model'), 'model'),
                (sidecar, f'task-{task_name}_bold')
                ], tmp_dir)

        # Save bundle as tarball
        bundle_path = str(
            FILE_DATA / f'analyses/{analysis["hash_id"]}_bundle.tar.gz')
        write_tarball(bundle_paths, bundle_path)
    except Exception as e:
        update_record(
            analysis_object,
            exception=e,
            traceback='Error writing tarball bundle'
        )
        raise

    return update_record(
        analysis_object,
        status='PASSED',
        bundle_path=bundle_path
    )


def generate_report(flask_app, hash_id, report_id):
    """ Generate report for analysis
    Args:
        hash_id (str): analysis hash_id
        report_id (int): Report object id
        run_ids (list): List of run ids
        sampling_rate (float): Rate to re-sample design matrix in Hz
        scale (bool): Scale columns in dm plot
    """
    FILE_DATA = Path(flask_app.config['FILE_DIR'])
    domain = flask_app.config['SERVER_NAME']
    report_obj = Report.query.filter_by(id=report_id).one()

    try:
        _, analysis, resources, pes, bids_dir, task_name, _ = analysis_to_json(
            hash_id, report_obj.runs)
    except Exception as e:
        update_record(
            report_obj,
            exception=e,
            traceback='Error deserializing analysis'
        )
        raise

    try:
        pre_warnings(analysis, pes, report_obj)
    except Exception as e:
        update_record(
            report_obj,
            exception=e,
            traceback='Error generating warnings'
        )

    try:
        _, _, bids_analysis = build_analysis(
            analysis, pes, bids_dir, task_name, report_obj.runs)
    except Exception as e:
        update_record(
            report_obj,
            exception=e,
            traceback='Error validating analysis'
        )
        raise

    try:
        outdir = FILE_DATA / 'reports' / analysis['hash_id']
        outdir.mkdir(exist_ok=True)

        first = bids_analysis.steps[0]
        results = {
            'design_matrix': [],
            'design_matrix_plot': [],
            'design_matrix_corrplot': []
            }

        hrf = [t for t in
               analysis['model']['Steps'][0]['Transformations']
               if t['Name'] == 'Convolve']

        sampling_rate = report_obj.sampling_rate
        if sampling_rate is None:
            sampling_rate = 'TR'

        for dm in first.get_design_matrix(
          mode='dense', force=True, entities=False,
          sampling_rate=sampling_rate):
            dense = impute_confounds(dm.dense)
            if hrf:
                dense = sort_dm(dense, interest=hrf[0]['Input'])

            builder = PathBuilder(
                outdir, domain, analysis['hash_id'], dm.entities)
            # Writeout design matrix
            out, url = builder.build('design_matrix', 'tsv')
            results['design_matrix'].append(url)
            dense.to_csv(out, index=False)

            dm_plot = plot_design_matrix(dense, scale=report_obj.scale)
            results['design_matrix_plot'].append(dm_plot)

            corr_plot = plot_corr_matrix(dense)
            results['design_matrix_corrplot'].append(corr_plot)
    except Exception as e:
        return update_record(
            report_obj,
            exception=e,
            traceback='Error generating report outputs'
        )
        raise

    return update_record(
        report_obj,
        result=results,
        status='OK'
        )
