# Usage

This assumes that you are using the Docker Container.
Docker commands for _neuroscout-cli_ will always being with:

    docker run -it --rm

Assuming you've already created an analysis on neuroscout.org, and have its analysis id (e.g.: `5xH93`), you can run it in one line:

    docker run -it --rm neuroscout/neuroscout-cli run /out 5xH93

Neuroscout will download the necessary images, analysis bundle, and fit your model. The fitted images will be upload to NeuroVault and linked to your analysis on (neuroscout.org)[htts://neuroscout.org].

## Saving data to disk

In order to save your fitted images to your local filesystem, you must mount volumes from your system to the Docker container.

Usually, you'll at least want to mount a directory where you want to save the results. 

In this example, we mount both of these directories to local volumes:

    docker run -it --rm -v /home/user/out:/out neuroscout/neuroscout-cli run /out 5xH93


In this command, the path preceding `:/out` specifies the local directory where the outputs will be stored. For example, a local folder `/home/user/out`.

Neuroscout creates a unique output directory `neuroscout-{analysis_id}`.
Given the `analysis_id`: `5xH93` and `dataset_name`: `Budapest`, this is a representative directory structure:


    /home/user/out/neuroscout-5xH93  
    └───inputs
    │   │
    │   └───Budapest
    │       └───fmriprep
    │   └───bundle
    │       └───events
    │       │   model.json
    │       │   ...
    └───out
    │   └───fitlins
    │       └───sub-01
    │       └───reports
    │       │   task-movie_space-MNI152NLin2009cAsym_contrast-{name}_stat-effect_statmap.nii.gz
            |   ...


Note that by default Neuroscout will save the input preprocessed fMRI images in the output folder, to create a fully reproducible result package.

If you wish to save the input preprocessed datasets elsewhere, simply specify a data installation directory with `-i`, and mount the corresponding local directory.

    docker run -it --rm -v /home/user/out:/out -v /home/user/data:/data neuroscout/neuroscout-cli run /out 5xH93 -i /data

The resulting cached data directory will look sonething like this, if you've run several analyses from different datasets:


    /home/user/scout-data  
    └───Budapest
    │   └───fmriprep
    └───studyforrest
    │   └───fmriprep


The next time you run a model with a previously downloaded dataset, it will not need to re-download the fMRI data. </br>

Note that you need to specify **absolute paths** for both directories.

## Command-Line Arguments

    neuroscout

    Usage:
        neuroscout run [-dfuv -i <dir> -w <dir> -s <k> -c <n> -n <nv> -e <es>] <outdir> <bundle_id>...
        neuroscout install [-ui <dir>] <outdir> <bundle_id>...
        neuroscout upload [-f -n <nv>] <outdir> <bundle_id>...
        neuroscout ls <bundle_id>
        neuroscout -h | --help
        neuroscout --version

    Options:
        -i, --install-dir <dir>  Optional directory to cache input images
        -w, --work-dir <dir>     Optional Fitlins working directory 
        -c, --n-cpus <n>         Maximum number of threads across all processes
                                 [default: 1]
        -s, --smoothing <k>      Smoothing kernel FWHM at group level
                                 [default: 4]
        -u, --unlock             Unlock datalad dataset
        -n, --neurovault <nv>    Upload mode (disable, all, or group)
                                 [default: group]
        -e, --estimator <es>     Estimator to use for first-level model
                                 [default: nistats]
        -f, --force-neurovault   Force upload, if a NV collection already exists
        -d, --drop-missing       Drop missing contrasts
        -v, --verbose	         Verbose mode


### Commands (first positional argument)

#### run                      
Runs analysis. If necessary, also runs `install` to download data.

#### install
Download analysis bundle, download data if necessary, and create empty output directory.

#### ls       
List input fMRI data files associated with this analysis, to be downloaded.
