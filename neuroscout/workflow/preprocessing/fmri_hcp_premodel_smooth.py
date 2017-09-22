""""
Usage:
    fmri_hcp_premodel run [options] <in_dir>
    fmri_hcp_premodel make [options] [<in_dir>]

-f <fwhm>               Smoothing kernel [default: 5]
-s <subject_id>         Subjects to analyze. [default: all]
-r <run_ids>            Runs to analyze. [default: all]
-o <out_dir>            Output directory.
                        [default: <in_dir>/smooth_func]
-w <work_dir>           Working directory.
                        [default: /tmp]
-d                      Debug mode.
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


def premodel(subjects, runs, fwhm, in_dir=None, method='susan',
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
                                  outfields=['func']),
                      name='datasource')
    if in_dir is not None:
        datasource.inputs.base_directory = in_dir
    datasource.inputs.template = '*'
    datasource.inputs.sort_filelist = True
    datasource.inputs.field_template = dict(
        func='downsample/2.5/downsampled_func/%s/tfMRI_MOVIE%s*[AP]_flirt.nii.gz')
    datasource.inputs.template_args = dict(
        func=[['subject_id', 'runs']])
    datasource.inputs.runs = runs
    wf.connect(infosource, 'subject_id', datasource, 'subject_id')

    # """
    # Extract the mean volume of the first functional run
    # """
    # def pickfirst(files):
    #     if isinstance(files, list):
    #         return files[0]
    #     else:
    #         return files
    #
    # meanfunc = Node(interface=fsl.ImageMaths(op_string='-Tmean',
    #                                          suffix='_mean'),
    #                 iterfield=['in_file'],
    #                 name='meanfunc')
    # wf.connect(datasource, ('func', pickfirst), meanfunc, 'in_file')
    #
    # """
    # Create mask
    # """
    # def mask_mean(mean_image):
    #     import nibabel as nib
    #     import os
    #     img = nib.load(mean_image)
    #     img.get_data()[:] = (img.get_data() != 0).astype('float')
    #
    #     nib.save(img, 'mean_mask.nii.gz')
    #
    #     return os.path.abspath('mean_mask.nii.gz')
    #
    # maskfunc = Node(Function(input_names=['mean_image'],
    #                          output_names=['mask'],
    #                          function=mask_mean),
    #                 name='maskfunc')
    # wf.connect(meanfunc, 'out_file', maskfunc, 'mean_image')
    #
    # """
    # Dilate the mask
    # """
    #
    # dilatemask = Node(interface=fsl.ImageMaths(suffix='_dil',
    #                                            op_string='-dilF'),
    #                   iterfield=['in_file'],
    #                   name='dilatemask')
    # wf.connect(maskfunc, 'mask', dilatemask, 'in_file')

    """
    Smooth each run using SUSAN with the brightness threshold set to 75%
    of the median value for each run and a mask consituting the mean
    functional
    """
    to_int = lambda x: int(x)

    # if method == 'susan':
    #     smooth = create_susan_smooth()
    #     wf.connect(infosource, ('fwhm', to_int), smooth, 'inputnode.fwhm')
    #     wf.connect(datasource, 'func', smooth, 'inputnode.in_files')
    #     wf.connect(dilatemask, 'out_file', smooth, 'inputnode.mask_file')
    # else:
    smooth = MapNode(interface=fsl.IsotropicSmooth(),
                     iterfield=['in_file'],
                     name='smooth')
    wf.connect(infosource, ('fwhm', to_int), smooth, 'fwhm')
    wf.connect(datasource, 'func', smooth, 'in_file')

    # """
    # Mask the smoothed data with the dilated mask
    # """
    #
    # maskfunc3 = MapNode(interface=fsl.ImageMaths(suffix='_mask',
    #                                              op_string='-mas'),
    #                     iterfield=['in_file'],
    #                     name='maskfunc3')
    # if method == 'susan':
    #     wf.connect(smooth, 'outputnode.smoothed_files', maskfunc3, 'in_file')
    # else:
    #     wf.connect(smooth, 'out_file', maskfunc3, 'in_file')
    #
    # wf.connect(dilatemask, 'out_file', maskfunc3, 'in_file2')

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
                                            ('_mask_', '_'),
                                            ('_dilatemask[0-9]*', ''),
                                            ('bet_thresh_dil', 'mask')]
    if out_dir is not None:
        datasink.inputs.base_directory = os.path.abspath(out_dir)

    wf.connect(infosource, 'subject_id', datasink, 'container')
    wf.connect(infosource, 'subject_id', subsgen, 'subject_id')
    wf.connect(subsgen, 'substitutions', datasink, 'substitutions')
    wf.connect(smooth, 'out_file', datasink, 'smooth_func')
    # wf.connect(maskfunc3, 'out_file', datasink, 'smooth_func')

    return wf


def validate_arguments(args):
    """ Validate and preload command line arguments """

    # Clean up names
    var_names = {'<in_dir>': 'in_dir',
                 '-o': 'out_dir',
                 '-f': 'fwhm',
                 '-w': 'work_dir',
                 '-s': 'subjects',
                 '-r': 'runs',
                 '--method': 'method'}

    for old, new in var_names.iteritems():
        args[new] = args.pop(old)

    if args['method'] not in ['susan', 'isotropic']:
        raise Exception("Invalid smoothing method specified.")

    if args.pop('-d'):
        from nipype import config
        config.enable_debug_mode()

    if args['out_dir'] == '<in_dir>/smooth_func':
        args['out_dir'] = os.path.join(args['in_dir'], 'smooth_func')
    for directory in ['out_dir', 'work_dir']:
        if args[directory] is not None:
            args[directory] = os.path.abspath(args[directory])
            if not os.path.exists(args[directory]):
                os.makedirs(args[directory])

    args['in_dir'] = os.path.abspath(args['in_dir'])

    # Check subject ids and runs
    for entity in ['subjects', 'runs']:
        args[entity] = args[entity].split(" ")

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
