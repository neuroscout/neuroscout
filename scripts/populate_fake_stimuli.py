from random import choice
import pandas as pd
from bids.grabbids import BIDSLayout
from glob import glob

dataset_dir = '/Users/alejandro/datasets/forrest/phase2/'
categories = ['body', 'face', 'house', 'object', 'scene', 'scramble']

stimuli = {cat: [s.replace(dataset_dir + 'code/stimulus/', '')
           for s in glob(dataset_dir + 'code/stimulus/visualarea_localizer/img/' + cat + '*')]
           for cat in categories}

layout = BIDSLayout(dataset_dir)

for subject in layout.get_subjects():
    for f in layout.get(
            type='events', return_type='file', subject=subject, session='localizer'):

        try:
            events = pd.read_table(f)
            events['stim_file'] = events.apply(
               lambda x: choice(stimuli[x['trial_type']]), axis=1)
            events.to_csv(f, sep='\t')
        except IOError:
            print(f)
