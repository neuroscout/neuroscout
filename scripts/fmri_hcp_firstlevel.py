""""
Usage:
    fmri_hcp_first run [options] <model> <in_dir> <out_dir>
    fmri_hcp_first make [options] <model> [<in_dir> <out_dir>]

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


class FirstLevelHCP(FirstLevel):
    def validate_arguments(self, args):
        super(FirstLevelHCP, self).validate_arguments(args)
        self.arguments['mask'] = '/mnt/d/neuroscout/datasets/hcp/MNI_3mm_brain_mask.nii.gz'

    def _add_custom(self):
        """
        Add pliers features and connect to workflow.
        """
        fx_getter = Node(name='fx_getter', interface=Function(
            input_names=['runs'],
            output_names=["transformed_events"], function=self._get_features))
        fx_getter.inputs.runs = self.arguments['runs']
        self.wf.connect(fx_getter, 'transformed_events', self.wf.get_node('eventspec'), 'bids_events')

        """
        Add inputs to datasource
        """
        datasource = self.wf.get_node('datasource')
        datasource.inputs.field_template = self.field_template
        datasource.inputs.template_args = self.template_args
        datasource.inputs.runs = self.arguments['runs']


if __name__ == '__main__':
    args = docopt(__doc__)
    Analysis = load_class(args.pop('<model>'))
    runner = Analysis(args)
    runner.execute()
