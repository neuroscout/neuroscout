# Neuroscout-cli

The Neuroscout Command Line Interface (_neuroscout-cli_) allows you to easily execute analyses created on [neuroscout.org](https://neuroscout.org).

_neuroscout-cli_ makes it easy to run your analysis with no configuration by fetching a self-contained analysis bundle, and downloading the required preprocessed fMRI data at run time using [DataLad](https://www.datalad.org/). _neuroscout-cli_ internally uses [FitLins](https://github.com/poldracklab/fitlins), a python pipeline for fMRI analysis in BIDS, to fits a statistical model to the fMRI data, and produce comprehensive reports. _neuroscout-cli_ automatically uploads the fitted images to [Neurovault](https://www.neurovault.org/), and links them to the analysis listing, making it easy to view and share your results.

## Installation

The recommended way to use the _neuroscout-cli_ is using a container to run Neuroscout. Containers greatly facilitate the management of software dependencies, and increase reproducibility of results. For workstations or PCs, we recommend using Docker. For HPCs, it's best to use a Singularity container

### Docker Container

In order to run _neuroscout-cli_ in a Docker Container, you must first install [Docker](https://docs.docker.com/engine/installation/).

Once Docker is is installed, pull down the latest _neuroscout-cli_ Docker image. This will be automatically done if you execute a `run` command.

    docker pull neuroscout/neuroscout-cli

### Singularity Container

In order to run _neuroscout-cli_ in High Performance Computing (HPC) environment, we recommend using Singularity, as Docker is not typically supported on HPCs.
First, check with your HPC administrator to ensure Singulraity is available, and for instructions on how to load it.

We host pre-build Singularity containers using Github Packages, which can be easily pulled like this:

    singularity pull oras://ghcr.io/neuroscout/neuroscout-cli:master


Note that typically you must be in on a compute node in order to execute singularity commands. 
For example, this could be done on TACC on an interactive node as follows:

    idev
    module load tacc_singularity
    singularity pull oras://ghcr.io/neuroscout/neuroscout-cli:master

In the current directory, you would now find an image file that can use to execute Neuroscout bundles.

### Manual installation

!!! Danger
    Manually installing _neuroscout-cli_ is not currently recommended. Proceed only if you really need to do this.

Use pip to install _neuroscout-cli_ directly from the github repo:

    pip install -e git+https://www.github.com/neuroscout/neuroscout-cli#egg=neuroscout_cli
