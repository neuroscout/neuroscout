""""
Usage: fmri_bids_group [options] <bids_dir> <model> <n_copes>

-o <output>             Output folder.
                        Default: <bids_dir>/derivatives/<model>_group
"""
from docopt import docopt
import os

from nipype import Workflow, Node
from nipype import DataGrabber, DataSink
from nipype.interfaces.fsl import (L2Model, Merge, FLAMEO,
                                   SmoothEstimate, Cluster, ImageMaths)
import nipype.interfaces.fsl as fsl
from nipype.interfaces.fsl.maths import BinaryMaths
from nipype import config
config.enable_provenance()


def validate_arguments(args):
    """ Validate and preload command line arguments """
    bids_dir = args['<bids_dir>']
    model = args['<model>']
    num_copes = int(args['<n_copes>'])

    out_dir = args['-o']
    if out_dir is None:
        out_dir = os.path.join(bids_dir, 'derivatives/{}_group'.format(model))
    else:
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    return (bids_dir, model, num_copes, out_dir)


def group_onesample(bids_dir, model, num_copes,
                    out_dir, no_reversal=False):
    wk = Workflow(name='one_sample')
    wk.base_dir = os.path.abspath(
        os.path.join(bids_dir, 'derivatives/{}_group_wd'.format(model)))

    dg = Node(DataGrabber(infields=['cope_id'],
                          outfields=['copes', 'varcopes']),
                          name='grabber')

    dg.inputs.base_directory = os.path.abspath(os.path.join(bids_dir, 'derivatives/{}'.format(model)))
    dg.inputs.template = os.path.join(
        bids_dir, '%s/*/_flameo%s/%s1.nii.gz'.format(model))
    dg.inputs.template_args['copes'] = [['copes', 'cope_id', 'cope']]
    dg.inputs.template_args['varcopes'] = [['varcopes', 'cope_id', 'varcope']]
    dg.iterables = ('cope_id', range(0, num_copes))

    dg.inputs.sort_filelist = True

    model = Node(L2Model(), name='l2model')

    def num_copes(files):
        return len(files)
        
    mergecopes = Node(Merge(dimension='t'), name='merge_copes')
    wk.connect(dg, 'copes', mergecopes, 'in_files')
    wk.connect(dg, ('copes', num_copes), model, 'num_copes')

    mergevarcopes = Node(Merge(dimension='t'), name='merge_varcopes')
    wk.connect(dg, 'varcopes', mergevarcopes, 'in_files')

    mask_file = fsl.Info.standard_image('MNI152_T1_2mm_brain_mask.nii.gz')
    flame = Node(FLAMEO(), name='flameo')
    flame.inputs.mask_file = mask_file
    flame.inputs.run_mode = 'flame1'

    wk.connect(model, 'design_mat', flame, 'design_file')
    wk.connect(model, 'design_con', flame, 't_con_file')
    wk.connect(mergecopes, 'merged_file', flame, 'cope_file')
    wk.connect(mergevarcopes, 'merged_file', flame, 'var_cope_file')
    wk.connect(model, 'design_grp', flame, 'cov_split_file')

    smoothest = Node(SmoothEstimate(), name='smooth_estimate')
    wk.connect(flame, 'zstats', smoothest, 'zstat_file')
    smoothest.inputs.mask_file = mask_file

    cluster = Node(Cluster(), name='cluster')
    wk.connect(smoothest, 'dlh', cluster, 'dlh')
    wk.connect(smoothest, 'volume', cluster, 'volume')

    cluster.inputs.connectivity = 26
    cluster.inputs.threshold = 2.3
    cluster.inputs.pthreshold = 0.05
    cluster.inputs.out_threshold_file = True
    cluster.inputs.out_index_file = True
    cluster.inputs.out_localmax_txt_file = True

    wk.connect(flame, 'zstats', cluster, 'in_file')

    ztopval = Node(ImageMaths(op_string='-ztop', suffix='_pval'),
                   name='z2pval')
    wk.connect(flame, 'zstats', ztopval, 'in_file')

    sinker = Node(DataSink(), name='sinker')
    sinker.inputs.base_directory = os.path.abspath(out_dir)
    sinker.inputs.substitutions = [('_cope_id', 'contrast'),
                                   ('_maths__', '_reversed_')]

    wk.connect(flame, 'zstats', sinker, 'stats')
    wk.connect(cluster, 'threshold_file', sinker, 'stats.@thr')
    wk.connect(cluster, 'index_file', sinker, 'stats.@index')
    wk.connect(cluster, 'localmax_txt_file', sinker, 'stats.@localmax')

    if no_reversal is False:
        zstats_reverse = Node(BinaryMaths(), name='zstats_reverse')
        zstats_reverse.inputs.operation = 'mul'
        zstats_reverse.inputs.operand_value = -1
        wk.connect(flame, 'zstats', zstats_reverse, 'in_file')

        cluster2 = cluster.clone(name='cluster2')
        wk.connect(smoothest, 'dlh', cluster2, 'dlh')
        wk.connect(smoothest, 'volume', cluster2, 'volume')
        wk.connect(zstats_reverse, 'out_file', cluster2, 'in_file')

        ztopval2 = ztopval.clone(name='ztopval2')
        wk.connect(zstats_reverse, 'out_file', ztopval2, 'in_file')

        wk.connect(zstats_reverse, 'out_file', sinker, 'stats.@neg')
        wk.connect(cluster2, 'threshold_file', sinker, 'stats.@neg_thr')
        wk.connect(cluster2, 'index_file', sinker, 'stats.@neg_index')
        wk.connect(cluster2, 'localmax_txt_file', sinker, 'stats.@neg_localmax')

    wk.run()

if __name__ == '__main__':
    arguments = docopt(__doc__)
    group_onesample(*validate_arguments(arguments))
