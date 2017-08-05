""""
Usage:
    fmri_bids_premodel run [options] <bids_dir> <task> <in_dir>
    fmri_bids_premodel make [options] <bids_dir> <task> [<in_dir>]

-f <fwhm>               Smoothing kernel [default: 5]
-s <subject_id>         Subjects to analyze. [default: all]
-r <run_ids>            Runs to analyze. [default: all]
-o <out_dir>            Output directory.
                        [default: <in_dir>/smooth_func]
-w <work_dir>           Working directory.
                        [default: /tmp]
-c                      Stop on first crash.
--method=<name>         Smoothing method: susan or isotropic.
                        [Default: susan]

--jobs=<n>              Number of parallel jobs [default: 1].
"""

from docopt import docopt

from nipype.pipeline.engine import Workflow, Node, MapNode
from nipype.interfaces.io import DataGrabber, DataSink
from nipype.interfaces import fsl

from nipype.interfaces.utility import Function, IdentityInterface
from nipype.workflows.fmri.fsl import create_susan_smooth

import os
from bids.grabbids import BIDSLayout


def premodel(bids_dir, task, subjects, runs, fwhm, in_dir=None, method='susan',
             out_dir=None, work_dir=None):
    """
    Experiment specific variables
    """
    wf = Workflow(name='premodel')
    if work_dir:
        wf.base_dir = work_dir

    """
    Subject iterator
    """
    infosource = Node(IdentityInterface(fields=['subject_id', 'fwhm']),
                      name="infosource")
    infosource.iterables = [('subject_id', subjects), ('fwhm', fwhm)]

    """
    Grab data for each subject
    """

    datasource = Node(DataGrabber(infields=['subject_id'],
                                  outfields=['func', 'mask']),
                      name='datasource')
    if in_dir is not None:
        datasource.inputs.base_directory = in_dir
    datasource.inputs.template = '*'
    datasource.inputs.sort_filelist = True
    datasource.inputs.field_template = dict(
        func='aligned/sub-%s/in_bold3Tp2/sub-%s_task-%s_%s_bold.nii.gz',
        mask='templatetransforms/sub-%s/bold3Tp2/brain_mask.nii.gz')
    datasource.inputs.template_args = dict(
        func=[['subject_id', 'subject_id', 'task', 'runs']],
        mask=[['subject_id']])
    datasource.inputs.runs = runs
    datasource.inputs.task = task
    wf.connect(infosource, 'subject_id', datasource, 'subject_id')

    """
    Mask the functional runs
    """

    maskfunc = MapNode(interface=fsl.ImageMaths(suffix='_bet',
                                                op_string='-mas'),
                       iterfield=['in_file'],
                       name='maskfunc')
    wf.connect(datasource, 'func', maskfunc, 'in_file')
    wf.connect(datasource, 'mask', maskfunc, 'in_file2')

    """
    Determine the 2nd and 98th percentile intensities of each functional run
    """

    getthresh = MapNode(interface=fsl.ImageStats(op_string='-p 2 -p 98'),
                        iterfield=['in_file'],
                        name='getthreshold')
    wf.connect(maskfunc, 'out_file', getthresh, 'in_file')

    """
    Threshold the first run of the functional data at 10% of the 98th percentile
    """

    threshold = MapNode(interface=fsl.ImageMaths(out_data_type='char',
                                                 suffix='_thresh'),
                        iterfield=['in_file', 'op_string'],
                        name='threshold')
    wf.connect(maskfunc, 'out_file', threshold, 'in_file')

    """
    Define a function to get 10% of the intensity
    """

    def getthreshop(thresh):
        return ['-thr %.10f -Tmin -bin' % (0.1 * val[1]) for val in thresh]
    wf.connect(getthresh, ('out_stat', getthreshop), threshold, 'op_string')

    """
    Determine the median value of the functional runs using the mask
    """

    medianval = MapNode(interface=fsl.ImageStats(op_string='-k %s -p 50'),
                        iterfield=['in_file', 'mask_file'],
                        name='medianval')
    wf.connect(datasource, 'func', medianval, 'in_file')
    wf.connect(threshold, 'out_file', medianval, 'mask_file')

    """
    Dilate the mask
    """

    dilatemask = MapNode(interface=fsl.ImageMaths(suffix='_dil',
                                                  op_string='-dilF'),
                         iterfield=['in_file'],
                         name='dilatemask')
    wf.connect(threshold, 'out_file', dilatemask, 'in_file')

    """
    Mask the input functional runs with the dilated mask
    """

    maskfunc2 = MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                 op_string='-mas'),
                        iterfield=['in_file', 'in_file2'],
                        name='maskfunc2')
    wf.connect(datasource, 'func', maskfunc2, 'in_file')
    wf.connect(dilatemask, 'out_file', maskfunc2, 'in_file2')

    """
    Smooth each run using SUSAN with the brightness threshold set to 75%
    of the median value for each run and a mask consituting the mean
    functional
    """
    to_int = lambda x: int(x)

    if method == 'susan':
        smooth = create_susan_smooth()
        wf.connect(infosource, ('fwhm', to_int), smooth, 'inputnode.fwhm')
        wf.connect(maskfunc2, 'out_file', smooth, 'inputnode.in_files')
        wf.connect(dilatemask, 'out_file', smooth, 'inputnode.mask_file')
    else:
        smooth = MapNode(interface=fsl.IsotropicSmooth(),
                         iterfield=['in_file'],
                         name='smooth')
        wf.connect(infosource, ('fwhm', to_int), smooth, 'fwhm')
        wf.connect(maskfunc2, 'out_file', smooth, 'in_file')

    """
    Mask the smoothed data with the dilated mask
    """

    maskfunc3 = MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                 op_string='-mas'),
                        iterfield=['in_file', 'in_file2'],
                        name='maskfunc3')
    if method == 'susan':
        wf.connect(smooth, 'outputnode.smoothed_files', maskfunc3, 'in_file')
    else:
        wf.connect(smooth, 'out_file', maskfunc3, 'in_file')

    wf.connect(dilatemask, 'out_file', maskfunc3, 'in_file2')

    """
    Save to datasink
    """
    def get_subs(subject_id):
        """ Generate substitutions """
        subs = [('_subject_id_%s' % subject_id, '')]

        return subs

    subsgen = Node(Function(input_names=['subject_id'],
                            output_names=['substitutions'],
                            function=get_subs),
                   name='subsgen')

    datasink = Node(DataSink(), name="datasink")
    datasink.inputs.regexp_substitutions = [('_maskfunc[0-9]*', ''),
                                            ('_fwhm_[0-9]*', ''),
                                            ('_mask_', '_'),
                                            ('_dilatemask[0-9]*', ''),
                                            ('bet_thresh_dil', 'dilmask')]
    if out_dir is not None:
        datasink.inputs.base_directory = os.path.abspath(out_dir)

    wf.connect(infosource, 'fwhm', datasink, 'container')
    wf.connect(infosource, 'subject_id', subsgen, 'subject_id')
    wf.connect(subsgen, 'substitutions', datasink, 'substitutions')
    wf.connect(dilatemask, 'out_file', datasink, 'dil_mask')
    wf.connect(maskfunc3, 'out_file', datasink, 'smooth_func')

    return wf


def validate_arguments(args):
    """ Validate and preload command line arguments """

    # Clean up names
    var_names = {'<bids_dir>': 'bids_dir',
                 '<in_dir>': 'in_dir',
                 '<task>': 'task',
                 '-o': 'out_dir',
                 '-f': 'fwhm',
                 '-w': 'work_dir',
                 '-s': 'subjects',
                 '-r': 'runs',
                 '--method': 'method'}

    if args['method'] not in ['susan', 'isotropic']:
        raise Exception("Invalid smoothing method specified.")

    if args.pop('-c'):
        from nipype import config
        cfg = dict(logging=dict(workflow_level='DEBUG'),
                   execution={'stop_on_first_crash': True})
        config.update_config(cfg)

    for old, new in var_names.iteritems():
        args[new] = args.pop(old)

    if args['out_dir'] == '<in_dir>/smooth_func':
        args['out_dir'] = os.path.join(args['in_dir'], 'smooth_func')
    for directory in ['out_dir', 'work_dir']:
        if args[directory] is not None:
            args[directory] = os.path.abspath(args[directory])
            if not os.path.exists(args[directory]):
                os.makedirs(args[directory])

    args['bids_dir'] = os.path.abspath(args['bids_dir'])
    args['in_dir'] = os.path.abspath(args['in_dir'])
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
            target=entity[:-1], return_type='id', task='movie')

        if args[entity] == 'all':
            args[entity] = all_ents
        else:
            args[entity] = args[entity].split(" ")
            for e in args[entity]:
                if e not in all_ents:
                    raise Exception("Invalid {} id {}.".format(entity[:-1], e))

    args['--jobs'] = int(args['--jobs'])
    args['fwhm'] = args['fwhm'].split(" ")
    return args


if __name__ == '__main__':
    arguments = validate_arguments(docopt(__doc__))
    jobs = arguments.pop('--jobs')
    run = arguments.pop('run')
    arguments.pop('make')
    wf = premodel(**arguments)

    if run:
        if jobs == 1:
            wf.run()
        else:
            wf.run(plugin='MultiProc', plugin_args={'n_procs': jobs})
