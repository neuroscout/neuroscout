import sys
sys.path.insert(0, "../")
from fmri_hcp_firstlevel import FirstLevelHCP

def _get_features(runs):
    """ Inject extracted features into event files """
    import pandas as pd
    from glob import glob
    from os import path
    import numpy as np

    file_path = '/mnt/c/Users/aid338/Documents/neuroscout_scripts/hcp_extract_results/'
    final_dfs = []

    """ First get labels """
    labels = ['street', 'outdoors', 'light', 'adult']
    all_dfs = []
    for run_id, f in enumerate(sorted(glob(file_path + 'Cla*'))):
        if str(run_id + 1) in runs:
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
            all_dfs.append(df)
    final_dfs.append(all_dfs)

    """ Next get sentiment"""
    all_dfs = []
    lengths = [(1, 921), (2, 918), (3, 915), (4, 901)]
    for run_id, length in lengths:
        dfs = []
        if str(run_id) in runs:
            for f in sorted(glob(file_path + 'Sent*MOVIE{}*'.format(run_id))):
                df = pd.read_csv(f)[['onset', 'IndicoAPIExtractor', 'IndicoAPIExtractor.1']]
                df = df.reindex(df.index.drop([0, 1]))
                df.columns = ['onset', 'duration', 'sentiment']
                dfs.append(df)
            dfs[1].onset = dfs[1].onset + length / 2  # Set onset of 2nd half
            dfs = pd.concat(dfs).reset_index().drop('index', axis=1)
            dfs = dfs.convert_objects(convert_numeric=True)
            dfs = pd.melt(dfs, id_vars=['onset', 'duration'],
                          value_name='amplitude', var_name='trial_type')
            all_dfs.append(dfs)
    final_dfs.append(all_dfs)

    """ Word frequency """
    all_dfs = []
    for run_id, f in enumerate(sorted(glob(file_path + "text*"))):
        if str(run_id + 1) in runs:
            df = pd.read_csv(f)
            df = df[['onset', 'PredefinedDictionaryExtractor', 'PredefinedDictionaryExtractor.1']].drop(0)
            df = df.fillna(0)
            df.columns = ['onset', 'long_freq', 'concreteness']
            df['word'] = 1
            df['duration'] = 0.25
            df = pd.melt(df, id_vars=['onset', 'duration'],
                         value_name='amplitude', var_name='trial_type')
            all_dfs.append(df)
    final_dfs.append(all_dfs)

    """ Auditory frequency """
    all_dfs = []
    for run_id, f in enumerate(sorted(glob(file_path + "freq*"))):
        if str(run_id + 1) in runs:
            df = pd.read_csv(f)[['onset', 'duration', '60_250']]
            df = pd.melt(df, id_vars=['onset', 'duration'],
                         value_name='amplitude', var_name='trial_type')
            df['amplitude'] = df.amplitude.astype('float').round(100).replace([np.inf, -np.inf], 0)
            all_dfs.append(df)
    final_dfs.append(all_dfs)

    """ Google Vision Faces """
    def setmaxConfidence(row):
        maxcol = row['maxFace']
        if pd.notnull(maxcol):
            val = row[maxcol]
        else:
            val = 0
        return val

    all_dfs = []
    for run_id, f in enumerate(sorted(glob(file_path + "clip*googleface*"))):
        if str(run_id + 1) in runs:
            df = pd.read_csv(f)

            # Calculate computed values
            confidence_cols = [c for c in df.columns if c.endswith(
                'face_detectionConfidence')]
            df['maxFace'] = df.apply(lambda x: x[confidence_cols].idxmax(), axis=1)
            df['maxfaceConfidence'] = df.apply(setmaxConfidence, axis=1)

            # Select only relevant columns
            df = df[['onset', 'duration', 'maxfaceConfidence']]
            df = pd.melt(df, id_vars=['onset', 'duration'],
                         value_name='amplitude', var_name='trial_type')
            all_dfs.append(df)
    final_dfs.append(all_dfs)

    """ Concat all features, standardize, and save"""
    new_filenames = []
    dfs_by_run = [pd.concat(dfs) for dfs in zip(*final_dfs)]

    for i, df in enumerate(dfs_by_run):
        df['run'] = i

    all_dfs = pd.concat(dfs_by_run)

    def standardize(x):
        return (x - x.mean()) / x.std()

    all_dfs.loc[all_dfs.trial_type == 'long_freq', 'amplitude'] = standardize(all_dfs[all_dfs.trial_type == 'long_freq'].amplitude.astype('float'))
    all_dfs.loc[all_dfs.trial_type == 'concreteness', 'amplitude'] = standardize(all_dfs[all_dfs.trial_type == 'concreteness'].amplitude.astype('float'))
    all_dfs.loc[all_dfs.trial_type == 'sentiment', 'amplitude'] = standardize(all_dfs[all_dfs.trial_type == 'sentiment'].amplitude.astype('float'))

    for run_id, df in all_dfs.groupby('run'):
        new_file = path.abspath('events_run{}.tsv'.format(run_id))
        new_filenames.append(new_file)
        df.drop('run', axis=1).to_csv(new_file, sep=str('\t'), index=False)

    return new_filenames


class AllFeatures(FirstLevelHCP):
    def validate_arguments(self, args):
        super().validate_arguments(args)
        self.field_template = dict(
            func='downsample/3/downsampled_func/%s/tfMRI_MOVIE%s*[AP]_flirt.nii.gz')
        self.template_args = dict(
            func=[['subject_id', 'runs']])

        conditions = ['street', 'outdoors', 'light', 'adult', 'sentiment',
                      'long_freq', 'concreteness', 'word',
                      '60_250',
                      'maxfaceConfidence']

        self.arguments['conditions'] = conditions
        self.arguments['contrasts'] = create_contrasts(conditions)
        self.arguments['TR'] = 1
        self._get_features = _get_features
