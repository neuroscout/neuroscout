from random import choice
import pandas as pd
from bids.grabbids import BIDSLayout
from glob import glob

from featurex.stimuli.image import ImageStim 
from featurex.extractors.google import GoogleVisionAPILabelExtractor     

dataset_dir = '/Users/alejandro/datasets/forrest/phase2/'
categories = ['body', 'face', 'house', 'object', 'scene', 'scramble']

stimuli = {cat: [s.replace(dataset_dir + 'code/stimulus/', '').replace('img/', '')
           for s in glob(dataset_dir + 'code/stimulus/visualarea_localizer/img/' + cat + '*')]
           for cat in categories}

ext = GoogleVisionAPILabelExtractor(discovery_file='/Users/alejandro/bin/forrest-1c48f2c6a8c9.json')

all_labels = []
for cat in categories:
    for f in stimuli[cat]:
        stim_name = f.split('.')[0].split('/')[1]
        stim = ImageStim(dataset_dir+'stimuli/'+f) 

        res = ext.extract(stim)
        for i, feat in enumerate(res.features):
            value = res.data[0][i]
            all_labels.append([cat, stim_name, feat, value])

all_labels = pd.DataFrame(all_labels, columns=['category', 'stimulus', 'label', 'confidence'])

all_pivot = all_labels.pivot(index='stimulus', columns='label', values = 'confidence').fillna('0.49') 
all_dense = pd.melt(all_pivot.reset_index(), id_vars='stimulus')     
all_dense['category'] = all_dense.apply(lambda x: x.stimulus[0:-2], axis=1)  

all_dense['value'] = all_dense.value.astype('float32')     
mean_cat_labels = all_dense.groupby(['category', 'label']).mean().reset_index

top_10_bycat = mean_cat_labels.reset_index().sort_values(
    'value').groupby('category').tail(10).sort_values(['category', 'value'])