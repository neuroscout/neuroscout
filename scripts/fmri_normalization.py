import os
from nipype.pipeline.engine import Workflow, Node, MapNode
from nipype.interfaces.io import DataGrabber, DataSink
from nipype.interfaces import fsl
from bids.grabbids import BIDSLayout
from nipype.interfaces.utility import IdentityInterface

"""Create a FEAT preprocessing workflow
Parameters
----------
::
Inputs::
    inputspec.source_files : files (filename or list of filenames to register)
    inputspec.mean_image : reference image to use
    inputspec.anatomical_image : anatomical image to coregister to
Outputs::
    outputspec.anat2target_transform : FLIRT+FNIRT transform
    outputspec.transformed_files : transformed files in target space
    outputspec.transformed_mean : mean image in target space
Example
-------
"""
bids_dir = os.path.abspath('../../forrest')
task = 'objectcategories'

layout = BIDSLayout(bids_dir)
### custom parameters
subjects = layout.get_subjects(task=task)
target = fsl.Info.standard_image('MNI152_T1_2mm_brain.nii.gz')


register = Workflow(name='registration')
## Infosource
infosource = Node(IdentityInterface(fields=['subject_id']),
                 name="infosource")
infosource.iterables = ('subject_id', subjects)

## Datasource
inputnode = Node(DataGrabber(infields=['subject_id'],
                             outfields=['source_files', 'mean_image', 'anatomical_image', 'brain_mask']), name='datasource')
inputnode.inputs.base_directory = os.path.join(bids_dir, 'derivatives/')
inputnode.inputs.template = '*'
inputnode.inputs.sort_filelist = False
inputnode.inputs.field_template = dict(
    source_files='studyforrest-data-aligned/sub-%s/in_bold3Tp2/sub-%s_task-%s_%s_bold.nii.gz',
    mean_image='studyforrest-data-templatetransforms/sub-%s/bold3Tp2/brain.nii.gz',
    anatomical_image='studyforrest-data-templatetransforms/sub-%s/t1w/in_bold3Tp2/brain.nii.gz',
    brain_mask='studyforrest-data-templatetransforms/sub-%s/bold3Tp2/brain_mask.nii.gz')
inputnode.inputs.template_args = dict(source_files=[['subject_id', 'subject_id', 'task', 'runs']],
    mean_image=[['subject_id']], anatomical_image=[['subject_id']], brain_mask=[['subject_id']])
inputnode.inputs.task = task
inputnode.inputs.runs = layout.get_runs(task=task)

register.connect(infosource,'subject_id', inputnode, 'subject_id')

# """
# Estimate the tissue classes from the anatomical image.
# """

### Datasource here to read in brain anat files
# fast = pe.Node(fsl.FAST(), name='fast')
# register.connect(datasource, 'anat', fast, 'in_files')

# """
# Binarize the segmentation
# """

# binarize = pe.Node(fsl.ImageMaths(op_string='-nan -thr 0.5 -bin'),
#                    name='binarize')
# pickindex = lambda x, i: x[i]
# register.connect(fast, ('partial_volume_files', pickindex, 2),
#                  binarize, 'in_file')

# """
# Calculate rigid transform from mean image to anatomical image
# """

# mean2anat = pe.Node(fsl.FLIRT(), name='mean2anat')
# mean2anat.inputs.dof = 6
# register.connect(inputnode, 'mean_image', mean2anat, 'in_file')
# register.connect(stripper, 'out_file', mean2anat, 'reference')

# """
# Now use bbr cost function to improve the transform
# """

# mean2anatbbr = pe.Node(fsl.FLIRT(), name='mean2anatbbr')
# mean2anatbbr.inputs.dof = 6
# mean2anatbbr.inputs.cost = 'bbr'
# mean2anatbbr.inputs.schedule = os.path.join(os.getenv('FSLDIR'),
#                                             'etc/flirtsch/bbr.sch')
# register.connect(inputnode, 'mean_image', mean2anatbbr, 'in_file')
# register.connect(binarize, 'out_file', mean2anatbbr, 'wm_seg')
# register.connect(inputnode, 'anatomical_image', mean2anatbbr, 'reference')
# register.connect(mean2anat, 'out_matrix_file',
#                  mean2anatbbr, 'in_matrix_file')

"""
Calculate affine transform from anatomical to target
"""

anat2target_affine = Node(fsl.FLIRT(), name='anat2target_linear')
anat2target_affine.inputs.searchr_x = [-180, 180]
anat2target_affine.inputs.searchr_y = [-180, 180]
anat2target_affine.inputs.searchr_z = [-180, 180]
register.connect(inputnode, 'anatomical_image', anat2target_affine, 'in_file')
# register.connect(inputnode, 'target_image_brain',
#                  anat2target_affine, 'reference')
anat2target_affine.inputs.reference = target


"""
Calculate nonlinear transform from anatomical to target
"""

anat2target_nonlinear = Node(fsl.FNIRT(), name='anat2target_nonlinear')
anat2target_nonlinear.inputs.fieldcoeff_file = True
register.connect(anat2target_affine, 'out_matrix_file',
                 anat2target_nonlinear, 'affine_file')
register.connect(inputnode, 'anatomical_image',
                 anat2target_nonlinear, 'in_file')
# register.connect(inputnode, 'config_file',
#                  anat2target_nonlinear, 'config_file')
# register.connect(inputnode, 'target_image',
#                  anat2target_nonlinear, 'ref_file')
anat2target_nonlinear.inputs.ref_file = target

"""
Transform the mean image. To target
"""

warpmean = Node(fsl.ApplyWarp(interp='spline'), name='warpmean')
register.connect(inputnode, 'mean_image', warpmean, 'in_file')
# register.connect(mean2anatbbr, 'out_matrix_file', warpmean, 'premat')
# register.connect(inputnode, 'target_image', warpmean, 'ref_file')
warpmean.inputs.ref_file = target
register.connect(anat2target_nonlinear, 'fieldcoeff_file',
                 warpmean, 'field_file')

"""
Transform the remaining images. First to anatomical and then to target
"""

warpall = MapNode(fsl.ApplyWarp(interp='spline'),
                     iterfield=['in_file'],
                     nested=True,
                     name='warpall')
register.connect(inputnode, 'source_files', warpall, 'in_file')
# register.connect(mean2anatbbr, 'out_matrix_file', warpall, 'premat')
# register.connect(inputnode, 'target_image', warpall, 'ref_file')
warpall.inputs.ref_file = target
register.connect(anat2target_nonlinear, 'fieldcoeff_file',
                 warpall, 'field_file')

"""
Transform brain mask
"""
warpmask = MapNode(fsl.ApplyWarp(interp='spline'),
                     iterfield=['in_file'],
                     nested=True,
                     name='warpmask')
register.connect(inputnode, 'brain_mask', warpmask, 'in_file')
# register.connect(mean2anatbbr, 'out_matrix_file', warpall, 'premat')
# register.connect(inputnode, 'target_image', warpall, 'ref_file')
warpmask.inputs.ref_file = target
register.connect(anat2target_nonlinear, 'fieldcoeff_file',
                 warpmask, 'field_file')

binarize = Node(fsl.ImageMaths(op_string='-nan -thr 0.9 -bin'),
                   name='binarize')
unlist = lambda x: x[0]
register.connect(warpmask, ('out_file', unlist),
                 binarize, 'in_file')

"""
Assign all the output files to DataSink
"""


def get_subs(subject_id):
    """ Generate substitutions """
    subs = [('_subject_id_%s' % subject_id, '{}'.format(subject_id))]
    return subs

subsgen = Node(Function(input_names=['subject_id', 'conds'],
                        output_names=['substitutions'],
                        function=get_subs),
               name='subsgen')

### Datasink
outputnode = Node(DataSink(), name="datasink")
outputnode.inputs.base_directory = os.path.join(bids_dir, 'derivatives/registration')
register.connect(warpmean, 'out_file', outputnode, 'mean')
register.connect(warpall, 'out_file', outputnode, 'func')
register.connect(binarize, 'out_file', outputnode, 'mask')

# register.connect(mean2anatbbr, 'out_matrix_file',
#                  outputnode, 'func2anat_transform')
wf.connect(infosource, 'subject_id', subsgen, 'subject_id')
wf.connect(subsgen, 'substitutions', datasink, 'substitutions')
register.connect(anat2target_nonlinear, 'fieldcoeff_file',
                 outputnode, 'anat2target_transform')
register.run(plugin='MultiProc', plugin_args={'n_procs' : 5})
