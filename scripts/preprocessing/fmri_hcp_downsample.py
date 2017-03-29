from nipype.pipeline.engine import Workflow, Node, MapNode
from nipype.interfaces.io import DataGrabber, DataSink
from nipype.interfaces import fsl
from nipype.interfaces.utility import Function, IdentityInterface

subjects = ['100610', '102311', '104416', '105923', '111312',
            '111514', '114823', '125525', '131722', '128935', '137128', '140117', '144226',
            '146129', '146432', '150423', '155938', '156334', '157336', '158035',
            '158136', '162935', '164131', '171633', '176542', '177746', '178142',
            '115017', '18225', '181232', '181636', '182436', '182739', '185442',
            '187345', '191841', '196144', '197348', '198653', '200210', '200311',
            '201515', '203418', '209228', '212419', '214019', '221319', '249947',
            '283543', '318637', '352738', '365343', '380036', '381038', '389357', '395756',
            '397760', '467351', '541943', '547046', '573249', '627549',
            '638049', '680957', '690152', '732243', '770352', '783462',
            '898176', '901139', '951457', '958976']

"""
Downsample
"""

data_dir = '/mnt/d/neuroscout/datasets/hcp/'
# subjects = ['100610']
out_dir = '/mnt/d/neuroscout/analyses/hcp/downsample/'
n_jobs = 5
res = 3

register = Workflow(name='registration')

"""
Infosource
"""

infosource = Node(IdentityInterface(fields=['subject_id']), name="infosource")
infosource.iterables = ('subject_id', subjects)

"""
Datasource
"""
inputnode = Node(DataGrabber(infields=['subject_id'],
                             outfields=['source_files']),
                 name='datasource')
inputnode.inputs.base_directory = data_dir
inputnode.inputs.template = '*'
inputnode.inputs.sort_filelist = False
inputnode.inputs.field_template = dict(
    source_files='movie_func_preproc/%s/MNINonLinear/Results/*/*_[AP][AP].nii.gz')
inputnode.inputs.template_args = dict(source_files=[['subject_id']])
register.connect(infosource, 'subject_id', inputnode, 'subject_id')

"""
Downsample
"""
downsample = MapNode(fsl.FLIRT(), name='downsample', iterfield=['in_file', 'reference'])
downsample.inputs.apply_isoxfm = res
register.connect(inputnode, 'source_files', downsample, 'in_file')
register.connect(inputnode, 'source_files', downsample, 'reference')

"""
Save to datasink
"""


def get_subs(subject_id):
    """ Generate substitutions """
    subs = [('_subject_id_%s' % subject_id, '{}'.format(subject_id))]
    return subs


subsgen = Node(Function(input_names=['subject_id'],
                        output_names=['substitutions'],
                        function=get_subs),
               name='subsgen')
register.connect(infosource, 'subject_id', subsgen, 'subject_id')

outputnode = Node(DataSink(), name="datasink")
outputnode.inputs.base_directory = out_dir
outputnode.inputs.regexp_substitutions = [('_downsample[0-9]*', '')]
outputnode.inputs.container = str(res)
register.connect(subsgen, 'substitutions', outputnode, 'substitutions')

register.connect(downsample, 'out_file',
                 outputnode, 'downsampled_func')

# register.run()
register.run(plugin='MultiProc', plugin_args={'n_procs': n_jobs})
