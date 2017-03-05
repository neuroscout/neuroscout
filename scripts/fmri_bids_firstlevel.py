""""
Usage:
    fmri_bids_first run [options] <bids_dir> <model> <out_dir>
    fmri_bids_first make [options] <bids_dir> <model> [<out_dir>]

-t <transformations>    Transformation to apply to events.
-s <subject_id>         Subjects to analyze. [default: all]
-r <run_ids>            Runs to analyze. [default: all]
-w <work_dir>           Working directory.
-c                      Stop on first crash.
--jobs=<n>              Number of parallel jobs [default: 1].
"""

from docopt import docopt
from base import FirstLevel
from nipype.pipeline.engine import Node
from nipype.interfaces.utility import Function
from base import load_class
from bids.grabbids import BIDSLayout
import os

class FirstLevelBIDS(FirstLevel):
    def validate_arguments(self, args):
        super(FirstLevelBIDS, self).validate_arguments(args)

        ext = ['<bids_dir>', 'task']
        self.bids_args = {key : self.arguments.pop(key) for key in ext}

        """
        BIDS specific validation.
        """
        layout = BIDSLayout(self.bids_args['<bids_dir>'])

        # Check BOLD data
        if 'bold' not in layout.get_types():
            raise Exception("BIDS project does not contain"
                            " preprocessed BOLD data.")

        # Check that task exists
        if self.bids_args['task'] not in layout.get_tasks():
            raise Exception("Task not found in BIDS project")

        # Check subject ids and runs
        for entity in ['subjects', 'runs']:
            all_ents = layout.get(
                target=entity[:-1], return_type='id', task=self.bids_args['task']) ### Session??

            if self.arguments[entity] == 'all':
                self.arguments[entity] = all_ents
            else:
                for e in self.arguments[entity]:
                    if e not in all_ents:
                        raise Exception("Invalid {} id {}.".format(entity[:-1], e))

        self.arguments['in_dir'] = os.path.join(os.path.abspath(self.bids_args['<bids_dir>']), 'derivatives/fmriprep')

    def _add_connectons(self):
        """
        Add BIDS events and connect to workflow.
        """
        def _get_events(bids_dir, subject_id, runs, task):
            """ Get a single subjects event files """
            from bids.grabbids import BIDSLayout
            layout = BIDSLayout(bids_dir)
            event_files = [layout.get(
                type='events', return_type='file', subject=subject_id, run=r, task=task)[0] for r in runs]
            return event_files

        events_getter = Node(name='events_getter', interface=Function(
            input_names=['bids_dir', 'subject_id', 'runs', 'task'],
            output_names=['events'], function=_get_events))
        events_getter.inputs.runs = self.arguments['runs']
        events_getter.inputs.bids_dir = self.bids_args['<bids_dir>']
        events_getter.inputs.task = self.bids_args['task']

        self.wf.connect(self.wf.get_node('infosource'), 'subject_id', events_getter, 'subject_id')
        self.wf.connect(events_getter, 'events', self.wf.get_node('eventspec'), 'bids_events')

        """
        Add inputs to datasource
        """
        datasource = self.wf.get_node('datasource')
        datasource.inputs.field_template =  dict(
            func='sub-%s/func/sub-%s_task-%s_%s_bold_space-MNI152NLin2009cAsym_preproc.nii.gz',
            mask='sub-%s/func/sub-%s_task-%s_%s_bold_space-MNI152NLin2009cAsym_brainmask.nii.gz',)
        datasource.inputs.template_args = dict(
            func=[['subject_id', 'subject_id', 'task', 'runs']],
            mask=[['subject_id', 'subject_id', 'task', 'runs']])
        datasource.inputs.runs = self.arguments['runs']
        datasource.inputs.task = self.bids_args['task']
        self.wf.connect(datasource, 'mask', fixed_fx, 'inputs.flameo.mask_file')

if __name__ == '__main__':
    args = docopt(__doc__)
    Analysis = load_class(args.pop('<model>'))
    runner = Analysis(args)
    runner.execute()
