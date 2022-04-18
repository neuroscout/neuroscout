# What is Neuroscout?

_Neuroscout is an end-to-end platform for analysis of *naturalistic* fMRI data designed to facilitate the adoption of *robust and generalizable research practices*._

![fig2a](https://user-images.githubusercontent.com/2774448/163874691-c44ebc96-dd3f-4642-bf5a-0d1abd4ddbad.png)

Neuroscout leverages state-of-the-art machine learning models to *automatically annotate naturalistic stimuli* in [dozens of naturalistic fMRI datasets](https://neuroscout.org/datasets), resulting in [hundreds of potential neural predictors](https://neuroscout.org/predictors). 

We pair this with an _easy-to-use [analysis builder](builder/index.md)_, enabling researchers to flexibly define novel statistical models.

![fig2b](https://user-images.githubusercontent.com/2774448/163874701-e2e6a18e-f9e6-451b-9014-ec2a2e3664e3.png)

[Analysis execution](cli/index.md) is achieved with _no configuration_ using self-contained bundles tied to unique analysis IDs, and run-time data retrieval using [DataLad](https://www.datalad.org/). Containerized _model-fitting pipelines_ minimize software dependencies and ensure _high portability_ across execution environments.

Finally, we make it easy for researchers to _share their results_ with interactive reports and automatic upload of statistical images to [NeuroVault](https://www.neurovault.org/).


## Where can I get more help?
In the analysis builder, be on the look out informational tooltips ("i" icon), provided throughout to clarify aspects of the web interface. Also, please read the [FAQ](faq.md) if you have questions.

For additional help, please ask questions on  [NeuroStars](https://neurostars.org/tag/neuroscout). For bug reports and feature requests 
please open an issue on [open an issue on GitHub](https://github.com/neuroscout/neuroscout/issues).

### Reference
*Neuroscout, a unified platform for generalizable and reproducible fMRI research.*

Alejandro de la Vega, Roberta Rocca, Ross W. Blair, Christopher J. Markiewicz, Jeff Mentch, James D. Kent, Peer Herholz, Satrajit S. Ghosh, Russell A. Poldrack, Tal Yarkoni.
bioRxiv 2022.04.05.487222; doi: https://doi.org/10.1101/2022.04.05.487222 
