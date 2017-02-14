from nipype.pipeline.engine import Workflow, Node
import nipype.algorithms.modelgen as model
import nipype.algorithms.events as events
from nipype.interfaces.io import DataGrabber, DataSink

from nipype.interfaces.utility import Function, IdentityInterface
from nipype.workflows.fmri.fsl import (create_modelfit_workflow,
                                       create_fixed_effects_flow)

import os
import json
import abc
import importlib


def load_class(full_class_string):
    """
    dynamically load a class from a string
    """

    class_data = full_class_string.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]

    module = importlib.import_module(module_path)
    # Finally, we retrieve the Class
    return getattr(module, class_str)


def create_first_level(in_dir, subjects, runs, conditions, contrasts, mask,
                       out_dir=None, work_dir=None, transformations=None, TR=1):
    """
    Set up workflow
    """
    wf = Workflow(name='first_level')
    if work_dir:
        wf.base_dir = work_dir

    """
    Subject iterator
    """
    infosource = Node(IdentityInterface(fields=['subject_id']),
                      name="infosource")
    infosource.iterables = ('subject_id', subjects)

    """
    Grab data for each subject
    """

    datasource = Node(DataGrabber(infields=['subject_id'],
                                  outfields=['func']),
                      name='datasource')
    datasource.inputs.base_directory = in_dir
    datasource.inputs.template = '*'
    datasource.inputs.sort_filelist = True

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
                (datasource, modelspec, [('func', 'functional_runs')]),
                (eventspec, modelspec, [('subject_info', 'subject_info')])])

    """
    Fit model to each run
    """

    modelfit = create_modelfit_workflow()

    modelfit.inputs.inputspec.contrasts = contrasts
    modelfit.inputs.inputspec.interscan_interval = TR
    modelfit.inputs.inputspec.model_serial_correlations = True
    modelfit.inputs.inputspec.bases = {'gamma': {'derivs': True}}

    wf.connect(modelspec, 'session_info', modelfit, 'inputspec.session_info')
    wf.connect(datasource, 'func', modelfit, 'inputspec.functional_data')

    """
    Fixed effects workflow to combine runs
    """

    fixed_fx = create_fixed_effects_flow()
    fixed_fx.inputs.flameo.mask_file = mask

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
    return wf


class FirstLevel(object):
    """ Validates arguments, and connect inputs to first level workflow"""
    __metaclass__ = abc.ABCMeta

    def __init__(self, args):
        self.validate_arguments(args)
        self.create_workflow()
        self._add_custom()

    def execute(self):
        if self.run:
            if self.jobs == 1:
                self.wf.run()
            else:
                self.wf.run(plugin='MultiProc', plugin_args={'n_procs': self.jobs})
        else:
            return self.wf

    def validate_arguments(self, args):
        """ Validate and preload command line arguments """

        # Clean up names
        var_names = {'<out_dir>': 'out_dir',
                     '<in_dir>': 'in_dir',
                     '-w': 'work_dir',
                     '-s': 'subjects',
                     '-r': 'runs',
                     '-t': 'transformations'}

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

        # Check subject ids and runs
        for entity in ['subjects', 'runs']:
            args[entity] = args[entity].split(" ")

        if args['transformations'] is not None:
            args['transformations'] = os.path.abspath(args['transformations'])
            try:
                json.load(open(args['transformations'], 'r'))
            except ValueError:
                raise Exception("Invalid transformation JSON file")
            except IOError:
                raise Exception("Transformation file not found")

        self.jobs = int(args.pop('--jobs'))
        self.run = args.pop('run')
        args.pop('make')

        self.arguments = args

    def create_workflow(self):
        """
        Import model specific files
        """
        self.wf = create_first_level(**self.arguments)

    @abc.abstractmethod
    def _add_custom(self):
        """ Add custom connections to the workflow after having loaded it
        Datasource templates *must* be updated """
