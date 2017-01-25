""""
Usage:
    fmri_bids_group run [options] <firstlv_dir> <output>
    fmri_bids_group make <firstlv_dir> [<output>]

-w <work_dir>           Working directory.
                        [default: None]
--jobs=<n>              Number of parallel jobs [default: 1].

"""
from docopt import docopt
import os

from nipype import Workflow, Node
from nipype import DataGrabber, DataSink
from nipype.interfaces.fsl import (L2Model, Merge, FLAMEO,
                                   SmoothEstimate, Cluster, ImageMaths)
import nipype.interfaces.fsl as fsl
from nipype.interfaces.fsl.maths import BinaryMaths
from glob import glob
import re


def group_onesample(firstlv_dir, work_dir=None,
                    out_dir=None, no_reversal=False):
    max_cope = sorted(glob(os.path.join(firstlv_dir, '*/copes/mni/*.nii.gz')))[-1].split('/')[-1]
    n_contrasts = int(re.findall('cope([0-9]*).*', max_cope)[0]) + 1

    wf = Workflow(name='group_onesample')
    if work_dir:
        wf.base_dir = work_dir

    dg = Node(DataGrabber(infields=['cope_id'],
                          outfields=['copes', 'varcopes']),
              name='grabber')

    dg.inputs.base_directory = firstlv_dir
    dg.inputs.template = '*/%s/mni/%s%s.nii.gz'
    dg.inputs.template_args['copes'] = [['copes', 'cope', 'cope_id']]
    dg.inputs.template_args['varcopes'] = [['varcopes', 'varcope', 'cope_id']]
    dg.iterables = ('cope_id', [str(n).zfill(2) for n in range(1, n_contrasts + 1)])

    dg.inputs.sort_filelist = True

    model = Node(L2Model(), name='l2model')

    def num_copes(files):
        return len(files)

    mergecopes = Node(Merge(dimension='t'), name='merge_copes')
    wf.connect(dg, 'copes', mergecopes, 'in_files')
    wf.connect(dg, ('copes', num_copes), model, 'num_copes')

    mergevarcopes = Node(Merge(dimension='t'), name='merge_varcopes')
    wf.connect(dg, 'varcopes', mergevarcopes, 'in_files')

    mask_file = fsl.Info.standard_image('MNI152_T1_2mm_brain_mask.nii.gz')
    flame = Node(FLAMEO(), name='flameo')
    flame.inputs.mask_file = mask_file
    flame.inputs.run_mode = 'flame1'

    wf.connect(model, 'design_mat', flame, 'design_file')
    wf.connect(model, 'design_con', flame, 't_con_file')
    wf.connect(mergecopes, 'merged_file', flame, 'cope_file')
    wf.connect(mergevarcopes, 'merged_file', flame, 'var_cope_file')
    wf.connect(model, 'design_grp', flame, 'cov_split_file')

    smoothest = Node(SmoothEstimate(), name='smooth_estimate')
    wf.connect(flame, 'zstats', smoothest, 'zstat_file')
    smoothest.inputs.mask_file = mask_file

    cluster = Node(Cluster(), name='cluster')
    wf.connect(smoothest, 'dlh', cluster, 'dlh')
    wf.connect(smoothest, 'volume', cluster, 'volume')

    cluster.inputs.connectivity = 26
    cluster.inputs.threshold = 2.3
    cluster.inputs.pthreshold = 0.05
    cluster.inputs.out_threshold_file = True
    cluster.inputs.out_index_file = True
    cluster.inputs.out_localmax_txt_file = True

    wf.connect(flame, 'zstats', cluster, 'in_file')

    ztopval = Node(ImageMaths(op_string='-ztop', suffix='_pval'),
                   name='z2pval')
    wf.connect(flame, 'zstats', ztopval, 'in_file')

    sinker = Node(DataSink(), name='sinker')
    if out_dir is not None:
        sinker.inputs.base_directory = os.path.abspath(out_dir)
    sinker.inputs.substitutions = [('_cope_id', 'contrast'),
                                   ('_maths__', '_reversed_')]

    wf.connect(flame, 'zstats', sinker, 'stats')
    wf.connect(cluster, 'threshold_file', sinker, 'stats.@thr')
    wf.connect(cluster, 'index_file', sinker, 'stats.@index')
    wf.connect(cluster, 'localmax_txt_file', sinker, 'stats.@localmax')

    if no_reversal is False:
        zstats_reverse = Node(BinaryMaths(), name='zstats_reverse')
        zstats_reverse.inputs.operation = 'mul'
        zstats_reverse.inputs.operand_value = -1
        wf.connect(flame, 'zstats', zstats_reverse, 'in_file')

        cluster2 = cluster.clone(name='cluster2')
        wf.connect(smoothest, 'dlh', cluster2, 'dlh')
        wf.connect(smoothest, 'volume', cluster2, 'volume')
        wf.connect(zstats_reverse, 'out_file', cluster2, 'in_file')

        ztopval2 = ztopval.clone(name='ztopval2')
        wf.connect(zstats_reverse, 'out_file', ztopval2, 'in_file')

        wf.connect(zstats_reverse, 'out_file', sinker, 'stats.@neg')
        wf.connect(cluster2, 'threshold_file', sinker, 'stats.@neg_thr')
        wf.connect(cluster2, 'index_file', sinker, 'stats.@neg_index')
        wf.connect(cluster2, 'localmax_txt_file', sinker, 'stats.@neg_localmax')

    return wf


def validate_arguments(args):
    """ Validate and preload command line arguments """

    # Clean up names
    var_names = {'<firstlv_dir>': 'firstlv_dir',
                 '<output>': 'out_dir',
                 '-w': 'work_dir'}

    for old, new in var_names.iteritems():
        args[new] = args.pop(old)

    for directory in ['out_dir', 'work_dir']:
        if args[directory] is not None:
            args[directory] = os.path.abspath(args[directory])
            if not os.path.exists(args[directory]):
                os.makedirs(args[directory])

    args['--jobs'] = int(args['--jobs'])

    return args


if __name__ == '__main__':
    arguments = validate_arguments(docopt(__doc__))
    jobs = arguments.pop('--jobs')
    run = arguments.pop('run')
    arguments.pop('make')
    wf = group_onesample(**arguments)

    if run:
        wf.run(plugin='MultiProc', plugin_args={'n_procs': jobs})
