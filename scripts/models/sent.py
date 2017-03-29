def get_features(runs):
    """ Inject extracted features into event files """
    import pandas as pd
    from glob import glob
    from os import path

    file_path = '/mnt/c/Users/aid338/Documents/neuroscout_scripts/hcp_extract_results/'
    cols = ['onset', 'IndicoAPIExtractor', 'IndicoAPIExtractor.1']
    lengths = [(1, 921), (2, 918), (3, 915), (4, 901)]

    new_event_files = []
    for run_id, length in lengths:
        dfs = []
        for f in sorted(glob(
                file_path + 'Sent*MOVIE{}*'.format(run_id))):
            df = pd.read_csv(f, index_col=False)[cols]
            df = df.reindex(df.index.drop(1).drop(0))
            df.columns = ['onset', 'duration', 'sentiment']
            dfs.append(df)
        dfs[1].onset = dfs[1].onset + length / 2
        dfs = pd.concat(dfs).reset_index().drop('index', axis=1)
        dfs = dfs.convert_objects(convert_numeric=True)
        dfs = pd.melt(dfs, id_vars=['onset', 'duration'],
                      value_name='amplitude', var_name='trial_type')

        # Save to curr dir, but give abs path
        new_file = path.abspath('events_run{}'.format(run_id))
        new_event_files.append(new_file)
        dfs.to_csv(new_file, sep=str('\t'), index=False)

    return new_event_files


conditions = ['sentiment']
contrasts = [['sentiment', 'T', conditions, [1]]]
