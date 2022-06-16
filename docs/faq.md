# Frequently Asked Questions


### Is this service free to use?

Yes! Note, however, that Neuroscout is a web-based engine for fMRI analysis specification; at the moment,
we don't provide free computing resources for the execution of the resulting analysis bundles. Analyses can be run on Google Colab and a demo notebook is provided [here](https://colab.research.google.com/github/neuroscout/neuroscout-cli/blob/master/examples/Neuroscout_Colab_Demo_NoMount.ipynb).

### I plan to publish results I've obtained using Neuroscout, how do I cite?

After you generate an analysis, a "Bibliography" tab will be shown which will auto-generate a reference list for
the dataset, feature extractors, and scientific software used for that analysis. In addition to these references,
be sure to include the unique analysis ID associated with any results.

### Are there any restrictions on analyses I've created?

Yes. By using Neuroscout, you agree that once you have finalized and "compiled" an analysis, the analysis
can no longer be deleted from our system. If you wish to 'edit' an Analysis, you may clone the analysis,
and make any desired changed on the forked version. Although analyses are by default not searchable by
other users, any user with the private analysis ID may view your analysis.

Also, in the event that you publish any results generated using the NeuroScout interface, you MUST provide
a link to the corresponding analysis page(s) on the NeuroScout website.

### I have a naturalistic study I'd like to share on Neuroscout, how do I do so?

Due to the financial cost of extracting features from multi-modal stimuli using external APIs, the set of
datasets we support is manually curated. However, we are continually expanding the list of supported
datasets, and we encourage researchers to contact us if they want to make their data available for use in
Neuroscout. Note that it is much easier for us to ingest datasets that are already deposited in the
<a href="https://openneuro.org"> OpenNeuro</a> repository, and we we strongly recommend uploading your
dataset to <a href="https://openneuro.org"> OpenNeuro</a> whether or not it eventually ends up in
Neuroscout.

### I want to make changes to an analysis I already ran, but it is locked. How can I edit it?

Once an analysis has been run, it is permanently locked and archived for provenance. You may "clone" your
analysis, and make changes to this new copy of your analysis.

### I want to make one of my "private" analyses public, but the website says the analysis is "locked"!

When an analysis is locked, you can no longer make any substantive changes that affect model specification.
However, you can always edit the name, description, and public/private status. So go ahead and make your
analysis public!

### How do you automatically extract features from naturalistic datasets?

The original stimuli presented to users are submitted to various machine learning algorithms and services
to extract novel feature timecourses. To facility this process, we have developed a Python library for
multimodal feature extraction called pliers.
Pliers allows us to extract a wide-variety of features across modalities using various external content
analysis services with ease. For example, we are able to use Google Vision API to encode various
aspects of the visual elements of movie frames, such as when a face is present. In addition, pliers
allows us to easily link up various feature extraction services; for example, we can use the IBM Watson
Speech to Text API to transcribe the speech in a movie into words with precise onsets, and then use a
predefined dictionary of lexical norms to extract lexical norms for each word, such as frequency. We can
then generate timecourses for each of these extracted features, creating novel predictors of brain
activity.  For more information of pliers, please see the [GitHub repository](https://github.com/tyarkoni/pliers) and the following
paper:

> McNamara, Q., De La Vega, A., & Yarkoni, T. (2017, August). Developing a comprehensive framework for
> multimodal feature extraction. In Proceedings of the 23rd ACM SIGKDD International Conference on Knowledge
> Discovery and Data Mining (pp. 1567-1574). ACM.

### Am I restricted to mass univariate GLMs, or can I use Neuroscout to specify other kinds of analyses?

Currently, that is the case. However,the underlying BIDS-StatsModel is designed with more complex
models in mind, such as predictive and linear-mixed effect models


### Can I contribute my own predictors to Neuroscout?

Yes! Using the "My Predictors" function, you can create custom collections of predictors to add to your analyses.
Simply navigate to [My Predictors](https://neuroscout.org/mycollections), and click on "Add New Predictors".

Features should be in BIDS-compliant events format. Two columns are mandatory: "onset" and "duration" (both in seconds).
You can then include any number of novel predictors as additional columns. Missing values can be annotated using the value "n/a" (no quotes).

For each events file that you upload, you will be asked to associate it with runs in the respective dataset. Typically, there will be a different event file for each run in a naturalistic dataset.
You must then associate each file with subjects. For example, in most cases, all subjects will have seen the same stimulus, but this will vary across datasets.

After uploading, a new collection of predictors will be created. By default, predictors in this collection will be private, and only visible to you in the Analysis Builder.
If you wish to share these predictors with other Neuroscout users, please contact us, and we can make your predictors public.
