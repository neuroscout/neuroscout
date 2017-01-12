""""
Usage: fmri_bids [options] <bids_dir> <task>

-m <bids_model>         JSON specification of model and contrasts.
                        Defaults to simple contrasts for each predictor.
-t <transformations>    Transformation to apply to events.
-r <read_options>       Options to pass to BIDS events reader.
-s <subject_id>         Subjects to analyze. Otherwise run all. 
-o <output>             Output folder. 
                        Defaults to <bids_dir>/derivatives/fmri_bids
"""
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
    bids_dir = args['<bids_dir>']

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
    if subject is None:
        subject = all_subjects
    else:
        for s in subject:
            if s not in all_subjects:
                raise Exception("Invalid subject id {}.".format(s))

    out_dir = args['-o']
    if out_dir is None:
        out_dir = os.path.join(bids_dir, 'derivatives/fmri_prep/derivatives/')
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

    return (bids_dir, task, out_dir, subject, transformations, read_options)


def get_events(bids_dir, subject_id, task_id):
    from bids.grabbids import BIDSLayout
    from tempfile import NamedTemporaryFile
    import pandas as pd

    ### Hardcoded stuff
    top_cats = ['clothing', 'face', 'property', 'product', 'black and white']
    ref = pd.read_csv('/datasets/forrest/phase2/derivatives/featurex/all_object_googlevislabels.csv')

    def lookup(row):
        """ This function looks up the featurex feats in ref file, given a stim name """
        confs = []
        stim_name = row.stim_file.split('/')[2].split('.')[0]
        for cat in top_cats:
            res = ref[(ref.label == cat) & (ref.stimulus==stim_name)]
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
            new_events.to_csv(tf.file, sep='\t')

    return all_runs

def create_contrasts(contrasts, condition):
    pass


def run_worflow(bids_dir, task, out_dir=None, subjects=None,
                transformations=None, read_options=None):
    layout = BIDSLayout(bids_dir)
    runs = layout.get_runs()
    TR = json.load(open(os.path.join(bids_dir, 'task-' + task + '_bold.json'), 'r'))['RepetitionTime']

    ## Meta-workflow
    wf = Workflow(name='fmri_bids')
    wf.base_dir = os.path.join(bids_dir, 'derivatives/fmri_bids')

    ## Infosource
    infosource = Node(IdentityInterface(fields=['subject_id']),
                     name="infosource")
    infosource.iterables = ('subject_id', subjects)

    ## Datasource
    datasource = Node(DataGrabber(infields=['subject_id', 'runs'],
                                         outfields=['func', 'mask']), name='datasource')
    datasource.inputs.base_directory = bids_dir
    datasource.inputs.template = '*'
    datasource.inputs.sort_filelist = True
    datasource.inputs.field_template = dict(
        func='derivatives/studyforrest-data-aligned/sub-%s/in_bold3Tp2/sub-%s_task-%s_%s_bold.nii.gz',
        mask='sub-%s/ses-localizer/func/sub-%s_ses-localizer_task-%s_%s_defacemask.nii.gz')
    datasource.inputs.template_args = dict(func=[['subject_id', 'subject_id', 'task', 'runs']], 
        mask=[['subject_id', 'subject_id', 'task', 'runs']],)
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
    modelspec.inputs.high_pass_filter_cutoff = 128.

    wf.connect(datasource, 'func', modelspec, 'functional_runs')
    wf.connect(eventspec, 'subject_info', modelspec, 'subject_info')
    wf.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                (infosource, event_getter, [('subject_id', 'subject_id')])])

    ## Model fitting
    conditions = ['clothing', 'face', 'property', 'product', 'black and white']
    contrasts = [['clothing', 'T', conditions,      [1, 0, 0, 0, 0]],
                 ['face', 'T', conditions,          [0, 1, 0, 0, 0]],
                 ['property', 'T', conditions,      [0, 0, 1, 0, 0]],
                 ['product', 'T', conditions,       [0, 0, 0, 1, 0]],
                 ['bw', 'T', conditions,             [0, 0, 0, 0, 1]],
                 ['faces vs all', 'T', conditions,  [-1, 4, -1, -1, -1]],
                 ['faces vs prop', 'T', conditions, [0, 1, 0, -1, 0]],
                 ['prop vs all', 'T', conditions,   [-1, -1, -1, -4, -1]],
                 ['prop vs faces', 'T', conditions, [0, -1, 0, 1, 0]]]


    modelfit = create_modelfit_workflow()

    modelfit.inputs.inputspec.contrasts = contrasts
    modelfit.inputs.inputspec.interscan_interval = TR
    modelfit.inputs.inputspec.model_serial_correlations = True
    modelfit.inputs.inputspec.film_threshold = 1000
    modelfit.inputs.inputspec.bases = {'dgamma': {'derivs': False}}

    wf.connect(modelspec, 'session_info', modelfit, 'inputspec.session_info')
    wf.connect(datasource, 'func', modelfit, 'inputspec.functional_data')


    ### Fixed effects
    fixed_fx = create_fixed_effects_flow()
    pick_first = lambda x: x[0]
    wf.connect(datasource, ('mask', pick_first), fixed_fx, 'flameo.mask_file')

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

    ### Datasink
    datasink = Node(DataSink(), name="datasink")
    datasink.inputs.base_directory = os.path.join(bids_dir, 'derivatives')
    datasink.inputs.container = 'test_transform'

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

    wf.run()

if __name__ == '__main__':
    arguments = docopt(__doc__)
    run_worflow(*validate_arguments(arguments))
