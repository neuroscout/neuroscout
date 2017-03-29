import sys
sys.path.insert(0, "../")
from fmri_hcp_firstlevel import FirstLevelHCP


def _get_features(runs):
    """ Inject extracted features into event files """
    import pandas as pd
    from glob import glob
    from os import path

    features = sorted(glob(
        '/mnt/c/Users/aid338/Documents/neuroscout_scripts/hcp_extract_results/Cla*'))
    labels = ['street', 'outdoors', 'light', 'adult']

    new_event_files = []
    for run, f in enumerate(features):
        if str(run + 1) in runs:
            df = pd.read_csv(f).fillna(0)
            onsets = df['onset']

            # Set index to label name
            df.columns = df.iloc[0]
            df = df.convert_objects(convert_numeric=True)
            df = df[labels]
            df[df > 0] = 1  # Binaraize

            df['onset'] = onsets
            df['duration'] = 1
            df = df.drop([0, 1])

            df = pd.melt(df, id_vars=['onset', 'duration'],
                         value_name='amplitude', var_name='trial_type')

            # Save to curr dir, but give abs path
            new_file = path.abspath('events_run{}'.format(run))
            new_event_files.append(new_file)
            df.to_csv(new_file, sep=str('\t'), index=False)

    return new_event_files


class FourLabels(FirstLevelHCP):
    def validate_arguments(self, args):
        super(FourLabels, self).validate_arguments(args)
        self.field_template = dict(
            func='downsample/2.5/downsampled_func/%s/tfMRI_MOVIE%s*[AP]_flirt.nii.gz')
        self.template_args = dict(
            func=[['subject_id', 'runs']])
        conditions = ['street', 'outdoors', 'light', 'adult']
        self.arguments['conditions'] = conditions
        self.arguments['contrasts'] = [
            ['street', 'T', conditions, [1, 0, 0, 0]],
            ['outdoors', 'T', conditions, [0, 1, 0, 0]],
            ['light', 'T', conditions, [0, 0, 1, 0]],
            ['adult', 'T', conditions, [0, 0, 0, 1]],
            ['svo', 'T', conditions, [1, -1, 0, 0]],
            ['svl', 'T', conditions, [1, 0, -1, 0]],
            ['sva', 'T', conditions, [1, 0, 0, -1]],
            ['ovl', 'T', conditions, [0, 1, -1, 0]],
            ['ova', 'T', conditions, [0, 1, 0, -1]],
            ['lva', 'T', conditions, [0, 0, 1, -1]]]
        self.arguments['TR'] = 1
        self._get_features = _get_features
