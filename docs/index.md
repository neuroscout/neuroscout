# What is Neuroscout?

_Neuroscout is a web-based platform for fast and flexible analysis of fMRI data._

## Motivation

fMRI studies using complex naturalistic stimulation, such as movies or audio narratives, hold great promise to reveal the neural activity underlying dynamic perception. However, this potential is limited by the resource-intensive nature of fMRI analysis, and exacerbated by the difficulty of encoding relevant events in rich, multi-modal stimuli.

Neuroscout leverages state-of-the-art _feature extraction_ tools to automatically extract hundreds of neural predictors from experimental stimuli. We pair this with an _easy-to-use analysis builder_, enabling researchers to flexibly define novel statistical models.

Analysis execution is achieved with _no configuration_ using self-contained bundles tied to unique analysis IDs, and run-time data retrieval using [DataLad](https://www.datalad.org/). Containerized _model-fitting pipelines_ minimize software dependencies and ensure _high portability_ across execution environments.

Finally, we make it easy for researchers to _share their results_ with interactive publication-like reports and statistical image hosting with [NeuroVault](https://www.neurovault.org/).

# Getting started

The [neuroscout.org](https://neuroscout.org) web interface has the following features:

 - Use the [analysis builder](builder/index.md) to create a custom fMRI analysis, drawing from hundreds of automatically extracted predictors.
 - Manage and clone existing analyses.
 - View uploaded results.
 - Upload custom predictors.

 Once you have generated an analysis, you can use the [neuroscout-cli](cli/index.md) to execute a model-fitting pipeline, and automatically upload your results.

## Sign Up

First things first, you need to register for an account.

Currently, there are two supported options, the choice is yours!

- Create an account using an email address and password (old fashioned way).
- Use Google single sign on.

If you create an account with us, you'll be asked to validate your email, as usual.


!!! Note
    Accounts are linked using email addresses. Signing up twice using the same email address, will result in a single account.


Once you've logged in, launch the [analysis builder](builder.md) using the `New Analysis` navigation button.

You can use the `Browse` button to view analyses you've created by selecting `My Analyses`, or publicly shared analyses under `Public analyses`.
Note that you don't need to log in to view public analyses.


## Where can I get more help?

The first time you use neuroscout.org, you will be given a tour of the interface. After the tour, be on the look out informational tooltips ("i" icon), provided throughout to clarify aspects of the web interface. Finally, please read the [FAQ](faq.md) thoroughly!

For usage questions not addressed here, please ask a question on  [NeuroStars](https://neurostars.org). For bug reports, feature requests, feedback, etc.,
please open an issue on [open an issue on GitHub](https://github.com/neuroscout/neuroscout/issues).
