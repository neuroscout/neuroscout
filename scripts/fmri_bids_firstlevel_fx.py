""""
Usage:
    fmri_bids_first run [options] <bids_dir> <task> <in_dir> <out_dir>
    fmri_bids_first make [options] <bids_dir> <task> [<in_dir> <out_dir>]

-t <transformations>    Transformation to apply to events.
-s <subject_id>         Subjects to analyze. [default: all]
-r <run_ids>            Runs to analyze. [default: all]
-f <fwhm>               Smoothing kernel file to use. [default: 5]
-w <work_dir>           Working directory.
                        [default: /tmp]
-c                      Stop on first crash.
--jobs=<n>              Number of parallel jobs [default: 1].
"""
import json
import os
from docopt import docopt

from nipype.pipeline.engine import Workflow, Node, MapNode
import nipype.algorithms.modelgen as model
import nipype.algorithms.events as events
from nipype.interfaces.io import DataGrabber, DataSink
from nipype.interfaces import fsl

from nipype.interfaces.utility import Function, IdentityInterface
from nipype.workflows.fmri.fsl import (create_modelfit_workflow,
                                       create_fixed_effects_flow)
from nipype.algorithms.rapidart import ArtifactDetect

from bids.grabbids import BIDSLayout


def get_events(bids_dir, subject_id, runs, task_id):
    """ Get a single subjects event files """
    from bids.grabbids import BIDSLayout
    layout = BIDSLayout(bids_dir)
    event_files = [layout.get(
        type='events', return_type='file', subject=subject_id, run=r, task=task_id)[0] for r in runs]
    return event_files


def get_features(event_files):
    """ Inject extracted features into event files """
    import pandas as pd
    from glob import glob
    from os import path
    import numpy as np
    import re
    from functools import partial

    event_files = sorted(event_files)
    features = sorted(glob(
        '/mnt/c/Users/aid338/Documents/neuroscout_scripts/forrest_extract_results/clip*'))

    def setmaxConfidence(row):
        maxcol = row['maxFace']
        if pd.notnull(maxcol):
            val = row[maxcol]
        else:
            val = 0
        return val

    def polyArea(x, y):
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    def computeMaxFaceArea(row):
        maxcol = row['maxFace']

        if pd.notnull(maxcol):
            prepend = re.sub('face_detectionConfidence', '', maxcol)
            x = []
            y = []

            for i in range(1, 5):
                x.append(row[prepend + 'boundingPoly_vertex{}_x'.format(i)])
                y.append(row[prepend + 'boundingPoly_vertex{}_y'.format(i)])

            val = polyArea(x, y)
        else:
            val = 0
        return val

    def calcNumFaces(confidence_cols, row):
        return (row[confidence_cols].isnull() == False).sum()

    new_event_files = []
    for i, run_file in enumerate(event_files):
        run_events = pd.read_table(run_file)
        run_features = pd.read_csv(features[i])

        # Move onset to when clip begins
        clip_start = run_events.iloc[0].onset
        run_features['onset'] = run_features['onset'] + clip_start

        # Calculate computed values
        confidence_cols = [c for c in run_features.columns if c.endswith(
            'face_detectionConfidence')]
        run_features['maxFace'] = run_features.apply(lambda x: x[confidence_cols].idxmax(), axis=1)
        run_features['maxfaceConfidence'] = run_features.apply(setmaxConfidence, axis=1)
        run_features['maxfaceArea'] = run_features.apply(computeMaxFaceArea, axis=1)
        partialnFaces = partial(calcNumFaces, confidence_cols)
        run_features['numFaces'] = run_features.apply(partialnFaces, axis=1)

        # Select only relevant columns
        run_features = run_features[['onset', 'duration', 'maxfaceConfidence', 'maxfaceArea', 'numFaces']]
        run_features = pd.melt(run_features, id_vars=['onset', 'duration'],
                               value_name='amplitude', var_name='trial_type')

        # Save to curr dir, but give abs path
        base_file = path.splitext(path.basename(run_file))
        new_file = path.abspath('{}_fx{}'.format(*base_file))
        new_event_files.append(new_file)
        run_features.to_csv(new_file, sep=str('\t'), index=False)

    return new_event_files


def first_level(bids_dir, task, in_dir, subjects, runs, out_dir=None,
                work_dir=None, transformations=None, read_options=None, fwhm=5):
    """
    Set up workflow
    """
    wf = Workflow(name='first_level')
    if work_dir:
        wf.base_dir = work_dir
    """
    Define conditions and contrasts
    (this should be auto-generated or loaded from model json in the future)
    """

    conditions = ['maxfaceConfidence', 'numFaces_orth']
    contrasts = [['maxfaceConfidence', 'T', conditions, [1, 0]],
                 ['maxfaceConfidencevall', 'T', conditions, [1, -1]],
                 ['numFaces_orth', 'T', conditions, [0, 1]],
                 ['numFaces_orthvall', 'T', conditions, [-1, 1]]]

    TR = json.load(open(os.path.join(
        bids_dir, 'task-' + task + '_bold.json'), 'r'))['RepetitionTime']
    """
    Subject iterator
    """
    infosource = Node(IdentityInterface(fields=['subject_id']),
                      name="infosource")
    infosource.iterables = ('subject_id', subjects)

    """
    Grab data for each subject
    #### ADD func2anat_transform
    #### RENAME anat2target_transform
    """

    datasource = Node(DataGrabber(infields=['subject_id'],
                                  outfields=['smooth_func', 'mask', 'field_file',
                                             'realignment_parameters', 'dil_mask']),
                      name='datasource')
    datasource.inputs.base_directory = in_dir
    datasource.inputs.template = '*'
    datasource.inputs.sort_filelist = True
    datasource.inputs.field_template = dict(
        smooth_func='smooth_func/%s/smooth_func/sub-%s_task-%s_%s_bold_smooth_mask.nii.gz',
        mask='templatetransforms/sub-%s/bold3Tp2/brain_mask.nii.gz',
        field_file='registration/anat2target_transform/%s/brain_fieldwarp.nii.gz',
        realignment_parameters='aligned/sub-%s/in_bold3Tp2/sub-%s_task-%s_%s_bold_mcparams.txt',
        dil_mask='smooth_func/%s/dil_mask/sub-%s_task-%s_%s_bold_dilmask.nii.gz')
    datasource.inputs.template_args = dict(
        smooth_func=[['fwhm', 'subject_id', 'task', 'runs']],
        mask=[['subject_id']], field_file=[['subject_id']],
        realignment_parameters=[['subject_id', 'subject_id', 'task', 'runs']],
        dil_mask=[['fwhm', 'subject_id', 'task', 'runs']])
    datasource.inputs.runs = runs
    datasource.inputs.task = task
    datasource.inputs.fwhm = fwhm

    """
    Artifact detection
    """
    art = MapNode(interface=ArtifactDetect(use_differences=[True, False],
                                           use_norm=True,
                                           norm_threshold=1,
                                           zintensity_threshold=3,
                                           parameter_source='FSL',
                                           mask_type='file'),
                  iterfield=['realigned_files', 'realignment_parameters',
                             'mask_file'],
                  name="art")

    wf.connect([(datasource, art, [('realignment_parameters',
                                    'realignment_parameters'),
                                   ('smooth_func',
                                    'realigned_files'),
                                   ('dil_mask', 'mask_file')])])
    """
    Get events.tsv file for each subject
    """

    event_getter = Node(name='event_getter', interface=Function(
        input_names=['bids_dir', 'subject_id', 'runs', 'task_id'],
        output_names=["events"], function=get_events))

    event_getter.inputs.bids_dir = bids_dir
    event_getter.inputs.task_id = task
    event_getter.inputs.runs = runs
    wf.connect(infosource, 'subject_id', event_getter, 'subject_id')

    """
    Add pliers features
    """

    fx_getter = Node(name='fx_getter', interface=Function(
        input_names=['event_files'],
        output_names=["transformed_events"], function=get_features))
    wf.connect(event_getter, 'events', fx_getter, 'event_files')

    """
    Specify model, apply transformations and specify fMRI model
    """

    eventspec = Node(interface=events.SpecifyEvents(), name="eventspec")
    modelspec = Node(interface=model.SpecifyModel(), name="modelspec")

    eventspec.inputs.input_units = 'secs'
    eventspec.inputs.time_repetition = TR
    if transformations is not None:
        eventspec.inputs.transformations = transformations

    modelspec.inputs.input_units = 'secs'
    modelspec.inputs.time_repetition = TR
    modelspec.inputs.high_pass_filter_cutoff = 100.

    wf.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                (datasource, modelspec, [('smooth_func', 'functional_runs')]),
                (datasource, modelspec, [('realignment_parameters', 'realignment_parameters')]),
                (eventspec, modelspec, [('subject_info', 'subject_info')]),
                (fx_getter, eventspec, [('transformed_events', 'bids_events')])])

    """
    Fit model to each run
    """

    modelfit = create_modelfit_workflow()

    modelfit.inputs.inputspec.contrasts = contrasts
    modelfit.inputs.inputspec.interscan_interval = TR
    modelfit.inputs.inputspec.model_serial_correlations = True
    modelfit.inputs.inputspec.bases = {'dgamma': {'derivs': False}}

    wf.connect(modelspec, 'session_info', modelfit, 'inputspec.session_info')
    wf.connect(datasource, 'smooth_func', modelfit, 'inputspec.functional_data')

    """
    Fixed effects workflow to combine runs
    """

    fixed_fx = create_fixed_effects_flow()
    wf.connect(datasource, 'mask', fixed_fx, 'flameo.mask_file')

    def sort_copes(copes, varcopes, contrasts):
        import numpy as np
        if not isinstance(copes, list):
            copes = [copes]
            varcopes = [varcopes]
        num_copes = len(contrasts)
        n_runs = len(copes)
        all_copes = np.array(copes).flatten()
        all_varcopes = np.array(varcopes).flatten()
        outcopes = all_copes.reshape(int(len(all_copes) / num_copes),
                                     num_copes).T.tolist()
        outvarcopes = all_varcopes.reshape(int(len(all_varcopes) / num_copes),
                                           num_copes).T.tolist()
        return outcopes, outvarcopes, n_runs

    cope_sorter = Node(Function(input_names=['copes', 'varcopes',
                                             'contrasts'],
                                output_names=['copes', 'varcopes',
                                              'n_runs'],
                                function=sort_copes),
                       name='cope_sorter')
    cope_sorter.inputs.contrasts = contrasts

    wf.connect([(modelfit, cope_sorter, [('outputspec.copes', 'copes')]),
                (modelfit, cope_sorter, [('outputspec.varcopes', 'varcopes')]),
                (cope_sorter, fixed_fx, [('copes', 'inputspec.copes'),
                                         ('varcopes', 'inputspec.varcopes'),
                                         ('n_runs', 'l2model.num_copes')]),
                (modelfit, fixed_fx, [('outputspec.dof_file',
                                       'inputspec.dof_files'),
                                      ])
                ])

    """
    Apply normalization warp (to MNI) to copes, varcopes, and tstats
    """

    def merge_files(copes, varcopes, zstats):
        out_files = []
        splits = []
        out_files.extend(copes)
        splits.append(len(copes))
        out_files.extend(varcopes)
        splits.append(len(varcopes))
        out_files.extend(zstats)
        splits.append(len(zstats))
        return out_files, splits

    mergefunc = Node(Function(input_names=['copes', 'varcopes',
                                           'zstats'],
                              output_names=['out_files', 'splits'],
                              function=merge_files),
                     name='merge_files')

    wf.connect([(fixed_fx.get_node('outputspec'), mergefunc,
                 [('copes', 'copes'),
                  ('varcopes', 'varcopes'),
                  ('zstats', 'zstats'),
                  ])])

    warpall = MapNode(fsl.ApplyWarp(interp='spline'),
                      iterfield=['in_file'],
                      nested=True,
                      name='warpall')
    wf.connect(mergefunc, 'out_files', warpall, 'in_file')

    warpall.inputs.ref_file = fsl.Info.standard_image('MNI152_T1_2mm_brain.nii.gz')
    wf.connect(datasource, 'field_file',
               warpall, 'field_file')

    def split_files(in_files, splits):
        copes = in_files[:splits[0]]
        varcopes = in_files[splits[0]:(splits[0] + splits[1])]
        zstats = in_files[(splits[0] + splits[1]):]
        return copes, varcopes, zstats

    splitfunc = Node(Function(input_names=['in_files', 'splits'],
                              output_names=['copes', 'varcopes',
                                            'zstats'],
                              function=split_files),
                     name='split_files')
    wf.connect(mergefunc, 'splits', splitfunc, 'splits')
    wf.connect(warpall, 'out_file',
               splitfunc, 'in_files')

    """
    Save to datasink
    """

    def get_subs(subject_id, conds):
        """ Generate substitutions """
        subs = [('_subject_id_%s' % subject_id, '')]

        for i in range(len(conds)):
            subs.append(('_flameo%d/cope1.' % i, 'cope%02d.' % (i + 1)))
            subs.append(('_flameo%d/varcope1.' % i, 'varcope%02d.' % (i + 1)))
            subs.append(('_flameo%d/zstat1.' % i, 'zstat%02d.' % (i + 1)))
            subs.append(('_flameo%d/tstat1.' % i, 'tstat%02d.' % (i + 1)))
            subs.append(('_flameo%d/res4d.' % i, 'res4d%02d.' % (i + 1)))
            subs.append(('_warpall%d/cope1_warp.' % i,
                         'cope%02d.' % (i + 1)))
            subs.append(('_warpall%d/varcope1_warp.' % (len(conds) + i),
                         'varcope%02d.' % (i + 1)))
            subs.append(('_warpall%d/zstat1_warp.' % (2 * len(conds) + i),
                         'zstat%02d.' % (i + 1)))
            subs.append(('_warpall%d/cope1_trans.' % i,
                         'cope%02d.' % (i + 1)))
            subs.append(('_warpall%d/varcope1_trans.' % (len(conds) + i),
                         'varcope%02d.' % (i + 1)))
            subs.append(('_warpall%d/zstat1_trans.' % (2 * len(conds) + i),
                         'zstat%02d.' % (i + 1)))
        return subs

    subsgen = Node(Function(input_names=['subject_id', 'conds'],
                            output_names=['substitutions'],
                            function=get_subs),
                   name='subsgen')

    datasink = Node(DataSink(), name="datasink")
    if out_dir is not None:
        datasink.inputs.base_directory = os.path.abspath(out_dir)

    wf.connect(infosource, 'subject_id', datasink, 'container')
    wf.connect(infosource, 'subject_id', subsgen, 'subject_id')
    wf.connect(subsgen, 'substitutions', datasink, 'substitutions')
    subsgen.inputs.conds = contrasts

    wf.connect([(modelfit.get_node('modelgen'), datasink,
                 [('design_cov', 'qa.model'),
                  ('design_image', 'qa.model.@matrix_image'),
                  ('design_file', 'qa.model.@matrix'),
                  ])])

    wf.connect([(fixed_fx.get_node('outputspec'), datasink,
                 [('res4d', 'res4d'),
                  ('copes', 'copes'),
                  ('varcopes', 'varcopes'),
                  ('zstats', 'zstats'),
                  ('tstats', 'tstats')])
                ])

    wf.connect([(splitfunc, datasink,
                 [('copes', 'copes.mni'),
                  ('varcopes', 'varcopes.mni'),
                  ('zstats', 'zstats.mni'),
                  ])])

    return wf


def validate_arguments(args):
    """ Validate and preload command line arguments """

    # Clean up names
    var_names = {'<bids_dir>': 'bids_dir',
                 '<task>': 'task',
                 '<out_dir>': 'out_dir',
                 '<in_dir>': 'in_dir',
                 '-w': 'work_dir',
                 '-s': 'subjects',
                 '-r': 'runs',
                 '-t': 'transformations',
                 '-f': 'fwhm'}

    if args.pop('-c'):
        from nipype import config
        cfg = dict(logging=dict(workflow_level='DEBUG'),
                   execution={'stop_on_first_crash': True})
        config.update_config(cfg)

    for old, new in var_names.iteritems():
        args[new] = args.pop(old)

    for directory in ['out_dir', 'work_dir']:
        if args[directory] is not None:
            args[directory] = os.path.abspath(args[directory])
            if not os.path.exists(args[directory]):
                os.makedirs(args[directory])

    args['bids_dir'] = os.path.abspath(args['bids_dir'])
    layout = BIDSLayout(args['bids_dir'])

    # Check BOLD data
    if 'bold' not in layout.get_types():
        raise Exception("BIDS project does not contain"
                        " preprocessed BOLD data.")

    # Check that task exists
    if args['task'] not in layout.get_tasks():
        raise Exception("Task not found in BIDS project")

    # Check subject ids and runs
    for entity in ['subjects', 'runs']:
        all_ents = layout.get(
            target=entity[:-1], return_type='id', session='movie')

        if args[entity] == 'all':
            args[entity] = all_ents
        else:
            args[entity] = args[entity].split(" ")
            for e in args[entity]:
                if e not in all_ents:
                    raise Exception("Invalid {} id {}.".format(entity[:-1], e))

    if args['transformations'] is not None:
        args['transformations'] = os.path.abspath(args['transformations'])
        try:
            json.load(open(args['transformations'], 'r'))
        except ValueError:
            raise Exception("Invalid transformation JSON file")
        except IOError:
            raise Exception("Transformation file not found")

    args['--jobs'] = int(args['--jobs'])

    return args


if __name__ == '__main__':
    arguments = validate_arguments(docopt(__doc__))
    jobs = arguments.pop('--jobs')
    run = arguments.pop('run')
    arguments.pop('make')
    wf = first_level(**arguments)

    if run:
        if jobs == 1:
            wf.run()
        else:
            wf.run(plugin='MultiProc', plugin_args={'n_procs': jobs})
