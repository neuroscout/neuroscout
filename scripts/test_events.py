import nipype.pipeline.engine as pe
import nipype.algorithms.modelgen as model
import nipype.algorithms.events as events
import nipype.interfaces.io as nio

from nipype.interfaces.utility import Function
from nipype.workflows.fmri.fsl.estimate import create_modelfit_workflow

import json
import os


def get_events(bids_dir, subject_id, run_id):
    from bids.grabbids import BIDSLayout
    layout = BIDSLayout(bids_dir)
    return layout.get(
        type='events', return_type='file', subject=subject_id, run=run_id)

def create_contrasts(contrasts, condition):
    pass

def run_worflow(task, subjects, run, bids_dir):
    # Add Info Source to loop over subjects
    # infosource = pe.Node(niu.IdentityInterface(fields=['subject_id',
    #                                                'run_id']),
    #                  name='infosource')

    TR = json.load(open(os.path.join(bids_dir, 'task-' + task + '_bold.json'), 'r'))['RepetitionTime']

    wf = pe.Workflow(name='transformer_test')
    wf.base_dir = os.path.join(bids_dir, 'derivatives/test_transform')

    datasource = pe.Node(nio.DataGrabber(infields=['subject_id', 'run'],
                                         outfields=['func']), name='datasource')
    datasource.inputs.base_directory = os.path.join(bids_dir, 'derivatives/fmri_prep/derivatives/')
    datasource.inputs.template = '*'
    datasource.inputs.sort_filelist = True
    datasource.inputs.field_template = dict(func='sub-%s/func/sub-%s_task-' + task + '_run-%d_bold_preproc.nii.gz')
    datasource.inputs.template_args = dict(func=[['subject_id', 'subject_id', 'run']])
    datasource.inputs.run = runs
    datasource.inputs.subject_id = subjects

    event_getter = pe.Node(name='eventgetter', interface=Function(
                           input_names=['bids_dir', 'subject_id', 'run_id'],
                           output_names=["events"], function=get_events))

    event_getter.inputs.bids_dir = bids_dir
    event_getter.inputs.subject_id = subjects
    event_getter.inputs.run_id = runs

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

    ## Load contrasts and input
    # wf.connect(contrastgen, 'contrasts', modelfit, 'inputspec.contrasts')

    wf.connect(modelspec, 'session_info', modelfit, 'inputspec.session_info')
    wf.connect(datasource, 'func', modelfit, 'inputspec.functional_data')


    ### Start configuring from 

    # Datasink
    datasink = pe.Node(nio.DataSink(), name="datasink")
    datasink.inputs.base_directory = os.path.join(bids_dir, 'derivatives')
    datasink.inputs.container = 'test_transform'

    wf.connect(modelfit, 'outputspec.zfiles', datasink, 'zfiles')
    wf.connect(modelfit, 'outputspec.parameter_estimates', datasink, 'pes')

    wf.run()

""""
Usage: test_events.py
if __name__ == '__main__':


    subjects = '01'
    task = 'flanker'
    runs = [1, 2]
    bids_dir = '/vagrant/local/datasets/ds000102'
 
