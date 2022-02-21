# Running Neuroscout-CLI on Singularity (High Performance Clusters)

!!! Note
    Singularity must be available on your HPC. Contact your administrator.
    This guide is for Singularity >= 2.5.

!!! important
    HPCs typically require jobs to be submitted using a scheduled such as SLURM. 
    This will not be covered in this guide, and will assume commands are run on compute nodes (via interactive sessions or submitted scripts)


## Preparing Singularity Images.

Unlike _Docker_, you must explicitly download or compile Singularity images to a file prior to execution.

For every release of _neuroscout-cli_, we publish Singularity images to GitHub Packages which mirror the images published on Docker Hub. 

You can download the latest pre-compiled image as follows:

    singularity pull oras://ghcr.io/neuroscout/neuroscout-cli:<version>

where `<version>` is the version of neuroscout-cli that you want to download.
You must specify a version.

You can see the tags available for download on [GitHub Packages](https://github.com/neuroscout/neuroscout-cli/pkgs/container/neuroscout-cli).


!!! note
`master` is a special tag name which refers to the most recent _unstable_ commit to GitHub. 
`latest` refers to the latest _stable_ release.


## Executing Singularity image

Assuming you've already created an analysis on [neuroscout.org](https://neuroscout.org), and have its analysis id (e.g.: `Mv3ev`), you can run it in one line:

    singularity run --cleanenv neuroscout-cli-<version>.simg Mv3ev <outdir>

Where `<outdir>` is a directory you can save files to.

This command will download the corresponding preprocessed images, event files and model specification, and fit a multi-level GLM model.
The results will be automatically uploaded to NeuroVault, and the analysis page will link to this upload: https://neuroscout.org/builder/Mv3ev.

!!! important
    `neuroscout-cli-<version>.simg` refers to a specific downloaded image on your system. 


## Saving data to disk

`Singularity` typically automatically mounts host volumes to the container. This may differ between systems, so see the documentation for your HPC for more details.

Thus, you can simplify modify `<outdir>` to a directory of your choice: 

     singularity run --cleanenv neuroscout-cli-<version>.simg run /work/dir/out Mv3ev

[See here](docker.md#output-derivative-structure) for more details on the output directory structure. 

## Caching input datasets

If you wish to save the input preprocessed datasets elsewhere, simply specify a data installation directory with `--download-dir`L

     singularity run --cleanenv neuroscout-cli-<version>.simg run --download-dir=/data Mv3ev /work/dir/out 

[See here](docker.md#caching-input-datasets) for more details on the cached data structure. 

For further guidance, see our [usage](usage.md) reference guide.

 for more details on the cached data structure. 