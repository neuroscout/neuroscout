""""
Patch script to go from lower levels to fixed fx
"""

# Need to remove BIDS stuff
# Update inputspec
# Remove motion regressors / art detection
# Add func -> anat .mat transform as input

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

# from nipype import config
# cfg = dict(logging=dict(workflow_level='DEBUG'),
#            execution={'stop_on_first_crash': True})
# config.update_config(cfg)

subjects = ['102311', '104416', '105923', '146129', '146432', '150423', '155938', '203418', '209228', '573249']
out_dir = '/mnt/d/neuroscout/analyses/hcp/kdd_fx'
in_dir = '/tmp/first_level/modelfit'
runs = ['1', '2', '3', '4']
jobs = 5
conditions = ['street', 'outdoors', 'light', 'adult', 'sentiment',
              'long_freq', 'concreteness', 'word',
              '60_250',
              'maxfaceConfidence']


def create_contrasts(conditions):
    """ Creates basic contrasts.
    Expand this and stick into main script later """
    contrasts = []
    for i, con in enumerate(conditions):
        mat = [0] * len(conditions)
        mat[i] = 1
        c = [con, 'T', conditions, mat]
        contrasts.append(c)

    return contrasts


contrasts = create_contrasts(conditions)

"""
Set up workflow
"""
wf = Workflow(name='fixed_fx')
wf.base_dir = '/mnt/d/tmp/fixed_patch_kdd/'
"""
Subject iterator
"""
infosource = Node(IdentityInterface(fields=['subject_id']),
                  name="infosource")
infosource.iterables = ('subject_id', subjects)

"""
Grab data for each subject
"""
datasource = MapNode(DataGrabber(infields=['subject_id', 'run'],
                                 outfields=['copes', 'varcopes', 'dof']),
                     name='datasource', iterfield=['run'])
datasource.inputs.base_directory = in_dir
datasource.inputs.template = '*'
datasource.inputs.sort_filelist = True
datasource.inputs.field_template = dict(
    copes='_subject_id_%s/modelestimate/mapflow/_modelestimate%s/results/cope*.nii.gz',
    varcopes='_subject_id_%s/modelestimate/mapflow/_modelestimate%s/results/varcope*.nii.gz',
    dof='_subject_id_%s/modelestimate/mapflow/_modelestimate%s/results/dof')
datasource.inputs.template_args = dict(
    copes=[['subject_id', 'run']],
    varcopes=[['subject_id', 'run']],
    dof=[['subject_id', 'run']])
datasource.inputs.run = [int(r) - 1 for r in runs]

wf.connect([(infosource, datasource, [('subject_id', 'subject_id')])])


"""
Fixed effects workflow to combine runs
"""

fixed_fx = create_fixed_effects_flow()
fixed_fx.inputs.flameo.mask_file = '/mnt/d/neuroscout/datasets/hcp/MNI_3mm_brain_mask_thr.nii.gz'


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

wf.connect([(datasource, cope_sorter, [('copes', 'copes')]),
            (datasource, cope_sorter, [('varcopes', 'varcopes')]),
            (cope_sorter, fixed_fx, [('copes', 'inputspec.copes'),
                                     ('varcopes', 'inputspec.varcopes'),
                                     ('n_runs', 'l2model.num_copes')]),
            (datasource, fixed_fx, [('dof', 'inputspec.dof_files'),
                                    ])
            ])

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
datasink.inputs.base_directory = os.path.abspath(out_dir)

wf.connect(infosource, 'subject_id', datasink, 'container')
wf.connect(infosource, 'subject_id', subsgen, 'subject_id')
wf.connect(subsgen, 'substitutions', datasink, 'substitutions')
subsgen.inputs.conds = contrasts

# wf.connect([(modelfit.get_node('modelgen'), datasink,
#              [('design_cov', 'qa.model'),
#               ('design_image', 'qa.model.@matrix_image'),
#               ('design_file', 'qa.model.@matrix'),
#               ])])

wf.connect([(fixed_fx.get_node('outputspec'), datasink,
             [('res4d', 'res4d'),
              ('copes', 'copes'),
              ('varcopes', 'varcopes'),
              ('zstats', 'zstats'),
              ('tstats', 'tstats')])
            ])

wf.run(plugin='MultiProc', plugin_args={'n_procs': jobs})
