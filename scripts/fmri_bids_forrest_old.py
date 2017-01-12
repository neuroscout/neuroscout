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

import nipype.pipeline.engine as pe
import nipype.algorithms.modelgen as model
import nipype.algorithms.events as events
import nipype.interfaces.io as nio

from nipype.interfaces.utility import Function
from nipype.workflows.fmri.fsl.estimate import create_modelfit_workflow
from nipype.workflows.fmri.fsl import create_fixed_effects_flow

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

    subject = args['-s']
    ## Assign subject ids
    all_subjects = layout.get_subjects()
    if subject is None:
        subject = all_subjects
    else:
        if subject not in all_subjects:
            raise Exception("Invalid subject id.")
        subject = [subject]

    out_dir = args['-o']
    if out_dir is None:
        out_dir = os.path.join(bids_dir, 'derivatives/fmri_prep/derivatives/')
    else:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    transformations = args['-t']
    if transformations is not None:
        try:
            transformations = json.load(open(transformations, 'r'))
        except ValueError:
            raise Exception("Invalid transformation JSON file")
        except IOError:
            raise Exception("Transformation file not found")

    ## Add options checker here
    read_options = None

    return (bids_dir, task, out_dir, subject, transformations, read_options)


def get_events(bids_dir, subject_id):
    from bids.grabbids import BIDSLayout
    layout = BIDSLayout(bids_dir)
    return layout.get(
        type='events', return_type='file', subject=subject_id)

    
def create_contrasts(contrasts, condition):
    pass


def run_worflow(bids_dir, task, out_dir=None, subjects=None,
                transformations=None, read_options=None):
    layout = BIDSLayout(bids_dir)

    # Add Info Source to loop over subjects
    # infosource = pe.Node(niu.IdentityInterface(fields=['subject_id',
    #                                                'run_id']),
    #                  name='infosource')
    
    ## This should probably be added to pybids, to be able to quiery meta data for task not just file
    TR = json.load(open(os.path.join(bids_dir, 'task-' + task + '_bold.json'), 'r'))['RepetitionTime']

    wf = pe.Workflow(name='fmri_bids')
    wf.base_dir = os.path.join(bids_dir, out_dir)

    datasource = pe.Node(nio.DataGrabber(infields=['subject_id', 'runs'],
                                         outfields=['func']), name='datasource')
    datasource.inputs.base_directory = os.path.join(bids_dir, 'derivatives/studyforrest-data-aligned/')
    datasource.inputs.template = '*'
    datasource.inputs.sort_filelist = True
    datasource.inputs.field_template = dict(func='sub-%s/v/sub-%s_task-' + task + '_run-%s_bold.nii.gz')
    datasource.inputs.template_args = dict(func=[['subject_id', 'subject_id', 'runs']])
    datasource.inputs.subject_id = subjects
    datasource.inputs.runs = layout.get_runs()

    event_getter = pe.Node(name='eventgetter', interface=Function(
                           input_names=['bids_dir', 'subject_id'],
                           output_names=["events"], function=get_events))

    ### Hardcoded stuff
    top_cats = ['clothing', 'face', 'property', 'product', 'black and white', 'black']

    event_getter.inputs.bids_dir = bids_dir
    event_getter.inputs.subject_id = subjects

    eventspec = pe.Node(interface=events.SpecifyEvents(), name="eventspec")
    modelspec = pe.Node(interface=model.SpecifyModel(), name="modelspec")

    eventspec.inputs.input_units = 'secs'
    eventspec.inputs.time_repetition = TR
    eventspec.inputs.transformations = '/vagrant/local/tests/transformations.json'

    wf.connect(event_getter, 'events', eventspec, 'bids_events')

    modelspec.inputs.input_units = 'secs'
    modelspec.inputs.time_repetition = TR
    modelspec.inputs.high_pass_filter_cutoff = 128.

    wf.connect(datasource, 'func', modelspec, 'functional_runs')
    wf.connect(eventspec, 'subject_info', modelspec, 'subject_info')

    ## Model fitting
    ## Temporary contrasts
    conditions = ['congruent_correct', 'incongruent_correct']
    contrasts = [['first',   'T', conditions, [1, 0]],
                 ['second',   'T', conditions, [0, 1]]]

    modelfit = create_modelfit_workflow()

    modelfit.inputs.inputspec.contrasts = contrasts
    modelfit.inputs.inputspec.interscan_interval = TR
    modelfit.inputs.inputspec.model_serial_correlations = True
    modelfit.inputs.inputspec.film_threshold = 1000
    modelfit.inputs.inputspec.bases = {'dgamma': {'derivs': False}}

    wf.connect(modelspec, 'session_info', modelfit, 'inputspec.session_info')
    wf.connect(datasource, 'func', modelfit, 'inputspec.functional_data')


    #### Fixed effects
    fixed_fx = create_fixed_effects_flow()

    wf.connect([(mask, fixed_fx, [('mask_file', 'flameo.mask_file')]),
                            (modelfit, cope_sorter, [('outputspec.copes', 'copes')]),
                            (modelfit, cope_sorter, [('outputspec.varcopes', 'varcopes')]),
                            (cope_sorter, fixed_fx, [('copes', 'inputspec.copes'),
                                                                             ('varcopes', 'inputspec.varcopes'),
                                                                             ('n_runs', 'l2model.num_copes')]),
                            (modelfit, fixed_fx, [('outputspec.dof_file',
                                                                            'inputspec.dof_files')])])
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
                                                                ])])''

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
    wf.connect(registration, 'outputspec.transforms',
                         splitfunc, 'in_files')

    # Datasink
    datasink = pe.Node(nio.DataSink(), name="datasink")
    datasink.inputs.base_directory = os.path.join(out_dir)
    datasink.inputs.container = 'outputs'

    wf.connect(modelfit, 'outputspec.zfiles', datasink, 'zfiles')
    wf.connect(modelfit, 'outputspec.parameter_estimates', datasink, 'pes')
    wf.connect([(fixed_fx.get_node('outputspec'), datasink,
                                                             [('res4d', 'res4d'),
                                                                ('copes', 'copes'),
                                                                ('varcopes', 'varcopes'),
                                                                ('zstats', 'zstats'),
                                                                ('tstats', 'tstats')])
                                                             ])
    wf.run()


if __name__ == '__main__':
    arguments = docopt(__doc__)
    run_worflow(*validate_arguments(arguments))
