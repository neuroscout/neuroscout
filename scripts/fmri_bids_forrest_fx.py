""""
Usage: fmri_bids [options] <bids_dir> <task>

-m <bids_model>         JSON specification of model and contrasts.
                        Defaults to simple contrasts for each predictor.
-t <transformations>    Transformation to apply to events.
-r <read_options>       Options to pass to BIDS events reader.
-s <subject_id>         Subjects to analyze. [default: all]
-o <output>             Output folder.
                        [default: <bids_dir>/derivatives/fmri_bids]
--jobs=<n>              Number of parallel jobs [default: 1].
"""
from nipype import config
config.enable_debug_mode()

from docopt import docopt

from nipype.pipeline.engine import Workflow, Node
import nipype.algorithms.modelgen as model
import nipype.algorithms.events as events
from nipype.interfaces.io import DataGrabber, DataSink

from nipype.interfaces.utility import Function, IdentityInterface
from nipype.workflows.fmri.fsl import (create_modelfit_workflow,
                                       create_fixed_effects_flow)
import json
import os

from bids.grabbids import BIDSLayout


def validate_arguments(args):
    """ Validate and preload command line arguments """

    bids_dir = os.path.abspath(args['<bids_dir>'])

    layout = BIDSLayout(bids_dir)

    ### Check data ###
    if 'bold' not in layout.get_types():
        raise Exception("BIDS project does not contain"
                        " preprocessed BOLD data.")

    task = args['<task>']
    ## Check that task exists
    if task not in layout.get_tasks():
        raise Exception("Task {} not found in BIDS project".format(task))

    subject = args['-s'].split(" ")
    ## Assign subject ids
    all_subjects = layout.get_subjects()
    if subject == 'all':
        subject = all_subjects
    else:
        for s in subject:
            if s not in all_subjects:
                raise Exception("Invalid subject id {}.".format(s))

    out_dir = args['-o']
    if out_dir == '<bids_dir>/derivatives/fmri_bids':
        out_dir = os.path.join(bids_dir, 'derivatives/fmri_bids')
    else:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    transformations = args['-t']
    if transformations is not None:
        try:
            t = json.load(open(transformations, 'r'))
        except ValueError:
            raise Exception("Invalid transformation JSON file")
        except IOError:
            raise Exception("Transformation file not found")

    ## Add options checker here
    read_options = None

    jobs = int(args['--jobs'])

    return (bids_dir, task, out_dir, subject, transformations, read_options, jobs)


def get_events(bids_dir, subject_id, task_id):
    from bids.grabbids import BIDSLayout
    from tempfile import NamedTemporaryFile
    import pandas as pd

    ### Hardcoded stuff
    top_cats = ['clothing', 'face', 'property', 'product']
    ref = pd.read_csv('/mnt/c/Users/aid338/Documents/neuroscout_scripts/forrest_extract_results/visionapi_labels_objectcategories.csv')

    def lookup(row):
        """ This function looks up the featurex feats in ref file, given a stim name """
        confs = []
        for cat in top_cats:
            res = ref[(ref.label == cat) & (ref.stimulus==row.stim_file)]
            if res.shape[0] == 1:
                conf = res.confidence.values[0]
            else:
                conf = 0
            confs.append(conf)

        return pd.Series(confs, index=top_cats)

    layout = BIDSLayout(bids_dir)
    event_files = layout.get(
        type='events', return_type='file', subject=subject_id, task=task_id)

    all_runs = []
    for f in event_files:
        df = pd.read_table(f)
        new_events = pd.concat([df[['onset', 'duration']], df.apply(lookup, axis=1)], axis=1)
        new_events = pd.melt(new_events, id_vars=['onset', 'duration'], var_name='trial_type', value_name='amplitude')

        with NamedTemporaryFile(delete=False, mode='w') as tf:
            all_runs.append(tf.name)
            new_events.to_csv(tf.file, sep=str('\t'), index=False)

    return all_runs
#
# def create_contrasts(contrasts, condition):
#     pass


def run_worflow(bids_dir, task, out_dir=None, subjects=None,
                transformations=None, read_options=None, jobs=1):

    layout = BIDSLayout(bids_dir)
    runs = layout.get_runs(task=task)
    TR = json.load(open(os.path.join(bids_dir, 'task-' + task + '_bold.json'), 'r'))['RepetitionTime']

    ## Meta-workflow
    wf = Workflow(name='fmri_bids')
    wf.base_dir = os.path.join(bids_dir, 'derivatives/fmri_first_wd')

    ## Infosource
    infosource = Node(IdentityInterface(fields=['subject_id']),
                     name="infosource")
    infosource.iterables = ('subject_id', subjects)

    ## Datasource
    datasource = Node(DataGrabber(infields=['subject_id'],
                                         outfields=['func', 'mask']), name='datasource')
    datasource.inputs.base_directory = bids_dir
    datasource.inputs.template = '*'
    datasource.inputs.sort_filelist = True
    datasource.inputs.field_template = dict(
        func='derivatives/studyforrest-data-aligned/sub-01/in_bold3Tp2/sub-%s_task-%s_%s_bold.nii.gz',
        mask='derivatives/studyforrest-data-templatetransforms/sub-%s/bold3Tp2/brain_mask.nii.gz',
        field_file='derivatives/registration/anat2target_transform/_subject_id_%s/brain_fieldwarp.nii.gz')
    datasource.inputs.template_args = dict(func=[['subject_id', 'task', 'runs']],
        mask=[['subject_id']], field_files=[['subject_id']])
    datasource.inputs.runs = runs
    datasource.inputs.task = task

    ## BIDS event tsv getter
    event_getter = Node(name='eventgetter', interface=Function(
                           input_names=['bids_dir', 'subject_id', 'task_id'],
                           output_names=["events"], function=get_events))

    event_getter.inputs.bids_dir = bids_dir
    event_getter.inputs.task_id = task

    ## Event and model specs
    eventspec = Node(interface=events.SpecifyEvents(), name="eventspec")
    modelspec = Node(interface=model.SpecifyModel(), name="modelspec")

    eventspec.inputs.input_units = 'secs'
    eventspec.inputs.time_repetition = TR
    if transformations is not None:
        eventspec.inputs.transformations = transformations

    wf.connect(event_getter, 'events', eventspec, 'bids_events')

    modelspec.inputs.input_units = 'secs'
    modelspec.inputs.time_repetition = TR
    modelspec.inputs.high_pass_filter_cutoff = 100.

    wf.connect(datasource, 'func', modelspec, 'functional_runs')
    wf.connect(eventspec, 'subject_info', modelspec, 'subject_info')
    wf.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                (infosource, event_getter, [('subject_id', 'subject_id')])])

    ## Model fitting
    conditions = ['clothing', 'face', 'property', 'product']
    contrasts = [['clothing', 'T', conditions,      [1, 0, 0, 0]],
                 ['face', 'T', conditions,          [0, 1, 0, 0]],
                 ['property', 'T', conditions,      [0, 0, 1, 0]],
                 ['product', 'T', conditions,       [0, 0, 0, 1]],
                 ['faces vs all', 'T', conditions,  [-1, 3, -1, -1]],
                 ['faces vs prop', 'T', conditions, [0, 1, 0, -1]],
                 ['prop vs all', 'T', conditions,   [-1, -1, -1, -3]],
                 ['prop vs faces', 'T', conditions, [0, -1, 0, 1]]]


    modelfit = create_modelfit_workflow()

    modelfit.inputs.inputspec.contrasts = contrasts
    modelfit.inputs.inputspec.interscan_interval = TR
    modelfit.inputs.inputspec.model_serial_correlations = True
    modelfit.inputs.inputspec.bases = {'dgamma': {'derivs': True}}

    wf.connect(modelspec, 'session_info', modelfit, 'inputspec.session_info')
    wf.connect(datasource, 'func', modelfit, 'inputspec.functional_data')


    ### Fixed effects
    fixed_fx = create_fixed_effects_flow()
    # pick_first = lambda x: x[0]
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

    ### Apply normalization warp to copes, varcopes and zstats
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

    mergefunc = pe.Node(niu.Function(input_names=['copes', 'varcopes',
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
    register.connect(mergefunc, 'out_files', warpall, 'in_file')
    # register.connect(mean2anatbbr, 'out_matrix_file', warpall, 'premat')
    # register.connect(inputnode, 'target_image', warpall, 'ref_file')
    warpall.inputs.ref_file = fsl.Info.standard_image('MNI152_T1_2mm_brain.nii.gz')
    register.connect(datasource, 'field_file',
                     warpall, 'field_file')

    def split_files(in_files, splits):
        copes = in_files[:splits[0]]
        varcopes = in_files[splits[0]:(splits[0] + splits[1])]
        zstats = in_files[(splits[0] + splits[1]):]
        return copes, varcopes, zstats

    splitfunc = pe.Node(niu.Function(input_names=['in_files', 'splits'],
                                     output_names=['copes', 'varcopes',
                                                   'zstats'],
                                     function=split_files),
                      name='split_files')
    wf.connect(mergefunc, 'splits', splitfunc, 'splits')
    wf.connect(warpall, 'out_file',
               splitfunc, 'in_files')

    ### Datasink
    datasink = Node(DataSink(), name="datasink")
    datasink.inputs.base_directory = os.path.join(bids_dir, 'derivatives')
    datasink.inputs.container = 'fmri_firstlevel'

    wf.connect([(modelfit.get_node('modelgen'), datasink,
                 [('design_cov', 'qa.model'),
                  ('design_image', 'qa.model.@matrix_image'),
                  ('design_file', 'qa.model.@matrix'),
                  ])])

    wf.connect([(fixed_fx.get_node('outputspec'), datasink,
                 [('res4d', 'res4d'),
                  ('copes', 'copes'),
                  ('varcopes', 'varcopes'),
                  ('zstats', 'ls'),
                  ('tstats', 'tstats')])
                ])

    wf.connect([(splitfunc, datasink,
                 [('copes', 'copes.mni'),
                  ('varcopes', 'varcopes.mni'),
                  ('zstats', 'zstats.mni'),
                  ])])

    if jobs == 1:
        wf.run()
    else:
        print("Running {} processes".format(jobs))
        wf.run(plugin='MultiProc', plugin_args={'n_procs' : jobs})

if __name__ == '__main__':
    arguments = docopt(__doc__)
    run_worflow(*validate_arguments(arguments))
