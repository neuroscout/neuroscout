def get_features(runs):
    """ Inject extracted features into event files """
    import pandas as pd
    from glob import glob
    from os import path

    file_path = '/mnt/c/Users/aid338/Documents/neuroscout_scripts/hcp_extract_results/'

    all_dfs = []
    for i, f in enumerate(glob(file_path + "text*")):
        df = pd.read_csv(f)
        df = df[['onset', 'PredefinedDictionaryExtractor', 'PredefinedDictionaryExtractor.1']].drop(0)
        df.columns = ['onset', 'long_frequency', 'concreteness']
        df['run'] = i
        all_dfs.append(df)
    all_dfs = pd.concat(all_dfs)

    def standardize(x):
        return (x - x.mean()) / x.std()

    all_dfs['long_frequency'] = standardize(all_dfs.long_frequency.astype('float'))
    all_dfs['concreteness'] = standardize(all_dfs.concreteness.astype('float'))
    all_dfs = all_dfs.fillna(0)
    all_dfs['mean'] = 1
    all_dfs['duration'] = 0.25

    new_event_files = []
    for run_id, df in all_dfs.groupby('run'):
        # Save to curr dir, but give abs path
        new_file = path.abspath('events_run{}'.format(run_id))
        new_event_files.append(new_file)
        df_out = df.drop('run', axis=1)
        df_out = pd.melt(df_out, id_vars=['onset', 'duration'],
                         value_name='amplitude', var_name='trial_type')
        df_out.to_csv(
            new_file, sep=str('\t'), index=False)

    return new_event_files

"""
Define conditions and contrasts
(this should be auto-generated or loaded from model json in the future)
"""

conditions = ['mean', 'long_frequency', 'concreteness']
contrasts = [
    ['mean', 'T', conditions, [1, 0, 0]],
    ['long_frequency', 'T', conditions, [0, 1, 0]],
    ['concreteness', 'T', conditions, [0, 0, 1]],
    ['freqvconcrete', 'T', conditions, [0, 1, -1]]
]
