# Running Neuroscout-CLI on Docker

## Quickstart

!!! Note
    You must have Docker installed on your system

Assuming you've already created an analysis on neuroscout.org, you can run it in one line using the analysis_id (e.g.: `a54oo`):

    docker run -it -v /local/dir:/outdir neuroscout/neuroscout-cli run 5xH93 /outdir

where `/local/dir` is the local directory you want to save the results. 

This command will first download the _latest_ stable release of _neuroscout-cli_.

Next, _neuroscout-cli_ will download the corresponding preprocessed images, event files and model specification, and fit a multi-level GLM model.
The results will be automatically uploaded to NeuroVault, and the analysis page will link to this upload: https://neuroscout.org/builder/a54oo.

`-it --rm` simply tells Docker to run in _interactive_ mode and _remove_ the running container after execution.

See the following sections for how to customize this command to cache the downloaded data for future use, and save modeling outputs to disk. 

## Docker Images

For every release of _neuroscout-cli_, we publish a corresponding Docker image 

You can manually download a specific _neuroscout-cli_ release as follows:

    docker pull neuroscout/neuroscout-cli:<version>

where `<version>` is the version of neuroscout-cli that you want to download.
If you omit version, the _latest_ stable version will be downloaded.

You can see the tags available for download on [Docker Hub](https://hub.docker.com/repository/docker/neuroscout/neuroscout-cli).

You can also reference a `<version>` in the run command. For example:

    docker run -it --rm neuroscout/neuroscout-cli:version-0.5.1 run Mv3ev /out

!!! Note
    `master` is a special tag name which refers to the most recent _unstable_ commit to GitHub. 

## Saving outputs to disk

Containers are by default sandboxed so that they have access to a clean and separate environment.
To access files in the container, you must explicitly mount volumes from your system to the Docker container.

You can mount local directories to Docker containers using the `-v` argument, with the following syntax: `/local/host/path:/absolute/path/in/container`.

Here we mount the local `/home/user/out` directory to `/out` on the container.:


    docker run -it --rm -v /home/user/out:/out neuroscout/neuroscout-cli run 5xH93 /out 

!!! Note
    After the `run` command, we are telling _neuroscout-cli_ to save the outputs to the `/out` directory on `Docker`,
    which is mapped to `/home/user/out` on our local system.

### Output derivative structure
Neuroscout creates a unique output directory `neuroscout-{analysis_id}` for each analysis.
Given the `analysis_id`: `Mv3ev` and `dataset_name`: `Budapest`, this is a representative directory structure:


    /home/user/out/neuroscout-Mv3ev  
    └───sourcedata
    │   │
    │   └───Budapest
    │       └───fmriprep
    │   └───bundle
    │       └───events
    │       │   model.json
    │       │   ...
    └───fitlins
    │   └───sub-01
    │   └───reports
    │   │   task-movie_space-MNI152NLin2009cAsym_contrast-{name}_stat-effect_statmap.nii.gz
    |   |   ...

Note that by default Neuroscout will save the input preprocessed fMRI images in the output folder, to create a fully reproducible result package.

## Caching input datasets

If you plan to run more than one analysis per dataset, it's wise to download the input fMRI data to a directory available to multiple analyses.

To do so simply specify a data directory with `--download-dir`, and mount the corresponding local directory.

    docker run -it --rm -v /home/user/out:/out -v /home/user/data:/data neuroscout/neuroscout-cli --download-dir=/data run Mv3ev /out

The resulting cached data directory will look something like this, if you've run several analyses from different datasets:


    /home/user/data  
    └───Budapest
    │   └───fmriprep
    └───studyforrest
    │   └───fmriprep


The next time you run a model with a previously downloaded dataset, it will not need to re-download the fMRI data. </br>

!!! important
    Docker expects **absolute paths** for mounted directories


## Other command line arguments

_neuroscout-cli_ has many more command line arguments which can be specified at the end:

    docker run -it --rm neuroscout/neuroscout-cli run /out Mv3ev <args>

For example, if you wanted to specify the estimator to be `AFNI` instead of `nilearn`, and the number of CPU's to be `15`:

    docker run -it --rm neuroscout/neuroscout-cli run /out Mv3ev --n-cpus=15 --estimator=afni

For more details on these arguments, see this [reference](usage.md).

    


