## Command-Line Arguments

    neuroscout

    Usage:
        neuroscout run [-mfuvd -i <dir> -w <dir> -s <k> -c <n> -n <nv> -e <es>] <outdir> <bundle_id>...
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
        -s, --smoothing <k>      Smoothing to apply in format: FWHM:level:type.
                                 See fitlins documentation for more information.
                                 [default: 4:Dataset:iso]
        -u, --unlock             Unlock datalad dataset
        -n, --neurovault <nv>    Upload mode (disable, all, or group)
                                 [default: group]
        -e, --estimator <es>     Estimator to use for first-level model
                                 [default: afni]
        -f, --force-neurovault   Force upload, if a NV collection already exists
        -m, --drop-missing       If contrast is missing in a run, skip.
        -d, --no-datalad-drop    Don't drop DataLad sourcedata. True by default
                                 if install-dir i


### Commands (first positional argument)

#### run                      
Runs analysis. If necessary, also runs `install` to download data.

#### install
Download analysis bundle, download data if necessary, and create empty output directory.

#### ls       
List input fMRI data files associated with this analysis, to be downloaded.