# What is Neuroscout?

_Neuroscout is an online platform for fast and flexible analysis of fMRI data._

fMRI studies using complex naturalistic stimulation, such as movies or audio narratives, hold great promise to reveal the neural activity underlying dynamic perception. However, this potential is limited by the resource-intensive nature of fMRI analysis, and exacerbated by the difficulty of encoding relevant events in rich, multi-modal stimuli.

Neuroscout leverages state-of-the-art _feature extraction_ tools to automatically extract hundreds of neural predictors from experimental stimuli. We pair this with an _easy-to-use [analysis builder](builder/index.md)_, enabling researchers to flexibly define novel statistical models.

Analysis execution is achieved with _no configuration_ using self-contained bundles tied to unique analysis IDs, and run-time data retrieval using [DataLad](https://www.datalad.org/). Containerized _model-fitting pipelines_ minimize software dependencies and ensure _high portability_ across execution environments.

Finally, we make it easy for researchers to _share their results_ with interactive publication-like reports and statistical image hosting with [NeuroVault](https://www.neurovault.org/).

If you're ready to build your own analysis, head over to [Getting Started](builder/index.md).

## Table of Contents

- Building analyses
    - [Getting started](builder/index.md)
    - [Predictors](builder/predictors.md)
    - [Transformations](builder/transformations.md)
    - [HRF Convolution](builder/hrf.md)
    - [Contrasts](builder/contrasts.md)
    - [Review](builder/review.md)
    - [Run / Status](builder/run.md)
    - [Bibliography](builder/bib.md)
- Browse analyses
    - [Browse & manage](browse/index.md)
    - [Clone](browse/clone.md)
- Running analyses:
    - [Introduction](cli/index.md)
    - [Usage](cli/usage.md)
- [FAQ](faq.md)



## Where can I get more help?

The first time you use neuroscout.org, you will be given a tour of the interface. After the tour, be on the look out informational tooltips ("i" icon), provided throughout to clarify aspects of the web interface. Finally, please read the [FAQ](faq.md) thoroughly!

For usage questions not addressed here, please ask a question on  [NeuroStars](https://neurostars.org). For bug reports, feature requests, feedback, etc.,
please open an issue on [open an issue on GitHub](https://github.com/neuroscout/neuroscout/issues).
