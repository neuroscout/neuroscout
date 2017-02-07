def get_features(runs):
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


"""
Define conditions and contrasts
(this should be auto-generated or loaded from model json in the future)
"""

conditions = ['street', 'outdoors', 'light', 'adult']
contrasts = [['street', 'T', conditions, [1, 0, 0, 0]],
             ['outdoors', 'T', conditions, [0, 1, 0, 0]],
             ['light', 'T', conditions, [0, 0, 1, 0]],
             ['adult', 'T', conditions, [0, 0, 0, 1]],
             ['svo', 'T', conditions, [1, -1, 0, 0]],
             ['svl', 'T', conditions, [1, 0, -1, 0]],
             ['sva', 'T', conditions, [1, 0, 0, -1]],
             ['ovl', 'T', conditions, [0, 1, -1, 0]],
             ['ova', 'T', conditions, [0, 1, 0, -1]],
             ['lva', 'T', conditions, [0, 0, 1, -1]]
             ]
TR = 1

field_template = dict(
    func='downsample/2.5/downsampled_func/%s/tfMRI_MOVIE%s*[AP]_flirt.nii.gz')
