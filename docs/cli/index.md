# Neuroscout-cli

The Neuroscout Command Line Interface (_neuroscout-cli_) allows you to execute analyses created on [neuroscout.org](https://neuroscout.org).

_neuroscout-cli_ makes it easy to run your analysis with no configuration by fetching a self-contained analysis bundle, and downloading the required preprocessed fMRI data using [DataLad](https://www.datalad.org/). _neuroscout-cli_ internally uses [FitLins](https://github.com/poldracklab/fitlins), a python pipeline for fMRI analysis in BIDS, to fit a statistical model to the fMRI data, and produce comprehensive reports. _neuroscout-cli_ automatically uploads the resulting images to [Neurovault](https://www.neurovault.org/), and links them to the analysis listing, making it easy to view and share your results.

## Installation & Usage

The recommended way to install and use _neuroscout-cli_ is using containers (i.e. Docker or Singularity). Containers greatly facilitate the management of software dependencies, and increase reproducibility of results. 

You can also install _neuroscout-cli_ directly on your system using a manually prepared environment, although this typically requires more effort. 

A third method of running analyses is Google Colab, though larger analyses will take longer to run using the limited free resources.

### Containerized Execution

#### Docker

For most systems, we recommend using [Docker](https://www.docker.com/resources/what-container). First, follow the instructions for installing [Docker](https://docs.docker.com/engine/install/) on your system.

Next, follow our guide for running [Neuroscout on Docker](docker.md)

#### Singularity

[Singularity](https://sylabs.io/singularity/) containers are a great solution for High Performance Computing (HPC) environments, where _Docker_ cannot typically be used due to more tightly controlled [user privileges](https://researchcomputing.princeton.edu/support/knowledge-base/singularity).

First, check with your HPC administrator that _Singularity_ is available for use. If so, follow our guide for running [Neuroscout on Singularity](singulraity.md).

### Google Colab

A Google colab notebook is available [here](https://colab.research.google.com/github/neuroscout/neuroscout-cli/blob/master/examples/Neuroscout_Colab_Demo_NoMount.ipynb) where you can run a sample pre-generated analysis with an already provided id or provide your own analysis id. To run your own analysis, copy your id into the field in the cell labelled _1) Set Neuroscout Analysis ID_ and then run all of the cells. The provided id will run 10 subjects and 1 run from the Budapest dataset, and may take around 15 minutes. Larger analyses will take longer due to the limited free resources.

### Manually prepared environment

!!! Danger
    Manually installing _neuroscout-cli_ can be difficult due to complex dependencies. Proceed only if you really need to do this.

Use pip to install _neuroscout-cli_ directly from the GitHub repo:

    pip install git+https://www.github.com/neuroscout/neuroscout-cli