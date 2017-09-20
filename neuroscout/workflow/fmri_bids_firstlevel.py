""""
Usage:
    fmri_bids_first run [options] <bundle> <out_dir>
    fmri_bids_first make [options] <bundle> [<out_dir>]

-b <local_bids_dir>     Optional local copy of remote directory
-i <install_dir>        Path to install dataset with datalad
-w <work_dir>           Working directory.
-c                      Stop on first crash.
--jobs=<n>              Number of parallel jobs [default: 1].
--disable-datalad       Don't attempt to use datalad to fetch data
"""

from docopt import docopt
import json
import os
import tempfile
from base import create_first_level
from bids.grabbids import BIDSLayout
import pandas as pd


class FirstLevel(object):
    """ Validates arguments, and connect inputs to first level workflow"""
    def __init__(self, args):
        self.args = {}
        self.validate_arguments(args)
        self.create_workflow()

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
        if args.pop('-c'):
            from nipype import config
            cfg = dict(logging=dict(workflow_level='DEBUG'),
                       execution={'stop_on_first_crash': True})
            config.update_config(cfg)

        for directory in ['<out_dir>', '-w']:
            if args[directory] is not None:
                args[directory] = os.path.abspath(args[directory])
                if not os.path.exists(args[directory]):
                    os.makedirs(args[directory])

        self.args['work_dir'] = args['-w'] \
                                     if args['-w'] else tempfile.mkdtemp()
        self.args['out_dir'] = args['<out_dir>']

        self.jobs = int(args.pop('--jobs'))
        self.run = args.pop('run')
        args.pop('make')

        """ Process bundle arguments """
        bundle = args.pop('<bundle>')
        if not isinstance(bundle, dict):
            bundle = json.load(open(bundle, 'r'))
        self.args['subjects'] = list(pd.DataFrame(
            bundle['runs']).subject.unique())
        self.args['config'] = bundle['config']
        self.args['contrasts'] = bundle['contrasts']
        self.args['transformations'] = bundle['transformations']
        self.args['task'] = bundle['task_name']
        ## For now ignoring name and hash_id

        """ Clone bids_dir or use existing"""
        if args['-b']:
            bids_dir = args['-b']
        else:
            bids_dir = bundle['dataset_address']

        self.args['bids_dir'] = bids_dir

        ## Disable datalad to use full BIDS dataset
        if not args['--disable-datalad']:
            from datalad import api as dl
            from datalad.auto import AutomagicIO

            if not args['-i'] and args['-b']:
                bids_dir = dl.install(path=bids_dir).path
            else:
                if not args['-i']:
                    args['-i'] = self.args['work_dir']
                bids_dir = dl.install(source=bids_dir,
                                      path=args['-i']).path

            automagic = AutomagicIO()
            automagic.activate()

        project = BIDSLayout(bids_dir)

        """ Write out event files """
        pes = pd.DataFrame(bundle.pop('predictor_events')).rename(
            columns={'predictor_id' : 'trial_type'})

        out_path = os.path.join(self.args['work_dir'], 'events')
        if not os.path.exists(out_path):
            os.mkdir(out_path)

        for r in bundle['runs']:
            ## Write out event files for each run_id
            run_events = pes[pes.run_id==r['id']].drop('run_id', axis=1)
            ses = 'ses-{}_'.format(r['session']) if r['session'] else ''

            events_fname = os.path.join(out_path,
                                        'sub-{}_{}task-{}_run-{}_events.tsv'.format(
                r['subject'], ses, bundle['task_name'], r['number']))

            run_events.to_csv(events_fname, sep='\t', index=False)

            ## Check there are functional preprocessed files for each run_events
            if len(project.get(type='preproc', extensions='.nii.gz',
                               task=bundle['task_name'])) < 1:
                raise Exception("BIDS directory does not contain"
                                "preprocessed data for run {}".format(r['id']))

        self.args['runs'] = bundle['runs']

        """ Set TR """
        self.args['TR'] = json.load(open(
            os.path.join(bids_dir,
                         'task-{}_bold.json'.format(
                             bundle['task_name']))))['RepetitionTime']

    def create_workflow(self):
        """
        Import model specific files
        """
        self.wf = create_first_level(**self.args)


if __name__ == '__main__':
    args = docopt(__doc__)
    runner = FirstLevel(args)
    runner.execute()
