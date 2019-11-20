# What is Neuroscout?

Neuroscout is a web-based platform for fast and flexible analysis of fMRI data.

## Motivation

fMRI studies using complex naturalistic stimulation, such as movies or audio narratives, hold great promise to reveal the neural activity underlying dynamic real-world perception. However, this potential utility is constrained by the resource-intensive nature of fMRI analysis, and further exacerbated by the difficulty of encoding relevant events in rich, multi-modal stimuli.

Neuroscout leverages state-of-the-art feature extraction tools to automatically extract hundreds of neural predictors from experimental stimuli using a variety of algorithms and content-analysis services. We pair this with an easy-to-use model building interface, enabling researchers to flexibly define novel statistical models.

Analysis execution is achieved with no configuration using self-contained bundles tied to unique analysis IDs, and run-time data retrieval using [DataLad](https://www.datalad.org/). Containerized model-fitting pipelines minimize software dependencies and ensure high portability across wide variety execution environments, including HPCs and the cloud.

Finally, we make it easy for researchers to share their results with interactive publication-like reports and statistical image hosting with [NeuroVault](https://www.neurovault.org/).

## Where can I get more help?

In this documentation, we'll walk you through building and executing your own analysis on [neuroscout.org](https://neuroscout.org).
In addition, the first time you use neuroscout.org, you will be given a tour of the interface. After the tour, be on the look out informational tooltips ("i" icon), provided throughout to clarify aspects of the web interface. Finally, please read the [FAQ](faq.md) thoroughly!

For usage questions not addressed here, please ask a question on  [NeuroStars](https://neurostars.org). For bug reports, feature requests, feedback, etc.,
please open an issue on [open an issue on GitHub](https://github.com/neuroscout/neuroscout/issues).
